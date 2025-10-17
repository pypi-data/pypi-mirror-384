import yaml
import os
from pathlib import Path
from typing import List


def get_wine_feature_whitelist(
    version: str = "v1",
) -> List[str]:
    """
    Loads the wine feature whitelist from the configuration file.

    Returns:
        List[str]: Ordered list of wine features that should be tracked
    """
    # Find the config file path
    config_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "config"
    config_path = config_dir / "wine_config.yaml"

    # Load the configuration
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Extract the feature whitelist from the latest version (v1)
    feature_whitelist = config[version]["feature_whitelist"]

    return feature_whitelist
