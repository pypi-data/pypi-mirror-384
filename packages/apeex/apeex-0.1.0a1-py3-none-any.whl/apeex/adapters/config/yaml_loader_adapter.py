import yaml
from typing import Any, Mapping, Optional
from apeex.contracts.config import ConfigLoaderInterface

class YAMLLoaderAdapter(ConfigLoaderInterface):
    """
    Адаптер для загрузки конфигурации из YAML файлов.
    Ядро не знает о PyYAML.
    """
    def __init__(self, default_path: Optional[str] = None):
        self.default_path = default_path

    def load(self, path: Optional[str] = None) -> Mapping[str, Any]:
        """
        path: путь к YAML файлу. Если не указан, используется default_path.
        """
        final_path = path or self.default_path
        if not final_path:
            raise ValueError("Config path must be provided")

        with open(final_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
