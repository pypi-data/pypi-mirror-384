# xgboost.py
import xgboost as xgb

from .TrainerFactory import TrainerFactory
from .base import BaseTrainer
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Union

class XGBoostTrainer(BaseTrainer):

    def get_model(self):
        params = self.config['model']['xgboost'].copy()
        params.setdefault("eval_metric", "auc")
        return xgb.XGBClassifier(**params)

    def fit_with_tuner(self, tuner, X_train, y_train, X_valid, y_valid):
        if X_valid is not None and y_valid is not None:
            tuner.fit(
                X_train, y_train,
                eval_set=[(X_train, y_train), (X_valid, y_valid)],
                verbose=False
            )
        else:
            tuner.fit(X_train, y_train)

    def fit_model(self, base_model, X_train, y_train, X_valid, y_valid):
        if X_valid is not None and y_valid is not None:
            base_model.fit(
                X_train, y_train,
                eval_set=[(X_train, y_train), (X_valid, y_valid)],
                verbose=False
            )
        else:
            base_model.fit(X_train, y_train)
        return base_model

    def post_fit(self, model, save_path: Union[str, Path, None] = None):
        pass
        # Plot feature importance
        #try:
        #    fig, ax = plt.subplots(figsize=(10, 8))
        #    xgb.plot_importance(model, ax=ax)
        #    plt.title(f"{type(model).__name__} Feature Importance")
        #    ax.tick_params(axis='y', labelsize=7)
        #    plt.tight_layout()
        #    if save_path:
        #        plt.savefig(save_path, dpi=300)
        #        print(f"Feature Importance plot saved to: {save_path}")
        #    plt.show()
        #except Exception as e:
        #    print(f"Could not plot feature importance: {e}")
        # Plot Learning Curve
        #self.plot_learning_curve(model)

    @property
    def importance_plot_func(self):
        return xgb.plot_importance

# Register with the factory
TrainerFactory.register_trainer("xgboost", XGBoostTrainer)
