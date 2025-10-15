import pandas as pd
from pandas import DataFrame
from pandas.io.common import file_path_to_url

from evolution.plugin.inputs.InputDataReader import InputDataReader


class FileInputDataReader(InputDataReader):
    input_file: str = None
    raw_file_type: str = None

    def __init__(self):
        super().__init__()


    def load_configs(self, config: dict):
        self.input_file = config['paths']['raw_data']
        self.raw_file_type = config['paths']['raw_file_type']

    def read_data(self):
        if self.input_file is None:
            print("input file is None")
        else:
            if self.raw_file_type == 'csv':
                self.dataframe = pd.read_csv(self.input_file)
            else:
                self.dataframe = pd.read_json(self.input_file, lines=True)
        print("data read done")

    def get_data(self) -> DataFrame:
        return self.dataframe


