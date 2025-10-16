import os
import tempfile
from typing import Any, Callable, List, Mapping, NamedTuple, Optional, Tuple, Type

from google.protobuf import struct_pb2

from chalk._gen.chalk.models.v1 import model_artifact_pb2 as _model_artifact_pb2
from chalk._gen.chalk.models.v1.model_artifact_pb2 import ModelFile
from chalk.ml.model_file_transfer import FileInfo
from chalk.ml.utils import ModelAttributeExtractor, ModelEncoding, ModelType

ModelSchemaType = List[Tuple[List[int], Any]]


class ModelSerializationConfig(NamedTuple):
    filename: str
    encoding: ModelEncoding
    serialize_fn: Callable[[str, Any], None]
    schema_fn: Optional[Callable[[Any], Tuple[Optional[ModelSchemaType], Optional[ModelSchemaType]]]] = None
    dependency_fn: Optional[Callable[[], Optional[List[str]]]] = None


MODEL_SERIALIZERS = {
    ModelType.PYTORCH: ModelSerializationConfig(
        filename="model.pth",
        encoding=ModelEncoding.PICKLE,
        serialize_fn=lambda model, path: ModelSerializer.with_import(
            "torch",
            lambda torch: torch.jit.save(torch.jit.script(model.eval()), path),
            "Please install PyTorch to save PyTorch models.",
        ),
        schema_fn=lambda model: ModelAttributeExtractor.infer_pytorch_schemas(model),
        dependency_fn=lambda: ModelSerializer.with_import(
            "torch", lambda torch: [f"torch=={torch.__version__}"], "Please install PyTorch to save PyTorch models."
        ),
    ),
    ModelType.SKLEARN: ModelSerializationConfig(
        filename="model.pkl",
        encoding=ModelEncoding.PICKLE,
        serialize_fn=lambda model, path: ModelSerializer.with_import(
            "joblib", lambda joblib: joblib.dump(model, path), "Please install joblib to save sklearn models."
        ),
        schema_fn=lambda model: ModelAttributeExtractor.infer_sklearn_schemas(model),
        dependency_fn=lambda: ModelSerializer.with_import(
            "sklearn",
            lambda sklearn: [f"scikit-learn=={sklearn.__version__}"],
            "Please install sklearn to save sklearn models.",
        ),
    ),
    ModelType.TENSORFLOW: ModelSerializationConfig(
        filename="model.h5", encoding=ModelEncoding.HDF5, serialize_fn=lambda model, path: model.save(path)
    ),
    ModelType.XGBOOST: ModelSerializationConfig(
        filename="model.json",
        encoding=ModelEncoding.JSON,
        serialize_fn=lambda model, path: model.save_model(path),
        schema_fn=lambda model: ModelAttributeExtractor.infer_xgboost_schemas(model),
        dependency_fn=lambda: ModelSerializer.with_import(
            "xgboost",
            lambda xgboost: [f"xgboost=={xgboost.__version__}"],
            "Please install xgboost to save xgboost models.",
        ),
    ),
    ModelType.LIGHTGBM: ModelSerializationConfig(
        filename="model.txt",
        encoding=ModelEncoding.TEXT,
        serialize_fn=lambda model, path: model.save_model(path),
    ),
    ModelType.CATBOOST: ModelSerializationConfig(
        filename="model.cbm",
        encoding=ModelEncoding.CBM,
        serialize_fn=lambda model, path: model.save_model(path),
    ),
    ModelType.ONNX: ModelSerializationConfig(
        filename="model.onnx",
        encoding=ModelEncoding.PROTOBUF,
        serialize_fn=lambda model, path: model.save_model(path),
    ),
}


