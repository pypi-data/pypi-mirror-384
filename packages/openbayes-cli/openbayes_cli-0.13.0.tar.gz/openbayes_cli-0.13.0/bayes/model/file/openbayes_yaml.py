import os
from importlib import resources
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, root_validator, model_validator, validator, field_validator
import yaml
from pathlib import Path
import typer

from bayes.model.file.data_bindings import DataBindings, OpenBayesDataBinding

FILE_NAME = "openbayes.yaml"
DEFAULT_JOB_RESOURCE = "rtx-4090"
DEFAULT_JOB_RUNTIME = "pytorch-2.6-2204"
DEFAULT_PARALLEL_COUNT = 1


class ParameterSpec(BaseModel):
    name: str
    type: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    scale_type: Optional[str] = None
    categorical_values: Optional[List[str]] = None
    discrete_values: Optional[List[float]] = None


class HyperTuning(BaseModel):
    max_job_count: int
    parallel_count: int
    hyperparameter_metric: str
    goal: str
    algorithm: str
    parameter_specs: List[ParameterSpec]
    side_metrics: List[str]

    def get_parameter_specs(self) -> List[ParameterSpec]:
        results = []

        for spec in self.parameter_specs:
            result = ParameterSpec(
                name=spec.name,
                type=spec.type
            )

            if spec.type in {"DOUBLE", "INTEGER"}:
                result.min_value = spec.min_value
                result.max_value = spec.max_value
                result.scale_type = spec.scale_type
            elif spec.type == "CATEGORICAL":
                result.categorical_values = spec.categorical_values
            elif spec.type == "DISCRETE":
                result.discrete_values = spec.discrete_values

            results.append(result)

        return results


class OpenBayesYaml(BaseModel):
    data_bindings: Optional[Union[DataBindings, List[OpenBayesDataBinding]]] = None
    resource: str
    env: str
    command: str
    node: int
    parameters: Dict[str, Any]
    hyper_tuning: HyperTuning

    @model_validator(mode="before")
    @classmethod
    def handle_bindings(cls, values):
        if 'bindings' in values and 'data_bindings' not in values:
            values['data_bindings'] = {'bindings': values.pop('bindings')}
        return values

    def get_runtime(self):
        return self.env

    def get_dataset_bindings(self) -> List[str]:
        result_list = []

        def join_data_path(data, path, binding_type):
            if binding_type:
                return f"{data}:{path}:{binding_type}"
            else:
                return f"{data}:{path}"

        def contains(data, path, binding_list):
            for binding in binding_list:
                if binding.endswith(path) or binding.startswith(data):
                    return True
            return False

        if isinstance(self.data_bindings, DataBindings):
            for binding in self.data_bindings.get_bindings():
                if ':' in binding:
                    result_list.append(binding)

            for dataset in self.data_bindings.get_data_bindings():
                data = dataset.name if dataset.name else dataset.data
                path = dataset.path

                if not contains(data, path, result_list):
                    result_list.append(join_data_path(data, path, dataset.type))
        elif isinstance(self.data_bindings, list):
            for dataset in self.data_bindings:
                data = dataset.name if dataset.name else dataset.data
                path = dataset.path

                if not contains(data, path, result_list):
                    result_list.append(join_data_path(data, path, dataset.type))

        return result_list


class OpenBayesYamlSettings(BaseModel):
    configuration: Optional[OpenBayesYaml] = None
    config_path: Optional[Path] = None

    def __init__(self, config_path: Optional[Path] = None, **kwargs):
        super().__init__(**kwargs)

        if config_path is None:
            self.config_path = Path(FILE_NAME)
        else:
            self.config_path = config_path

        self.load_or_create_default_yaml()

    def load_or_create_default_yaml(self):
        if self.config_path.exists():
            self.load_from_yaml()
        else:
            self.create_default(self.config_path.parent)

    def load_from_yaml(self):
        with open(self.config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}
        self.configuration = OpenBayesYaml(**config_data)

    def save_to_yaml(self):
        with open(self.config_path, "w") as f:
            yaml.dump(self.configuration.model_dump(), f)

    @staticmethod
    def read_template():
        # 'bayes.templates' 是资源所在的包路径
        with resources.open_text('bayes.templates', 'openbayes_zh-Hans.yaml') as file:
            return file.read()

    @staticmethod
    def write_template(file_path, content):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def create_default(self, directory):
        template_content = self.read_template()

        placeholders = {
            'resource': DEFAULT_JOB_RESOURCE,
            'env': DEFAULT_JOB_RUNTIME,
            'parallel_count': DEFAULT_PARALLEL_COUNT
        }

        # 将配置转换为字符串,替换占位符
        config_str = yaml.dump(template_content)
        for key, value in placeholders.items():
            config_str = config_str.replace(f'{{{key}}}', str(value))
        # 解析替换后的 YAML 字符串
        content = yaml.safe_load(config_str)

        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
        file_path = directory / FILE_NAME

        # 写入生成的内容到指定文件
        self.write_template(file_path, content)

        # 读取生成的文件内容并加载
        with open(file_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file) or {}
        self.configuration = OpenBayesYaml(**config_data)
