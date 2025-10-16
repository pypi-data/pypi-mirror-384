import json
import sys

from gql.transport.exceptions import TransportQueryError

from bayes.client.base import BayesGQLClient
from bayes.error import Error
from bayes.model.runtime import ClusterRuntime


def get_runtimes(client: BayesGQLClient, partyId, type, labels, runtimeType):
    query = """
     query NormalClusterRuntimes($partyId: String, $type: [DeployType], $labels: [String!], $runtimeType: [RuntimeType]) {
          normalClusterRuntimes(partyId: $partyId, type: $type, labels: $labels, runtimeType: $runtimeType) {
            framework
            name
            version
            type
            device
            deprecated
            labels
          }
        }
    """
    variables = {"partyId": partyId, "type": type, "labels": labels, "runtimeType": runtimeType}
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

    runtime_data_list = response.get("normalClusterRuntimes", [])
    if runtime_data_list is None or not runtime_data_list:
        return None

    return [ClusterRuntime(**runtime_data) for runtime_data in runtime_data_list]
