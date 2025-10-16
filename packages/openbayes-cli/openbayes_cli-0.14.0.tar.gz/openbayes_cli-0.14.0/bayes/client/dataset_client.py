import json
import sys

from gql.transport.exceptions import TransportQueryError

from bayes.client.base import BayesGQLClient
from bayes.model.dataset import Dataset
from bayes.model.dataset_version import DatasetVersion


def get_dataset_by_id(client: BayesGQLClient, id):
    query = """
    query Dataset($datasetId: String!) {
      dataset(datasetId: $datasetId) {
        size
        id
        name
        latestVersion
        links {
          name
          value
        }
      }
    }
    """
    variables = {"datasetId": id}

    try:
        response = client.exec(query, variables)
    except TransportQueryError as e:
        if e.errors:
            error_message = e.errors[0].get('message', 'Unknown error')
            extensions = e.errors[0].get('extensions', {})
            details = extensions.get('details', {})

            # 只有当 details 不为空时，我们才添加 details 信息
            if details:
                details_str = json.dumps(details, ensure_ascii=False, indent=2)
                full_error_message = f"{error_message}. Details: {details_str}"
            else:
                full_error_message = error_message
        else:
            full_error_message = str(e)

        print(full_error_message, file=sys.stderr)
        sys.exit(1)

    dataset_data = response.get("dataset", {})
    if not dataset_data:
        return None

    return Dataset(**dataset_data)


def create(client: BayesGQLClient, party_name, name, message):
    query = """
        mutation CreateDataset($userId: String!, $name: String!, $description: String) {
          createDataset(userId: $userId, name: $name, description: $description) {
            id
            name
            links {
              name
              value
            }
          }
        }
    """
    variables = {"userId": party_name, "name": name, "description": message}

    try:
        response = client.exec(query, variables)
    except TransportQueryError as e:
        if e.errors:
            error_message = e.errors[0].get('message', 'Unknown error')
            extensions = e.errors[0].get('extensions', {})
            details = extensions.get('details', {})

            # 只有当 details 不为空时，我们才添加 details 信息
            if details:
                details_str = json.dumps(details, ensure_ascii=False, indent=2)
                full_error_message = f"{error_message}. Details: {details_str}"
            else:
                full_error_message = error_message
        else:
            full_error_message = str(e)

        print(full_error_message, file=sys.stderr)  # 打印错误消息到标准错误流
        sys.exit(1)

    dataset_data = response.get("createDataset", {})
    if not dataset_data:
        return None

    return Dataset(**dataset_data)


def create_empty_version(client: BayesGQLClient, party_name, dataset_id):
    query = """
    mutation CreateEmptyVersion($datasetId: String!) {
        createEmptyVersion(datasetId: $datasetId) {
          id
          version
          name
        }
    }
    """

    variables = {"datasetId": dataset_id}

    try:
        response = client.exec(query, variables)
    except TransportQueryError as e:
        if e.errors:
            error_message = e.errors[0].get('message', 'Unknown error')
            extensions = e.errors[0].get('extensions', {})
            details = extensions.get('details', {})

            # 只有当 details 不为空时，我们才添加 details 信息
            if details:
                details_str = json.dumps(details, ensure_ascii=False, indent=2)
                full_error_message = f"{error_message}. Details: {details_str}"
            else:
                full_error_message = error_message
        else:
            full_error_message = str(e)

        print(full_error_message, file=sys.stderr)
        sys.exit(1)

    dataset_version_data = response.get("createEmptyVersion", {})
    if not dataset_version_data:
        return None

    return DatasetVersion(**dataset_version_data)


