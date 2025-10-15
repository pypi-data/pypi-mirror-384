from abc import abstractmethod, ABC
from typing import List, Optional
from pandas import DataFrame
from typing import Self


class DataCleaner(ABC):


    def _load_data(self, df: DataFrame):
        self.df = df.copy()

    @abstractmethod
    def _validate(self, required_cols: Optional[List[str]] = None) -> Self:
        pass

    @abstractmethod
    def _drop_columns(self, cols_to_drop: Optional[List[str]] = None) -> Self:
        pass

    @abstractmethod
    def _handle_missing_values(self) -> Self:
        pass

    def process(self, cols_to_drop: Optional[List[str]] = None, required_cols: Optional[List[str]] = None) -> DataFrame:
        print("Starting data preprocessing...")
        self._validate(required_cols)
        self._drop_columns(cols_to_drop)
        self._handle_missing_values()
        print("Preprocessing complete.")
        return self.df