from apeex.contracts.config_loader import ConfigLoaderInterface


class YamlLoaderAdapter(ConfigLoaderInterface):
    """
    Adapter for YAML configuration loading.
    MVP placeholder — actual logic will be added later.
    """

    def load(self, path: str) -> dict:
        """Load configuration from YAML file."""
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
