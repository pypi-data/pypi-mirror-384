from abc import abstractmethod, ABC
from pandas import DataFrame

class EDA(ABC):

    def load_data(self, df: DataFrame):
        self.df = df.copy()

    @abstractmethod
    def standardize_categories(self) -> DataFrame:
        pass

