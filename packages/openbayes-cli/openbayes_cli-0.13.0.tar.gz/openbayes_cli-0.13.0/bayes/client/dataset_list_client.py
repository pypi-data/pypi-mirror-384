import json
import sys

from gql.transport.exceptions import TransportQueryError

from bayes.client.base import BayesGQLClient
from bayes.model.dataset import Dataset
from bayes.model.dataset_version import DatasetVersion


def get_datasets(client: BayesGQLClient, party_name, page):
    query = """
        query Datasets($partyId: ID!, $page: Int!) {
          party(id: $partyId) {
            datasets(page: $page) {
              data {
                status
                id
                name
                latestVersion
                size
                updatedAt
              }
            }
          }
        }
    """
    variables = {"partyId": party_name, "page": page}

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

    datasets_data = response.get("party", {}).get("datasets", {}).get("data", [])
    if not datasets_data:
        return None

    return [Dataset(**dataset) for dataset in datasets_data]


def get_dataset_versions(client: BayesGQLClient, id):
    query = """
    query Versions($datasetId: String!) {
      dataset(datasetId: $datasetId) {
        versions {
          version
          name
          description
          status
          deletedAt
          size
          createdAt
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

    dataset_version_list = response.get("dataset", {}).get("versions", [])
    if not dataset_version_list:
        return None

    return [DatasetVersion(**dataset_version) for dataset_version in dataset_version_list]
