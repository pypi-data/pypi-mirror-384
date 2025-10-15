# model_registry.py

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

from evolution.utility import save_artifact, load_artifact


class ModelRegistry:

    def __init__(self, registry_path: Union[str, Path]):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

    def register_model(self, model: Any, model_name: str, metrics: Dict[str, Any], params: Dict[str, Any] = None):

        version = "model-01"
        model_version_path = self.registry_path / model_name / version
        model_version_path.mkdir(parents=True, exist_ok=True)

        # Save the model artifact
        model_path = model_version_path / "model.joblib"
        save_artifact(model, model_path)

        # Create and save the metadata file
        metadata = {
            "model_name": model_name,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "parameters": params or {}
        }
        metadata_path = model_version_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)

        print(f"Successfully registered model '{model_name}' with version '{version}'.")
        #print(f"Metrics: {metrics}")

    def load_model(self, model_name: str, version: str = 'latest') -> Any:
        model_path = self.registry_path / model_name
        if not model_path.exists():
            raise FileNotFoundError(f"No models found for name: {model_name}")

        if version == 'latest':
            # Find the most recent version directory by name
            versions = sorted([d.name for d in model_path.iterdir() if d.is_dir()])
            if not versions:
                raise FileNotFoundError(f"No versions found for model: {model_name}")
            latest_version = versions[-1]
        else:
            latest_version = version

        model_file = model_path / latest_version / "model.joblib"
        print(f"Loading model '{model_name}' version '{latest_version}'...")
        return load_artifact(model_file)

