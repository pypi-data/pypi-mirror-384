from json import JSONDecodeError, dump, load
from pathlib import Path

from rich import print

from minid.exceptions import Misconfiguration


class Config:
    def __init__(self):
        self.config_path = Path.home() / ".minid" / "config.json"
        self._config = None

    def _ensure_loaded(self):
        if self._config is None:
            self._config = self._load_config()

    def _load_config(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return load(f)
            except (JSONDecodeError, KeyError):
                return {}
        else:
            return self._create_initial_config()

    def _create_initial_config(self) -> dict:
        default_path = "~/.minid/db"
        response = input(f"Database location [{default_path}]: ").strip()

        if response:
            db_path = str(Path(response).expanduser())
        else:
            db_path = str(Path(default_path).expanduser())

        config = {"db_path": db_path}

        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, "w") as f:
            dump(config, f, indent=2)

        print(f"[green]Config saved to {self.config_path}[/green]")
        return config

    @property
    def db_path(self) -> Path:
        self._ensure_loaded()
        if self._config is None:
            raise Misconfiguration()
        path_str = self._config.get("db_path", "~/.minid/db")
        return Path(path_str).expanduser()


config = Config()
