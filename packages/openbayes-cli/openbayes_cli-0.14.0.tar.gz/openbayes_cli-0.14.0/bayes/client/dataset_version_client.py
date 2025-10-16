import json
import sys

from gql.transport.exceptions import TransportQueryError

from bayes.client.base import BayesGQLClient
from bayes.model.dataset_version import PublicDatasetVersions, DatasetVersion
from bayes.model.party import Party, JobData, DatasetVersionData


def get_public_dataset_version_for_gear_binding(client: BayesGQLClient, q: str):
    query = """
    query PublicDatasetVersions($status: [DatasetStatusInput], $tagIds: [Int!], $q: String!) {
      publicDatasetVersions(status: $status, tagIds: $tagIds, q: $q) {
        data {
          semanticBindingName
          createdAt
        }
      }
    }
    """
    variables = {"status": "VALID", "tagIds": [0], "q": q}
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

    result = response.get("publicDatasetVersions", {}).get("data", [])
    if not result:
        return None

    return PublicDatasetVersions(data=[DatasetVersion(**dataset) for dataset in result])


def get_party_private_dataset_version_for_gear_binding(client: BayesGQLClient, party_name, q: str):
    query = """
        query Data($partyId: ID!, $status: [DatasetStatusInput], $q: String!) {
          party(id: $partyId) {
            datasetVersions(status: $status, q: $q) {
              data {
                semanticBindingName
                createdAt
              }
            }
          }
        }
    """
    variables = {"partyId": party_name, "status": ["ALL"], "q": q}
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

    result = response.get("party", {})
    if not result or not result.get("datasetVersions"):
        return None

    return DatasetVersionData(**result["datasetVersions"])


def get_party_job_output_for_gear_binding(client: BayesGQLClient, party_name):
    query = """
      query Jobs($partyId: ID!, $status: [JobStatusInput]) {
          party(id: $partyId) {
            jobs(status: $status) {
              data {
                output {
                  path
                }
                createdAt
              }
            }
          }
        }  
    """
    variables = {"partyId": party_name, "status": ["CANCELLED", "SUCCEEDED", "FAILED"]}
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

    result = response.get("party", {})
    if not result or not result.get("jobs"):
        return None

    return JobData(**result["jobs"])
