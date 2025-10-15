from evolution.algo.evaluators.classification import ClassificationEvaluator
from evolution.algo.evaluators.regression import RegressionEvaluator


class EvaluatorFactory:

    _registry = {
        "classification": ClassificationEvaluator,
        "regression": RegressionEvaluator
    }

    @staticmethod
    def create(model, task_type: str):
        task_type = task_type.lower()
        if task_type not in EvaluatorFactory._registry:
            raise ValueError(f"Unsupported task type: {task_type}")
        return EvaluatorFactory._registry[task_type](model)
