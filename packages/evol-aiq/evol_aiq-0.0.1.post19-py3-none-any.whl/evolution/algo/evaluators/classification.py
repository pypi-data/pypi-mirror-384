from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

from evolution.algo.evaluators.base import BaseEvaluator
from evolution.utility import save_dict_as_json


class ClassificationEvaluator(BaseEvaluator):

    def __init__(self, model):
        super().__init__(model)
        self.y_pred_ = None
        self.y_prob_ = None
        self.metrics_ = {}
        self.class_report_ = None
        self.y_test_ = None

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series):
        self.y_pred_ = self.model.predict(X_test)
        self.y_test_ = y_test

        if hasattr(self.model, 'predict_proba'):
            self.y_prob_ = self.model.predict_proba(X_test)[:, 1]

        cm = confusion_matrix(y_test, self.y_pred_)
        self.metrics_ = {
            "accuracy": accuracy_score(y_test, self.y_pred_),
            "precision": precision_score(y_test, self.y_pred_),
            "recall": recall_score(y_test, self.y_pred_),
            "f1_score": f1_score(y_test, self.y_pred_),
            "roc_auc": roc_auc_score(y_test, self.y_prob_) if self.y_prob_ is not None else "N/A",
            "confusion_matrix": cm.tolist()
        }
        self.class_report_ = classification_report(y_test, self.y_pred_, output_dict=True)
        return self

    def display_report(self):
        print("=" * 40)
        print("      Classification Evaluation Report (Test)    ")
        print("=" * 40)
        print(f"Model Class: {self.model.__class__.__name__}\n")

        for key, value in self.metrics_.items():
            if key != "confusion_matrix":
                print(f"{key:<12}: {value:.4f}" if isinstance(value, float) else f"{key:<12}: {value}")

        #print("\n--- Classification Report ---")
        #print(classification_report(self.y_test_, self.y_pred_))

        print("\nConfusion Matrix:\n", np.array(self.metrics_["confusion_matrix"]))
        print("=" * 40)

    def save_results(self, path: Union[str, Path]):
        if not self.metrics_:
            raise RuntimeError("No results to save. Run evaluate() first.")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        results = {
            "metrics": self.metrics_,
            "classification_report": self.class_report_
        }
        save_dict_as_json(results, path)
        print(f"Evaluation results saved to: {path}")

    def plot_confusion_matrix(self, save_path: Union[str, Path, None] = None):
        if 'confusion_matrix' not in self.metrics_:
            raise RuntimeError("You must run evaluate() before plotting.")

        cm = np.array(self.metrics_["confusion_matrix"])
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['Predicted Negative', 'Predicted Positive'],
                    yticklabels=['Actual Negative', 'Actual Positive'])
        plt.title('Confusion Matrix', fontsize=16)
        plt.ylabel('Actual Label')
        plt.xlabel('Predicted Label')

        if save_path:
            path = Path(save_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(path)
            print(f"Confusion matrix plot saved to: {path}")
        plt.show()


    def run(self, X_test, y_test, results_path=None, plot_path=None):
        self.evaluate(X_test, y_test)
        self.display_report()
        if plot_path:
            self.plot_confusion_matrix(plot_path)
        if results_path:
            self.save_results(results_path)
