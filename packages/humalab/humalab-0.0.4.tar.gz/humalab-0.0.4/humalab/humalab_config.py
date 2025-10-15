from pathlib import Path
import yaml
import os

class HumalabConfig:
    def __init__(self):
        self._config = {
            "workspace_path": "",
            "entity": "",
            "base_url": "",
            "api_key": "",
            "timeout": 30.0,
        }
        self._workspace_path = ""
        self._entity = ""
        self._base_url = ""
        self._api_key = ""
        self._timeout = 30.0
        self._load_config()

    def _load_config(self):
        home_path = Path.home()
        config_path = home_path / ".humalab" / "config.yaml"
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.touch()
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)
        self._workspace_path = os.path.expanduser(self._config["workspace_path"]) if self._config and "workspace_path" in self._config else home_path
        self._entity = self._config["entity"] if self._config and "entity" in self._config else ""
        self._base_url = self._config["base_url"] if self._config and "base_url" in self._config else ""
        self._api_key = self._config["api_key"] if self._config and "api_key" in self._config else ""
        self._timeout = self._config["timeout"] if self._config and "timeout" in self._config else 30.0

    def _save(self) -> None:
        yaml.dump(self._config, open(Path.home() / ".humalab" / "config.yaml", "w"))

    @property
    def workspace_path(self) -> str:
        return str(self._workspace_path)
    
    @workspace_path.setter
    def workspace_path(self, path: str) -> None:
        self._workspace_path = path
        self._config["workspace_path"] = path
        self._save()

    @property
    def entity(self) -> str:
        return str(self._entity)

    @entity.setter
    def entity(self, entity: str) -> None:
        self._entity = entity
        self._config["entity"] = entity
        self._save()

    @property
    def base_url(self) -> str:
        return str(self._base_url)

    @base_url.setter
    def base_url(self, base_url: str) -> None:
        self._base_url = base_url
        self._config["base_url"] = base_url
        self._save()

    @property
    def api_key(self) -> str:
        return str(self._api_key)

    @api_key.setter
    def api_key(self, api_key: str) -> None:
        self._api_key = api_key
        self._config["api_key"] = api_key
        self._save()

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: float) -> None:
        self._timeout = timeout
        self._config["timeout"] = timeout
        self._save()