class ModelSerializer:
    def __init__(self, model: Any, model_type: ModelType):
        self._temp_files: List[str] = []
        self._model = model
        self._model_type = model_type
        super().__init__()

    @classmethod
    def from_model(cls, model: Any, model_type: ModelType) -> "ModelSerializer":
        return cls(model=model, model_type=model_type)

    def __enter__(self) -> "ModelSerializer":
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[object]
    ) -> bool:
        self.cleanup()
        return False

    def serialize(self) -> Tuple[str, ModelEncoding]:
        return self.serialize_model(self._model, self._model_type)

    def serialize_model(self, model: Any, model_type: ModelType) -> tuple[str, ModelEncoding]:
        if model_type not in MODEL_SERIALIZERS:
            raise NotImplementedError(f"Unsupported model type: {model_type}")

        tmp_dir = tempfile.mkdtemp()
        serializer_config = MODEL_SERIALIZERS[model_type]

        file_name = serializer_config.filename

        model_path = os.path.join(tmp_dir, file_name)

        serializer_config.serialize_fn(model, model_path)

        self._temp_files.append(model_path)
        return model_path, serializer_config.encoding

    @staticmethod
    def with_import(module_name: str, func: Callable[[Any], Any], error_msg: str) -> Any:
        try:
            module = __import__(module_name)
            return func(module)
        except ImportError:
            raise ImportError(error_msg)

    def get_dependencies(self) -> Optional[List[str]]:
        return (MODEL_SERIALIZERS[self._model_type].dependency_fn or (lambda: None))()

    def cleanup(self):
        import shutil

        for temp_path in self._temp_files:
            try:
                if os.path.isfile(temp_path):
                    os.remove(temp_path)
                elif os.path.isdir(temp_path):
                    shutil.rmtree(temp_path)
                temp_dir = os.path.dirname(temp_path)
                if temp_dir and os.path.exists(temp_dir) and temp_dir.startswith(tempfile.gettempdir()):
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
        self._temp_files.clear()

    @staticmethod
    def fileinfo_to_protobuf(file_info: FileInfo) -> ModelFile:
        return ModelFile(name=file_info.name, size_kb=file_info.size_kb, file_hash=file_info.file_hash)

    @staticmethod
    def protobuf_to_fileinfo(model_file: ModelFile) -> FileInfo:
        return FileInfo(name=model_file.name, size_kb=model_file.size_kb, file_hash=model_file.file_hash)

    @staticmethod
    def convert_metadata_to_protobuf(metadata: Optional[Mapping[str, Any]]) -> Optional[Mapping[str, struct_pb2.Value]]:
        metadata_converted: Mapping[str, struct_pb2.Value] = {}
        if metadata is not None:
            for k, v in metadata.items():
                converted_v = struct_pb2.Value()
                if isinstance(v, str):
                    converted_v.string_value = v
                elif isinstance(v, (int, float)):
                    converted_v.number_value = v
                elif isinstance(v, bool):
                    converted_v.bool_value = v
                else:
                    raise ValueError(
                        f"Unable to parse metadata field: `{k}:{v}`. "
                        + f"{type(v).__name__} is not currently supported."
                    )
                metadata_converted[k] = converted_v
        return metadata_converted

    @staticmethod
    def infer_input_output_schemas(
        model: Any, model_type: ModelType
    ) -> Tuple[Optional[ModelSchemaType], Optional[ModelSchemaType]]:
        serializer_config = MODEL_SERIALIZERS[model_type]
        if serializer_config.schema_fn:
            return serializer_config.schema_fn(model)
        else:
            return None, None

    @staticmethod
    def build_tabular_schema(column_dtypes: Mapping[str, Any]) -> _model_artifact_pb2.TabularSchema:
        import pyarrow as pa

        from chalk.features._encoding.converter import PrimitiveFeatureConverter

        tabular_schema = _model_artifact_pb2.TabularSchema()

        for col_name, dtype in column_dtypes.items():
            if not isinstance(dtype, pa.DataType):
                if dtype == str:
                    pa_dtype = pa.string()
                elif dtype == int:
                    pa_dtype = pa.int64()
                elif dtype == float:
                    pa_dtype = pa.float64()
                elif dtype == bool:
                    pa_dtype = pa.bool_()
                else:
                    raise ValueError(f"Unsupported dtype {dtype} for column {col_name}")
            else:
                pa_dtype = dtype

            proto_arrow_type = PrimitiveFeatureConverter.convert_pa_dtype_to_proto_dtype(pa_dtype)

            column_spec = _model_artifact_pb2.TabularSpec(name=col_name, dtype=proto_arrow_type)

            tabular_schema.columns.append(column_spec)

        return tabular_schema

    @staticmethod
    def build_tensor_schema(tensor_specs: ModelSchemaType) -> _model_artifact_pb2.TensorSchema:
        import pyarrow as pa

        from chalk.features._encoding.converter import PrimitiveFeatureConverter

        tensor_schema = _model_artifact_pb2.TensorSchema()

        for shape, dtype in tensor_specs:
            if not isinstance(dtype, pa.DataType):
                if dtype == str:
                    pa_dtype = pa.string()
                elif dtype == int:
                    pa_dtype = pa.int64()
                elif dtype == float:
                    pa_dtype = pa.float64()
                elif dtype == bool:
                    pa_dtype = pa.bool_()
                else:
                    raise ValueError(f"Unsupported dtype {dtype} for tensor")
            else:
                pa_dtype = dtype

            proto_arrow_type = PrimitiveFeatureConverter.convert_pa_dtype_to_proto_dtype(pa_dtype)

            tensor_spec = _model_artifact_pb2.TensorSpec(
                dtype=proto_arrow_type, shape=[_model_artifact_pb2.TensorDimension(fixed=dim) for dim in shape]
            )

            tensor_schema.tensors.append(tensor_spec)

        return tensor_schema

    @staticmethod
    def convert_schema(schema: Any) -> Optional[_model_artifact_pb2.ModelSchema]:
        model_schema = _model_artifact_pb2.ModelSchema()
        if schema is not None:
            if isinstance(schema, dict):
                model_schema.tabular.CopyFrom(ModelSerializer.build_tabular_schema(schema))
            elif isinstance(schema, list):
                model_schema.tensor.CopyFrom(ModelSerializer.build_tensor_schema(schema))
            else:
                raise ValueError(f"Invalid schema: {schema}")
        else:
            raise ValueError(f"Invalid empty schema.")

        return model_schema
