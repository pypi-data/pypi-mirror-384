import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

FILE_NAME = ".openbayesgear"


class OpenBayesGear(BaseModel):
    id: str
    name: str
    jid: Optional[str] = ""


class OpenBayesGearSettings(BaseModel):
    configuration: Optional[OpenBayesGear] = None
    config_path: Optional[Path] = None

    def __init__(self, config_path: Optional[Path] = None, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path or Path(FILE_NAME)
        self.load_from_file()

    def load_from_file(self):
        if self.config_path.exists():
            with self.config_path.open("r") as f:
                config_data = yaml.safe_load(f)
            if config_data:
                self.configuration = OpenBayesGear(**config_data)
            else:
                self.configuration = None

    def save_to_file(self):
        with self.config_path.open("w") as f:
            if self.configuration:
                yaml.dump(self.configuration.model_dump(), f, default_flow_style=False)
            else:
                f.write("")

    def create_or_update(self, directory: str, pid: str, project_name: str) -> None:
        directory_path = Path(directory)
        file_path = directory_path / FILE_NAME

        os.makedirs(directory_path, exist_ok=True)

        self.config_path = file_path
        self.configuration = OpenBayesGear(id=pid, name=project_name)

        self.save_to_file()

    def read_from_file(self, path: str) -> OpenBayesGear:
        with open(path, "r") as f:
            config_data = yaml.safe_load(f)
        if config_data:
            return OpenBayesGear(**config_data)
        else:
            raise FileNotFoundError(f"No config data found in {path}")

    def update_jid(self, directory: str, jid: str) -> None:
        path = Path(directory) / FILE_NAME

        gear = self.read_from_file(str(path))

        gear.jid = jid
        self.configuration = gear

        try:
            self.save_to_file()
        except Exception as e:
            raise RuntimeError(f"Error saving to file: {e}")
