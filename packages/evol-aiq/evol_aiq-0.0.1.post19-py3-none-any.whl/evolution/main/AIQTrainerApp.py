from pathlib import Path

from pandas import DataFrame

from evolution import utility
from evolution.algo.evaluators.EvaluatorFactory import EvaluatorFactory
from evolution.plugin.inputs.DataExplorer import DataExplorer
from evolution.plugin.inputs.DataCleaner import DataCleaner
from evolution.plugin.inputs.DataTransformer import DataTransformer
from evolution.plugin.inputs.EDA import EDA
from evolution.plugin.inputs.file.FileInputDataReader import FileInputDataReader
from evolution.plugin.inputs.InputDataReader import InputDataReader

from evolution.algo.feature_selectors.FeatureSelectorFactory import FeatureSelectorFactory
from evolution.algo.feature_selectors.permutation import PermutationFeatureSelector
from evolution.algo.feature_selectors.rfecv import RFECVFeatureSelector
from evolution.algo.model_registry import ModelRegistry
from evolution.algo.trainers.TrainerFactory import TrainerFactory
from evolution.utility import load_class
from evolution.algo.trainers.lightgbm import LightGBMTrainer
from evolution.algo.trainers.xgboost import XGBoostTrainer

# force-load trainers so they register


class AIQTrainerApp:
    input_data_reader: InputDataReader = None
    data_cleaner: DataCleaner = None
    data_explorer: DataExplorer = None
    eda: EDA = None
    config: dict = None
    data_transformer: DataTransformer = None

    def __init__(self, config: dict):

        # 1. Load Configuration
        self.config = config
        input_type = self.config["input_data_type"]
        if input_type == 'file':
            self.input_data_reader = load_class('evolution.plugin.inputs.file.FileInputDataReader', 'FileInputDataReader', FileInputDataReader);
        else:
            self.input_data_reader = load_class('evolution.plugin.inputs.file.FileInputDataReader', 'FileInputDataReader', FileInputDataReader);
        self.input_data_reader.load_configs(config)
        self.data_transformer = DataTransformer()

        self.load_plugins()
        print("plugins loaded")

    def load_plugins(self):
        self.data_cleaner = load_class(self.config['plugins']["cleaner_package"], self.config['plugins']["cleaner_class"], DataCleaner)
        self.data_explorer = load_class(self.config['plugins']["explorer_package"], self.config['plugins']["explorer_class"], DataExplorer)
        self.eda = load_class(self.config['plugins']["eda_package"], self.config['plugins']["eda_class"], EDA)


    def explore_data(self, dataframe: DataFrame) -> DataFrame:
        return self.data_explorer.explore_data(dataframe)



    def validate_data(self, dataframe: DataFrame) -> DataFrame:
        print("validating data - final dataframe")
        print(dataframe)
        return dataframe

    def run(self):

        # 2. Data Ingestion
        self.input_data_reader.read_data()
        data_frame = self.input_data_reader.get_data()

        # 3. Data Preprocessing
        self.data_cleaner._load_data(data_frame)
        cleaned_df = self.data_cleaner.process(
            cols_to_drop=self.config['columns_to_drop'],
            required_cols=self.config['required_columns']
        )

        # 4. EDA
        print("\n" + "=" * 20 + " EDA " + "=" * 20)
        self.eda.load_data(cleaned_df)
        cleaned_eda_df = self.eda.standardize_categories()

        # 5. Data Transformation
        print("\n" + "=" * 20 + " Data Transformation " + "=" * 20)
        self.data_transformer.prepare(df=cleaned_eda_df, target_column=self.config['target_column'])
        X_train, X_test, y_train, y_test = self.data_transformer.prepare_datasets(
            test_size=self.config['data_split']['test_size'],
            random_state=self.config['random_state']
        )
        print("\nraw encoded features: ", self.data_transformer.final_feature_names_)
        # save transformer state
        self.data_transformer.save_state("artifacts/features/transformer.joblib")

        # 6. Feature Transformation
        print("\n" + "=" * 20 + " Feature Transformation " + "=" * 20)
        trainer = TrainerFactory.create(self.config)
        fs_config = self.config.get('feature_selection', {})
        if fs_config.get('active', False):
            print("Explicit Feature selection is ACTIVE.")
            selector = FeatureSelectorFactory.create(self.config, trainer.get_model())
            selector.fit(X_train, y_train)
            selector.plot(save_path=Path(self.config['paths']['evaluation_plot']) / "feature_selection_plot.png")

            X_train_selected = selector.transform(X_train)
            X_test_selected = selector.transform(X_test)

            # OPTIONAL
            selector.save_state(self.config['paths']['features_list'])
        else:
            print("Explicit Feature selection is INACTIVE. Using all features.")
            X_train_selected = X_train
            X_test_selected = X_test

        # 7. model training & tuning
        utility.save_data(X_train_selected, self.config['paths']['processed_train_data'])
        utility.save_data(X_test_selected, self.config['paths']['processed_test_data'])
        print("\n" + "=" * 20 + " model trainers & tuning " + "=" * 20)

        final_model = trainer.train(X_train_selected, y_train, X_valid=X_test_selected, y_valid=y_test, save_path=Path(self.config['paths']['evaluation_plot']) / "feature_importance_plot.png")
        print(f"\nFinal model object: {final_model}")
        print("\nModel trained with features:", trainer.best_model_.feature_names_in_)
        trainer.plot_learning_curve(save_path=Path(self.config['paths']['evaluation_plot']) / "learning_curve_plot.png")
        trainer.plot_importance(save_path=Path(self.config['paths']['evaluation_plot']) / "feature_importance_plot.png")

        # 8. Evaluation
        print("\n" + "=" * 20 + " model Evaluation " + "=" * 20)
        evaluator = EvaluatorFactory.create(final_model, self.config["learning_task"]["type"])
        evaluator.run(
            X_test_selected,
            y_test,
            results_path=self.config['paths']['evaluation_report'],
            plot_path=Path(self.config['paths']['evaluation_plot']) / "confusion_matrix.png"
        )

        # 9. Model Registration
        print("\n" + "=" * 20 + " model Registration " + "=" * 20)
        registry = ModelRegistry(registry_path=self.config['paths']['model_registry'])
        registry.register_model(
            model=final_model,
            model_name=self.config['model']['active'],
            metrics=evaluator.metrics_,
            params=trainer.best_params_
        )


        print("all done")
        pass


# my_config = {
#     'input_type':'file',
#     'file_path':'C:\\Users\\rmitra.INDIA\\PycharmProjects\\nglm-ai\\support\\input-data.json',
#     'cleaner_package':'qa.plugins.cleaner.QACleaner',
#     'cleaner_class':'QACleaner1',
#     'explorer_package':'qa.plugins.explorer.QADataExplorer',
#     'explorer_class':'QADataExplorer',
#     'output_path':'C:\\Users\\rmitra.INDIA\\PycharmProjects\\nglm-ai\\support\\'
# }
# ai_trainer_app = AITrainerApp(my_config)
# ai_trainer_app.run()

