# src/data_transformation.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from typing import Tuple, List, Iterable
from typing import Union
from pathlib import Path

from evolution import utility


class DataTransformer:

    def prepare(self, df: pd.DataFrame, target_column: str):
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame.")

        self.df = df.copy()
        self.target_column = target_column

        # Separate features and target
        self.X = self.df.drop(self.target_column, axis=1)
        self.y = self.df[self.target_column]

        # Identify feature types
        self.cat_columns: List[str] = self.X.select_dtypes(include=["object", "category"]).columns.tolist()
        self.num_columns: List[str] = self.X.select_dtypes(include=[np.number]).columns.tolist()

        # OneHotEncoder — categorical encoding
        self.encoder: OneHotEncoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop=None)
        self.final_feature_names_: List[str] | None = None


    def split(self, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        print(f"Splitting data with test_size={test_size}, random_state={random_state}...")

        X_train_raw, X_test_raw, y_train, y_test = train_test_split(
            self.X, self.y,
            test_size=test_size,
            random_state=random_state,
            stratify=self.y if self.y.nunique() > 1 else None
        )
        print(f"Data split into {X_train_raw.shape[0]} training samples and {X_test_raw.shape[0]} testing samples.")
        print(f"Train shape: {X_train_raw.shape}, Test shape: {X_test_raw.shape}")
        return X_train_raw, X_test_raw, y_train, y_test

    def fit_encoder(self, X_train_raw: pd.DataFrame):
        if self.cat_columns:
            self.encoder.fit(X_train_raw[self.cat_columns])

    def transform(self, X_raw: pd.DataFrame) -> pd.DataFrame:
        # Numeric
        X_num = X_raw[self.num_columns] if self.num_columns else pd.DataFrame(index=X_raw.index)

        # Categorical
        if self.cat_columns:
            X_cat = pd.DataFrame(
                self.encoder.transform(X_raw[self.cat_columns]),
                columns=self.encoder.get_feature_names_out(self.cat_columns),
                index=X_raw.index
            )
        else:
            X_cat = pd.DataFrame(index=X_raw.index)

        # Merge
        X_all = pd.concat([X_num, X_cat], axis=1)
        # Normalize col names
        X_all.columns = self._normalize_columns(X_all.columns)
        return X_all


    def prepare_datasets(self, test_size: float = 0.2, random_state: int = 42):
        # split train and test set
        X_train_raw, X_test_raw, y_train, y_test = self.split(test_size, random_state)
        # hot-encode
        self.fit_encoder(X_train_raw)
        # transform
        X_train = self.transform(X_train_raw)
        X_test = self.transform(X_test_raw)
        # Save feature names
        self.final_feature_names_ = X_train.columns.tolist()
        print(f"Final features: {len(self.final_feature_names_)}")
        return X_train, X_test, y_train, y_test

    def save_state(self, path: Union[str, Path]):
        state = {
            "cat_columns": self.cat_columns,
            "num_columns": self.num_columns,
            "final_feature_names": self.final_feature_names_,
            "encoder": self.encoder
        }
        utility.save_artifact(state, path)
        print(f"DataTransformation state saved to: {path}")

    @classmethod
    def load_saved_state(cls, path: Union[str, Path]):
        state = utility.load_artifact(path)
        required_keys = {"cat_columns", "num_columns", "final_feature_names", "encoder"}
        if not isinstance(state, dict) or not required_keys.issubset(state.keys()):
            raise ValueError(f"Invalid state file at {path}")

        obj = cls.__new__(cls)  # bypass __init__
        obj.df = None
        obj.target_column = None
        obj.X = None
        obj.y = None
        obj.cat_columns = state["cat_columns"]
        obj.num_columns = state["num_columns"]
        obj.final_feature_names_ = state["final_feature_names"]
        obj.encoder = state["encoder"]
        return obj


    # NO USE -- TO REMOVE
    def split_data(self, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        print(f"Splitting data with test_size={test_size}, random_state={random_state}...")

        X_train_raw, X_test_raw, y_train, y_test = train_test_split(
            self.X, self.y,
            test_size=test_size,
            random_state=random_state,
            stratify=self.y if self.y.nunique() > 1 else None  # IMPROVEMENT: Stratify only if possible
        )
        print(f"Data split into {X_train_raw.shape[0]} trainers samples and {X_test_raw.shape[0]} testing samples.")

        # --- Fit encoder on train categorical data ---
        if self.cat_columns:
            # Fit the encoder
            self.encoder.fit(X_train_raw[self.cat_columns])

            # Transform categorical columns into DataFrames
            X_train_cat = pd.DataFrame(
                self.encoder.transform(X_train_raw[self.cat_columns]),
                columns=self.encoder.get_feature_names_out(self.cat_columns),
                index=X_train_raw.index
            )
            X_test_cat = pd.DataFrame(
                self.encoder.transform(X_test_raw[self.cat_columns]),
                columns=self.encoder.get_feature_names_out(self.cat_columns),
                index=X_test_raw.index
            )
        else:
            # Handle case with no categorical features
            X_train_cat = pd.DataFrame(index=X_train_raw.index)
            X_test_cat = pd.DataFrame(index=X_test_raw.index)

        # --- Keep numeric columns ---
        X_train_num = X_train_raw[self.num_columns]
        X_test_num = X_test_raw[self.num_columns]

        # --- Combine numerical and encoded categorical columns ---
        X_train = pd.concat([X_train_num, X_train_cat], axis=1)
        X_test = pd.concat([X_test_num, X_test_cat], axis=1)

        # --- Normalize column names ---
        X_train.columns = self._normalize_columns(X_train.columns)
        X_test.columns = self._normalize_columns(X_test.columns)

        # Save final feature names from the trainers set
        self.final_feature_names_ = X_train.columns.tolist()

        print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
        return X_train, X_test, y_train, y_test


    @staticmethod
    def _normalize_columns(columns: Iterable[str]) -> List[str]:
        return (
            pd.Series(columns)
            .str.replace(" ", "_", regex=False)
            .str.replace("&", "_and_", regex=False)
            .str.replace("/", "_", regex=False)
            .str.replace("-", "_", regex=False)
            .str.replace(r"[^a-zA-Z0-9_]", "", regex=True)
            .str.replace("__+", "_", regex=True)
            .tolist()
        )
