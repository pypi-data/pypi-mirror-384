from typing import List, Optional
from pydantic import BaseModel, Field
import yaml
from pathlib import Path
import typer

APP_NAME = "openbayes"
FILE_NAME = "config.yaml"
TypeHyperTuning = "HYPER_TUNING"
DefaultJobModeWorkSpace = "WORKSPACE"
DefaultBatchJobModeWorkSpace = "BATCH_WORKSPACE"
DefaultJobModeTask = "TASK"
DefaultBatchJobModeTask = "BATCH_TASK"


class BayesEnvConfig(BaseModel):
    name: str
    isDefault: bool = False
    username: Optional[str] = None
    token: Optional[str] = None
    endpoint: str
    graphQL: str
    orgName: Optional[str] = None

    def __init__(self, **data):
        if "name" in data:
            data["name"] = data["name"].lower()
        if "endpoint" in data:
            data["graphQL"] = data["endpoint"] + "/gateway"
        super().__init__(**data)

    def __setattr__(self, name, value):
        if name == "name" and isinstance(value, str):
            value = value.lower()
        super().__setattr__(name, value)


class BayesSettings(BaseModel):
    environments: List[BayesEnvConfig] = Field(default_factory=list)
    config_path: Optional[Path] = None

    def __init__(self, config_path: Optional[Path] = None, **kwargs):
        super().__init__(**kwargs)

        if config_path is None:
            app_dir = typer.get_app_dir(APP_NAME, force_posix=True)
            app_dir_path = Path(app_dir)
            app_dir_path.mkdir(parents=True, exist_ok=True)
            self.config_path = app_dir_path / FILE_NAME
        else:
            self.config_path = config_path

        self.load_from_yaml()

    def load_from_yaml(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f) or []
            self.environments = [BayesEnvConfig(**env) for env in config_data]

        # Check if there are no environments or if none of the environments is set as default
        if not self.environments or not any(env.isDefault for env in self.environments):
            self.add_new_env("default", "https://openbayes.com")

    def add_new_env(self, name: str, endpoint: str) -> BayesEnvConfig:
        """
        Add a new environment configuration or update an existing one, and set it as the default.

        Args:
            name (str): The name of the new or existing environment.
            endpoint (str): The endpoint URL for the environment.

        Returns:
            BayesEnvConfig: The newly created or updated environment configuration.
        """
        name = name.lower()
        existing_config = self.get_env(name)

        if existing_config:
            existing_config.endpoint = endpoint
            existing_config.graphQL = endpoint + "/gateway"
            new_config = existing_config
        else:
            new_config = BayesEnvConfig(name=name, endpoint=endpoint)
            self.environments.append(new_config)

        self.switch_default_env(name)
        return new_config

    @property
    def default_env(self) -> Optional[BayesEnvConfig]:
        return next((env for env in self.environments if env.isDefault), None)

    def get_env(self, name: str) -> Optional[BayesEnvConfig]:
        return next((env for env in self.environments if env.name == name), None)

    def switch_default_env(self, name: str) -> bool:
        """
        Switch the default environment to the one with the given name.
        Returns True if successful, False if the environment was not found.
        """
        new_default = self.get_env(name.lower())
        if new_default is None:
            return False

        for env in self.environments:
            env.isDefault = env.name == new_default.name

        self.save_to_yaml()

        return True

    def save_to_yaml(self):
        config_data = [env.model_dump() for env in self.environments]
        with open(self.config_path, "w") as f:
            yaml.dump(config_data, f)

    def login(self, username, token):
        default_env = self.default_env
        if default_env:
            # print(f"正在更新登录信息: username={username}, token={token[:10]}...")
            default_env.username = username
            default_env.token = token
            self.save_to_yaml()
            # print(f"登录信息已保存到配置文件: {self.config_path}")
            
            # 重新加载配置，确保获取最新的配置
            self.load_from_yaml()
            default_env = self.default_env
            # print(f"登录后重新加载配置: username={default_env.username}, token={default_env.token[:10]}...")
        else:
            raise ValueError("No default environment found")

    def logout(self):
        default_env = self.default_env
        if not default_env:
            print("No default environment found")
            return False
        else:
            default_env.token = None
            default_env.orgName = None
            self.save_to_yaml()
            return True

    def switch_org(self, orgName):
        default_env = self.default_env
        if not default_env:
            print("No default environment found")
            return False
        else:
            default_env.orgName = orgName
            self.save_to_yaml()
            return True

    def switch_user(self, username):
        default_env = self.default_env
        if not default_env:
            print("No default environment found")
            return False
        else:
            default_env.username = username
            default_env.orgName = None
            self.save_to_yaml()
            return True
