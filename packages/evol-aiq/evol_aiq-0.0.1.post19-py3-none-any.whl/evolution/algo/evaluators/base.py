from abc import ABC, abstractmethod
from typing import Any, Union
import pandas as pd


class BaseEvaluator(ABC):

    def __init__(self, model: Any):
        if not hasattr(model, 'predict'):
            raise TypeError("Model must have a 'predict' method.")
        self.model = model

    @abstractmethod
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series):
        pass

    @abstractmethod
    def display_report(self):
        pass

    @abstractmethod
    def save_results(self, path: Union[str, None]):
        pass

    @abstractmethod
    def run(self, X_test: pd.DataFrame, y_test: pd.Series,
            results_path: Union[str, None] = None,
            plot_path: Union[str, None] = None):
        pass
