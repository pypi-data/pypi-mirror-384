import json
import sys
from datetime import datetime

from gql.transport.exceptions import TransportQueryError
from pydantic import BaseModel

from bayes.client.base import BayesGQLClient


class SSHKey(BaseModel):
    id: int
    name: str
    fingerprint: str
    createdAt: datetime


def get_keys(client: BayesGQLClient, username: str):
    query = """
    query Keys($userId: String!) {
      keys(userId: $userId) {
        id
        name
        fingerprint
        createdAt
      }
    }  
    """
    variables = {"userId": username}
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

    keys_list = response.get("keys", [])
    if keys_list is None or not keys_list:
        return None

    return [SSHKey(**key) for key in keys_list]


def create_key(client: BayesGQLClient, userId, name, content):
    query = """
    mutation CreateSSHKey($userId: String!, $name: String!, $content: String!) {
      createSSHKey(userId: $userId, name: $name, content: $content) {
        id
        name
        fingerprint
        createdAt
      }
    }
    """
    variables = {"userId": userId, "name": name, "content": content}
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

    result = response.get("createSSHKey")
    if result is None:
        raise Exception("create SSHKey result is none")

    return SSHKey(**result)
