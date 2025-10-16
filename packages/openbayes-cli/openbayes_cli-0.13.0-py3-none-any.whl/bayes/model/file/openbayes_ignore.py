from importlib import resources

from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os
import yaml

IGNORE_FILE_NAME = ".openbayesignore"
# 定义忽略的文件和目录模式
IGNORE_CLEANUPS = [
    "__MACOSX",
    "*.rsrc",
    ".openbayesdata",
    ".openbayesgear",
    ".openbayesignore",
    ".DS_Store",
    "Desktop.ini",
    "desktop.ini",
    "._*",
    "Thumbs.db",
    ".Spotlight-V100",
    ".Trashes",
    ".VolumeIcon.icns",
    "$RECYCLE.BIN",
    "$Recycle.Bin",
    ".tus_storage",
    ".git",
    ".venv",
    "auto_upload_dataset_and_model.py",
    "openbayes_params.json"
]


class OpenBayesIgnore(BaseModel):
    message: Optional[str] = None


class OpenBayesIgnoreSettings(BaseModel):
    configuration: Optional[OpenBayesIgnore] = None
    config_path: Optional[Path] = None

    def __init__(self, config_path: Optional[Path] = None, **kwargs):
        super().__init__(**kwargs)
        try:
            self.config_path: Path = Path(config_path) if isinstance(config_path, str) else config_path or Path(
                IGNORE_FILE_NAME)
            if not self.config_path.exists():
                raise FileNotFoundError(f"{self.config_path} does not exist.")
            if self.config_path.is_dir():
                self.config_path = self.config_path / IGNORE_FILE_NAME
            self.load_or_create_default_yaml()
        except Exception as e:
            # Handle specific exceptions or log them
            print(f"Error initializing settings: {e}")

    def load_or_create_default_yaml(self):
        if self.config_path.exists():
            self.load_from_yaml()
        else:
            self.create_default(self.config_path.parent)

    def load_from_yaml(self):
        with open(self.config_path, "r", encoding='utf-8') as f:
            message = f.read()
        self.configuration = OpenBayesIgnore(message=message)

    def save_to_yaml(self):
        with open(self.config_path, "w", encoding='utf-8') as f:
            f.write(self.configuration.message)

    @staticmethod
    def read_template():
        # 'bayes.templates' 是资源所在的包路径
        with resources.open_text('bayes.templates', 'openbayesignore.yaml') as file:
            return file.read()

    def create_default(self, directory):
        # 读取模板内容
        template_content = self.read_template()

        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
        file_path = directory / IGNORE_FILE_NAME

        # 写入模板内容到文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(template_content)

        # 加载文件内容为配置
        self.configuration = OpenBayesIgnore(message=template_content)
