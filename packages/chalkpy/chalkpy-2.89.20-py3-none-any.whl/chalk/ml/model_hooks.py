from typing import Any, Callable, Dict, Optional, Tuple

import pyarrow as pa

from chalk.ml.utils import ModelEncoding, ModelType


def load_xgb_classifier(f: str):
    import xgboost  # pyright: ignore[reportMissingImports]

    model = xgboost.XGBClassifier()
    model.load_model(f)
    return model


def load_xgb_regressor(f: str):
    import xgboost  # pyright: ignore[reportMissingImports]

    model = xgboost.XGBRegressor()
    model.load_model(f)
    return model


def load_pytorch_model(f: str):
    import torch  # pyright: ignore[reportMissingImports]

    torch.set_grad_enabled(False)
    model = torch.jit.load(f)
    model.input_to_tensor = lambda X: torch.from_numpy(X.__array__()).float()
    return model


MODEL_HOOKS: Dict[Tuple[ModelType, ModelEncoding, Optional[str]], Callable[[str], Any]] = {
    (ModelType.PYTORCH, ModelEncoding.PICKLE, None): load_pytorch_model,
    (ModelType.SKLEARN, ModelEncoding.PICKLE, None): lambda f: __import__("joblib").load(f),
    (ModelType.TENSORFLOW, ModelEncoding.HDF5, None): lambda f: __import__("tensorflow").keras.models.load_model(f),
    (ModelType.TENSORFLOW, ModelEncoding.SAFETENSOR, None): lambda f: __import__("tensorflow").keras.models.load_model(
        f
    ),
    (ModelType.XGBOOST, ModelEncoding.JSON, None): load_xgb_regressor,
    (ModelType.XGBOOST, ModelEncoding.JSON, "classifier"): load_xgb_classifier,
    (ModelType.XGBOOST, ModelEncoding.JSON, "regressor"): load_xgb_regressor,
    (ModelType.LIGHTGBM, ModelEncoding.TEXT, None): lambda f: __import__("lightgbm").Booster(model_file=f),
    (ModelType.CATBOOST, ModelEncoding.CBM, None): lambda f: __import__("catboost").CatBoost().load_model(f),
    (ModelType.ONNX, ModelEncoding.PROTOBUF, None): lambda f: __import__("onnxruntime").InferenceSession(f),
}


def pytorch_predict(model: Any, X: Any):
    outputs = model(model.input_to_tensor(X))
    result = outputs.detach().numpy().astype("float64")
    result = result.squeeze()
    # Convert 0-dimensional array to scalar, or ensure we have a proper 1D array
    if result.ndim == 0:
        return result.item()
    return result


PREDICT_HOOKS: Dict[Tuple[ModelType, ModelEncoding, Optional[str]], Callable[[Any, pa.Table], Any]] = {
    (ModelType.PYTORCH, ModelEncoding.PICKLE, None): pytorch_predict,
    (ModelType.SKLEARN, ModelEncoding.PICKLE, None): lambda model, X: model.predict(X),
    (ModelType.TENSORFLOW, ModelEncoding.HDF5, None): lambda model, X: model.predict(X),
    (ModelType.TENSORFLOW, ModelEncoding.SAFETENSOR, None): lambda model, X: model.predict(X),
    (ModelType.XGBOOST, ModelEncoding.JSON, None): lambda model, X: model.predict(X),
    (ModelType.LIGHTGBM, ModelEncoding.TEXT, None): lambda model, X: model.predict(X),
    (ModelType.CATBOOST, ModelEncoding.CBM, None): lambda model, X: model.predict(X),
    (ModelType.ONNX, ModelEncoding.PROTOBUF, None): lambda model, X: model.run(None, {"input": X.astype("float32")})[0],
}
