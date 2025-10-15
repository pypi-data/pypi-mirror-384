# base.py
from abc import ABC, abstractmethod
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.metrics import roc_auc_score, make_scorer
from typing import Union
import seaborn as sns
import pandas as pd

from evolution.utility import save_artifact


class BaseTrainer(ABC):

    def __init__(self, config):
        self.config = config
        self.model_name = self.config['model']['active']
        self.best_model_ = None
        self.best_params_ = None
        self.best_score_ = None
        self.cv_score_ = None

    @abstractmethod
    def get_model(self): ...
    @abstractmethod
    def fit_with_tuner(self, tuner, X_train, y_train, X_valid, y_valid): ...
    @abstractmethod
    def fit_model(self, base_model, X_train, y_train, X_valid, y_valid): ...
    @abstractmethod
    def post_fit(self, model, save_path): ...

    @property
    @abstractmethod
    def importance_plot_func(self): ...

    def get_tuner(self, base_model):
        tuning_cfg = self.config['hyperparameter_tuning']
        param_grid = tuning_cfg[self.model_name]['param_grid']

        if not param_grid:
            raise ValueError(f"No param_grid found for {self.model_name} in config.")

        search_method = tuning_cfg['search_method']
        print("search_method: ", search_method)

        if search_method == "grid":
            return GridSearchCV(
                estimator=base_model,
                param_grid=param_grid,
                scoring=tuning_cfg['scoring'],
                cv=tuning_cfg['cv_folds'],
                n_jobs=-1,
                verbose=1
            )
        elif search_method == "random":
            return RandomizedSearchCV(
                estimator=base_model,
                param_distributions=param_grid,
                scoring=tuning_cfg['scoring'],
                cv=tuning_cfg['cv_folds'],
                n_iter=tuning_cfg.get('n_iter', 25),
                n_jobs=-1,
                verbose=1,
                random_state=self.config.get('random_state', 42)
            )
        else:
            raise NotImplementedError(f"Search method '{search_method}' is not implemented.")


    def train(self, X_train, y_train, X_valid=None, y_valid=None, save_path: Union[str, Path, None] = None):
        base_model = self.get_model()

        if self.config['hyperparameter_tuning']['active']:
            print(f"--- Starting Hyperparameter Tuning for {self.model_name} ---")
            tuner = self.get_tuner(base_model)

            self.fit_with_tuner(tuner, X_train, y_train, X_valid, y_valid)
            self.best_model_ = tuner.best_estimator_
            self.best_params_ = tuner.best_params_
            self.best_score_ = tuner.best_score_
            self.cv_score_ = self.best_score_

            print(f"Best Score ({self.config['hyperparameter_tuning']['scoring']}): {self.cv_score_:.4f}")
            print(f"Best Parameters: {self.best_params_}")
        else:
            print(f"--- Training {self.model_name} with default parameters ---")
            hyper_scoring = self.config['hyperparameter_tuning']['scoring']

            # Cross Validation
            cv = StratifiedKFold(n_splits=self.config['hyperparameter_tuning']['cv_folds'],
                                 shuffle=True, random_state=self.config.get("random_state", 42))

            print(f"--- Running 5-Fold Cross-Validation (for diagnostics) ---")
            roc_auc = make_scorer(roc_auc_score, response_method="predict_proba")
            cv_results = cross_validate(
                base_model, X_train, y_train,
                cv=cv,
                #scoring=hyper_scoring,
                scoring={'roc_auc': roc_auc},
                return_train_score=True,
                n_jobs=-1
            )

            train_score = np.mean(cv_results['train_' + hyper_scoring])
            val_score = np.mean(cv_results['test_' + hyper_scoring])
            print(f"Mean Train {hyper_scoring}: {train_score:.4f}")
            print(f"Mean Valid {hyper_scoring}: {val_score:.4f}")
            print(f"Generalization Gap (Train-Val): {train_score - val_score:.4f}")

            # Fit final model on all of X_train
            base_model = self.fit_model(base_model, X_train, y_train, X_valid, y_valid)
            self.best_model_ = base_model

        self.post_fit(self.best_model_, save_path)
        return self.best_model_

    def evaluate(self, X_test, y_test):
        if self.best_model_ is None:
            raise RuntimeError("Train the model first.")

        y_pred = self.best_model_.predict(X_test)
        y_proba = self.best_model_.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }
        print("=" * 40)
        print("      Model Training Report (Train)      ")
        print("=" * 40)
        print(f"Model Class: {self.best_model_.__class__.__name__}\n")
        print("--- Key Metrics ---")
        for key, value in metrics.items():
            if key != 'confusion_matrix':
                print(f"{key.replace('_', ' ').title():<12}: {value:.4f}" if isinstance(value,
                                                                                        float) else f"{key.replace('_', ' ').title():<12}: {value}")

        print("--- Confusion Matrix ---")
        print(np.array(metrics['confusion_matrix']))
        print("=" * 40)

        return metrics


    def save_model(self, file_name=None):
        if self.best_model_ is None:
            raise RuntimeError("No model to save.")
        model_dir = Path(self.config['model_dir'])
        file_name = file_name or f"{type(self.best_model_).__name__}.joblib"
        save_artifact(self.best_model_, model_dir / file_name)

    def plot_importance2(self, save_path: Union[str, Path, None] = None, top_n: int = 100):
        """Generic feature importance plot with standard production-level styling."""

        if self.best_model_ is None:
            raise RuntimeError("Train the model first before plotting importance.")

        plot_func = self.importance_plot_func
        if plot_func is None:
            raise NotImplementedError(f"{type(self).__name__} must define importance_plot_func.")

        fig, ax = plt.subplots(figsize=(10, 8))

        # --- Call library-specific plot function ---
        plot_func(self.best_model_, ax=ax, max_num_features=top_n)

        # --- Standardized styling ---
        model_type = type(self.best_model_).__name__
        plt.title(f"{model_type} Feature Importance", fontsize=14)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", linestyle="--", alpha=0.6)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Feature Importance plot saved to: {save_path}")

        plt.show()

    def plot_importance(self, save_path: Union[str, Path, None] = None, top_n: int = 100):
        """Generic feature importance plot with enhanced styling."""

        if self.best_model_ is None:
            raise RuntimeError("Train the model first before plotting importance.")

        plot_func = self.importance_plot_func
        if plot_func is None:
            raise NotImplementedError(f"{type(self).__name__} must define importance_plot_func.")

        # --- Extract raw importance values (instead of library's plot) ---
        if hasattr(self.best_model_, "feature_importances_"):
            importances = self.best_model_.feature_importances_
            feature_names = getattr(self.best_model_, "feature_names_in_", [f"f{i}" for i in range(len(importances))])
            fi_df = pd.DataFrame({"Feature": feature_names, "Importance": importances})
        else:
            raise ValueError("Model does not expose feature_importances_")

        # Sort & keep top_n
        fi_df = fi_df.sort_values(by="Importance", ascending=False).head(top_n)

        # --- Plotting ---
        plt.figure(figsize=(12, max(6, 0.4 * len(fi_df))))
        ax = sns.barplot(data=fi_df, y="Feature", x="Importance", palette="Blues_d")
        ax = sns.barplot(data=fi_df, y="Feature", x="Importance", hue="Feature", dodge=False, palette="Blues_d", legend=False)

        # Add value annotations
        for i, v in enumerate(fi_df["Importance"]):
            plt.text(v + max(fi_df["Importance"]) * 0.01, i, f"{v:.1f}", va="center", fontsize=7)

        model_type = type(self.best_model_).__name__
        #plt.axvline(x=0, color="black", linestyle="--", lw=1)
        plt.title(f"{model_type} Feature Importance", fontsize=14, weight="bold", pad=20)
        plt.xlabel("Importance Score", fontsize=10)
        plt.ylabel("Features", fontsize=12)
        ax.tick_params(axis="y", labelsize=7)
        plt.grid(axis="x", linestyle="--", alpha=0.5)
        sns.despine(left=True, bottom=True)

        plt.tight_layout(pad=4)
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Feature Importance plot saved to: {save_path}")
        plt.show()

    def plot_learning_curve(self, save_path: Union[str, Path, None] = None):
        model = self.best_model_
        model_type = type(model).__name__
        print(f"\n--- Generating Learning Curve for {model_type} ---")

        results = None
        try:
            if model_type == 'XGBClassifier':
                results = model.evals_result()
                best_iteration = None #model.best_iteration
            elif model_type == 'LGBMClassifier':
                results = model.evals_result_
                best_iteration = model.best_iteration_
            else:
                print(f"Learning curve plot not supported for model type: {model_type}")
                return
        except (AttributeError, KeyError):
            print("Could not retrieve evaluation results. Learning curve not plotted.")
            print("Hint: Ensure 'eval_set' is provided during the .fit() call and history is recorded.")
            return

        if not results or not isinstance(results, dict) or len(results) == 0:
            print("No evaluation sets found in model history. Cannot plot learning curve.")
            return

        # --- Plotting Logic (Handles 1 or 2 eval sets) ---
        eval_keys = list(results.keys())
        num_eval_sets = len(eval_keys)
        metric_name = list(results[eval_keys[0]].keys())[0]  # Infer metric name from first set

        plt.figure(figsize=(10, 7))

        if num_eval_sets >= 2:
            # Ideal case: plot both training and validation curves
            train_key, val_key = eval_keys[0], eval_keys[1]
            train_scores = results[train_key][metric_name]
            val_scores = results[val_key][metric_name]

            plt.plot(train_scores, label=f'Training {metric_name.upper()}')
            plt.plot(val_scores, label=f'Validation {metric_name.upper()}')
            print(f"Plotting Train ({train_key}) and Validation ({val_key}) curves.")

        elif num_eval_sets == 1:
            key = eval_keys[0]
            scores = results[key][metric_name]

            print(f"Warning: Only one evaluation set found ('{key}'). Plotting a single curve.")
            plt.plot(scores, label=f'Evaluation ({key}) {metric_name.upper()}')

        # Add common plot elements
        if best_iteration:
            plt.axvline(best_iteration, color='r', linestyle='--', label=f'Best Iteration ({best_iteration})')

        plt.title(f'{model_type} Learning Curve')
        plt.xlabel('Boosting Round (Number of Trees)')
        plt.ylabel(f'Score ({metric_name.upper()})')
        plt.legend()
        plt.grid(True)
        if save_path:
            plt.savefig(save_path, dpi=300)
            print(f"Learning curve plot saved to: {save_path}")
        plt.show()
