# FeatureSelectorFactory.py

from typing import Type, Dict
from .base import BaseFeatureSelector


class FeatureSelectorFactory:

    _registry: Dict[str, Type[BaseFeatureSelector]] = {}

    @classmethod
    def register_selector(cls, name: str, selector_cls: Type[BaseFeatureSelector]) -> None:
        if not issubclass(selector_cls, BaseFeatureSelector):
            raise TypeError(f"Selector '{selector_cls.__name__}' must inherit from BaseFeatureSelector.")
        cls._registry[name.lower()] = selector_cls

    @classmethod
    def create(cls, config: dict, estimator) -> BaseFeatureSelector:
        method = config.get("feature_selection", {}).get("method")
        if not method:
            raise ValueError("Config must define 'feature_selection.method'.")

        selector_cls = cls._registry.get(method.lower())
        if selector_cls is None:
            available = ", ".join(cls._registry.keys()) or "none"
            raise ValueError(
                f"Unsupported feature selection method '{method}'. Available selectors: {available}"
            )

        # Here, need to do some fine-tune config reading later
        selection_config = config.get("feature_selection", {})
        return selector_cls(estimator=estimator, **selection_config)