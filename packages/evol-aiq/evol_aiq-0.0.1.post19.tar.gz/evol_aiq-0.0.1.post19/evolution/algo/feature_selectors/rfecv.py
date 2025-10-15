import numpy as np
import pandas as pd
from sklearn.feature_selection import RFECV
from sklearn.model_selection import StratifiedKFold
from sklearn.base import BaseEstimator, clone
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Union

from .base import BaseFeatureSelector
from .FeatureSelectorFactory import FeatureSelectorFactory


class RFECVFeatureSelector(BaseFeatureSelector):

    def __init__(self, estimator: BaseEstimator, step: int = 1, cv_folds: int = 5, scoring: str = "accuracy", min_features: int = 1, **kwargs):
        super().__init__()
        self.estimator = clone(estimator)
        self.step = step
        self.cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        self.scoring = scoring
        self.min_features = min_features
        self.rfecv_ = None

    def fit(self, X: pd.DataFrame, y: pd.Series):
        print("Starting feature selection with RFECV...")
        self.rfecv_ = RFECV(
            estimator=self.estimator,
            step=self.step,
            cv=self.cv,
            scoring=self.scoring,
            min_features_to_select=self.min_features,
            n_jobs=-1,
        )
        self.rfecv_.fit(X, y)
        self.selected_features_ = X.columns[self.rfecv_.support_].tolist()
        print(f"Optimal features: {len(self.selected_features_)}")
        return self

    def plot(self, save_path: Union[str, Path, None] = None):
        if not self.rfecv_:
            raise RuntimeError("You must run fit() before plotting the scores.")

        # The number of features explored during RFECV
        n_features_tested = range(self.min_features,
                                  len(self.rfecv_.cv_results_['mean_test_score']) * self.step + self.min_features,
                                  self.step)

        plt.figure(figsize=(12, 7))
        sns.set_theme(style="whitegrid")

        # Plot the mean CV scores
        plt.plot(n_features_tested, self.rfecv_.cv_results_['mean_test_score'], marker='o', linestyle='-')

        # Highlight the optimal number of features
        optimal_score = np.max(self.rfecv_.cv_results_['mean_test_score'])
        plt.axvline(x=self.rfecv_.n_features_, color='r', linestyle='--',
                    label=f'Optimal features: {self.rfecv_.n_features_}\n(Score: {optimal_score:.4f})')

        plt.title('RFECV Performance vs. Number of Features')
        plt.xlabel('Number of Features Selected')
        plt.ylabel(f'Cross-Validation Score ({self.scoring})')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300)
            print(f"Plot saved to: {save_path}")

        plt.show()

# Register this selector with the factory
FeatureSelectorFactory.register_selector("rfecv", RFECVFeatureSelector)