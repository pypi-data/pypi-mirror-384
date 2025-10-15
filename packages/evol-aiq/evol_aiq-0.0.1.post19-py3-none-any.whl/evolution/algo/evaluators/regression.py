from pathlib import Path
from typing import Union
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from evolution.algo.evaluators.base import BaseEvaluator
from evolution.utility import save_dict_as_json


class RegressionEvaluator(BaseEvaluator):

    def __init__(self, model):
        super().__init__(model)
        self.metrics_ = {}

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series):
        y_pred = self.model.predict(X_test)
        self.metrics_ = {
            "rmse": mean_squared_error(y_test, y_pred, squared=False),
            "mae": mean_absolute_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred)
        }
        return self

    def display_report(self):
        print("=" * 40)
        print("      Regression Evaluation Report      ")
        print("=" * 40)
        for key, value in self.metrics_.items():
            print(f"{key:<8}: {value:.4f}")
        print("=" * 40)

    def save_results(self, path: Union[str, Path]):
        save_dict_as_json(self.metrics_, Path(path))

    def run(self, X_test, y_test, results_path=None, plot_path=None):
        self.evaluate(X_test, y_test)
        self.display_report()
        if results_path:
            self.save_results(results_path)
