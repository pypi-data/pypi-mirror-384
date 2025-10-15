import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_importance
from pathlib import Path
from typing import List, Union
from sklearn.base import BaseEstimator, clone

from .base import BaseFeatureSelector
from .FeatureSelectorFactory import FeatureSelectorFactory


class PermutationFeatureSelector(BaseFeatureSelector):

    def __init__(self, estimator: BaseEstimator, scoring="accuracy", n_repeats=10, random_state=42, **kwargs):
        super().__init__()
        self.estimator = clone(estimator)
        self.scoring = scoring
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.importances_ = None

    def fit(self, X: pd.DataFrame, y: pd.Series):
        print("Starting feature selection with Permutation Importance...")
        self.estimator.fit(X, y)
        result = permutation_importance(
            self.estimator, X, y, scoring=self.scoring,
            n_repeats=self.n_repeats, random_state=self.random_state, n_jobs=-1
        )

        self.result_ = result
        self.feature_names_ = X.columns.tolist()
        importance_mean = result.importances_mean
        selected = importance_mean > 0  # keep features that have positive contribution
        self.selected_features_ = X.columns[selected].tolist()
        self.importances_ = importance_mean
        print(f"Selected {len(self.selected_features_)} features by permutation importance.")
        return self


    def plot(self, save_path: Union[str, Path, None] = None):
        if self.importances_ is None:
            raise RuntimeError("Run fit() before plotting importances.")

        # Build DataFrame
        df = pd.DataFrame({
            "Feature": self.feature_names_,
            "Importance": self.result_.importances_mean,
            "Std": self.result_.importances_std
        }).sort_values("Importance", ascending=False)

        # Shorten long feature names for readability -- (to check if this is useful or not)
        #df["Feature"] = df["Feature"].apply(lambda x: x if len(x) < 25 else x[:22] + "...")

        # Plot
        plt.figure(figsize=(12, max(6, 0.4 * len(df))))
        y_pos = range(len(df))

        # Horizontal bars
        plt.barh(y_pos, df["Importance"], xerr=df["Std"],
                 align="center", color="#007bff", ecolor="black", capsize=3)

        # Y-axis labels
        plt.yticks(y_pos, df["Feature"], fontsize=8)
        plt.gca().invert_yaxis()  # largest on top

        # Annotate bars
        for i, (imp, std) in enumerate(zip(df["Importance"], df["Std"])):
            if imp > 0.0:  # show only meaningful importances
                label = f"{imp:.3f}" + (f" ± {std:.3f}" if std > 0.001 else "")
            else:
                label = "0.000"    # For zero or negative importance
            plt.text(imp + max(std, 0.002), i, label, va="center", fontsize=8)

        # Titles and labels
        plt.axvline(x=0, color="black", linestyle="--", lw=1)
        plt.title("Permutation Feature Importances", fontsize=14, pad=20)
        plt.xlabel("Mean Importance (± Std)", fontsize=10)
        plt.ylabel("Features", fontsize=12)

        plt.tight_layout(pad=4)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Permutation importance plot saved to {save_path}")

        plt.show()

# Register this selector with the factory
FeatureSelectorFactory.register_selector("permutation", PermutationFeatureSelector)
