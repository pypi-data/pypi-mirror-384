from concurrent.futures.thread import ThreadPoolExecutor
from datetime import time
from pathlib import Path
from typing import Optional, Tuple

import typer

from bayes.client import dataset_client
from bayes.client.base import BayesGQLClient
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.usercases import open_usecase


def get_dataset_by_id(id):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return dataset_client.get_dataset_by_id(gql_client, id)


def open_dataset(id):
    dataset = get_dataset_by_id(id)
    frontend_url = dataset.get_link_value("frontend")
    print(f"正在打开数据集 {frontend_url}")
    print("正在跳转到浏览器...")
    open_usecase.open_browser(frontend_url)


def create(party_name, name, message):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return dataset_client.create(gql_client, party_name, name, message)


def get_absolute_path(dataset_path) -> Tuple[str, str]:
    try:
        abs_dataset_path = Path(dataset_path).resolve()
        return str(abs_dataset_path), None
    except Exception as e:
        return None, str(e)


def stat_file(path):
    try:
        file_info = Path(path).stat()
        return file_info, None
    except OSError as e:
        return None, str(e)


def create_empty_version(party_name, dataset_id):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return dataset_client.create_empty_version(gql_client, party_name, dataset_id)
