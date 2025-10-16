from __future__ import annotations

from datetime import datetime
from typing import Any, List

from chalk.ml.model_hooks import MODEL_HOOKS, PREDICT_HOOKS
from chalk.ml.utils import ModelEncoding, ModelType


class ModelVersion:
    def __init__(
        self,
        *,
        name: str,
        version: int | None = None,
        alias: str | None = None,
        as_of_date: datetime | None = None,
        identifier: str | None = None,
        model_type: ModelType | None = None,
        model_encoding: ModelEncoding | None = None,
        model_class: str | None = None,
        filename: str | None = None,
    ):
        """Specifies the model version that should be loaded into the deployment.

        Examples
        --------
        >>> from chalk.ml import ModelVersion
        >>> ModelVersion(
        ...     name="fraud_model",
        ...     version=1,
        ... )
        """
        super().__init__()
        self.name = name
        self.version = version
        self.alias = alias
        self.as_of_date = as_of_date
        self.identifier = identifier
        self.model_type = model_type
        self.model_encoding = model_encoding
        self.model_class = model_class
        self.filename = filename

        self._model = None
        self._predict_fn = None

    def get_model_file(self) -> str | None:
        """Returns the filename of the model."""
        if self.filename is None:
            return None
        return self.filename

    def load_model(self):
        """Loads the model from the specified filename using the appropriate hook."""
        if self.model_type and self.model_encoding:
            load_function = MODEL_HOOKS.get((self.model_type, self.model_encoding, self.model_class))
            if load_function is not None and self.filename is not None:
                self._model = load_function(self.filename)
            else:
                raise ValueError(
                    f"No load function defined for type {self.model_type} and extension {self.model_encoding}"
                )

    def predict(self, X: List[List[float]]):
        """Loads the model from the specified filename using the appropriate hook."""

        if self._predict_fn is None:
            if self.model_type is None or self.model_encoding is None:
                raise ValueError("Model type and encoding must be specified to use predict.")
            self._predict_fn = PREDICT_HOOKS.get((self.model_type, self.model_encoding, self.model_class), None)
            if self._predict_fn is None:
                raise ValueError(
                    f"No predict function defined for type {self.model_type} and extension {self.model_encoding}"
                )
        return self._predict_fn(self.model, X)

    @property
    def model(self) -> Any:
        """Returns the loaded model instance."""
        if self._model is None:
            self.load_model()

        return self._model
