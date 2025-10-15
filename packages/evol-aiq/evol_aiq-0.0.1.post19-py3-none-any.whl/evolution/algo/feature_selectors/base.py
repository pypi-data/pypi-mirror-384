from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
import pandas as pd

from evolution.utility import save_artifact, load_artifact


class BaseFeatureSelector(ABC):

    def __init__(self):
        self.selected_features_ = []

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series):
        pass

    @abstractmethod
    def plot(self, save_path: Union[str, Path, None] = None):
        pass

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.selected_features_:
            raise RuntimeError("Run fit() before transform().")
        missing_cols = set(self.selected_features_) - set(X.columns)
        if missing_cols:
            raise ValueError(f"Missing columns in transform(): {missing_cols}")
        return X[self.selected_features_]

    def save_state(self, path: Union[str, Path]):
        state = {"selected_features": self.selected_features_}
        save_artifact(state, path)
        print(f"FeatureSelector state saved to: {path}")

    @classmethod
    def from_saved_state(cls, path: Union[str, Path]):
        state = load_artifact(path)
        if not isinstance(state, dict) or "selected_features" not in state:
            raise ValueError(f"Invalid state file at {path}")
        selector = cls.__new__(cls)  # bypass __init__
        selector.selected_features_ = state["selected_features"]
        return selector

