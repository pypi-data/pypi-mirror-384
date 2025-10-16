from typing import Optional, List

from bayes.client import dataset_list_client
from bayes.client.base import BayesGQLClient
from bayes.model.dataset import Dataset
from bayes.model.dataset_version import DatasetVersion
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.usercases.org_usecase import display_table
from bayes.utils import Utils


def list_datasets(uid, page):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return dataset_list_client.get_datasets(gql_client, uid, page)


def process_datasets(datasets: List[Dataset]):
    if datasets is None:
        datasets = []
    data = [[dataset.status, dataset.id, dataset.name, dataset.latestVersion,
             Utils.byte_size(dataset.size, True),
             Utils.date_from_now(dataset.updatedAt)] for dataset in datasets]
    return data


def list_datasets_display_table(datasets: List[Dataset]):
    headers = ["STATUS", "ID", "NAME", "VERSIONS", "SIZE", "UPDATED_AT"]
    result = process_datasets(datasets)
    display_table(result, headers)


def list_dataset_versions(id):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return dataset_list_client.get_dataset_versions(gql_client, id)


def process_dataset_versions(dataset_versions: List[DatasetVersion]):
    if dataset_versions is None:
        dataset_versions = []
    data = [[dataset_version.version, dataset_version.name, dataset_version.description, dataset_version.status,
             dataset_version.deletedString(), Utils.byte_size(dataset_version.size, True),
             Utils.date_from_now(dataset_version.createdAt)] for dataset_version in dataset_versions]
    return data


def list_dataset_versions_display_table(dataset_versions: List[DatasetVersion]):
    headers = ["VERSION", "NAME", "DESC", "STATUS", "DELETED", "SIZE", "UPDATED_AT"]
    result = process_dataset_versions(dataset_versions)
    display_table(result, headers)
