import json
import sys

from gql.transport.exceptions import TransportQueryError

from bayes.client.base import BayesGQLClient
from bayes.error import Error
from bayes.model.resource import ResourceData, Quota, Limitations


def get_resources(client: BayesGQLClient, partyId, type, labels):
    query = """
    query NormalClusterResources($partyId: String, $type: [DeployType], $labels: [String]) {
      normalClusterResources(partyId: $partyId, type: $type, labels: $labels) {
        name
        memory
        type
        cpu {
          type
          millicores
          count
        }
        disk {
          type
          size
        }
        gpu {
          verboseName
          vendor
          type
          name
          mode
          memory
          group
          description
          count
        }
        verboseName
        gpuResource
        labels
      }
    }
    """
    variables = {"partyId": partyId, "type": type, "labels": labels}
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
        raise Error(full_error_message)

    resource_data_list = response.get("normalClusterResources", [])
    if resource_data_list is None or not resource_data_list:
        return None

    return [ResourceData(**resource_data) for resource_data in resource_data_list]


def get_resource_quota(client: BayesGQLClient, partyId):
    query = """
        query Quota($partyId: ID!) {
          party(id: $partyId) {
            quota {
              computationQuota {
                value {
                  availableMinutes
                }
                key
              }
            }
          }
        }
    """
    variables = {"partyId": partyId}
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
        raise Error(full_error_message)

    result = response.get("party", {}).get("quota", {})
    if not result:
        return None

    return Quota(**result)


def get_resource_limitation(client: BayesGQLClient, partyId):
    query = """
       query Resources($partyId: ID!) {
          party(id: $partyId) {
            limitations {
              resources {
                key
                value {
                  current
                  limit
                }
              }
            }
          }
        }
    """
    variables = {"partyId": partyId}
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
        raise Error(full_error_message)

    result = response.get("party", {}).get("limitations", {})
    if not result:
        return None

    return Limitations(**result)
