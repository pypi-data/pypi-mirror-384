import json
import sys

from gql.transport.exceptions import TransportQueryError

from .base import BayesGQLClient

from pydantic import BaseModel

from ..error import Error


class LoginModel(BaseModel):
    email: str
    token: str
    username: str


def login(client: BayesGQLClient, username: str, password: str) -> LoginModel:
    query = """
    mutation Login($username: String!, $password: String!) {
      login(username: $username, password: $password) {
        email
        token
        username
      }
    }
    """
    variables = {"username": username, "password": password}
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

    login_data = response.get("login")
    if login_data is None:
        raise Error("Login failed: Unexpected response format")

    return LoginModel(**login_data)


def login_with_token(client: BayesGQLClient, token):
    query = """
        query LoginWithToken($token: String!) {
            loginWithToken(token: $token) {
                email
                username
            }
        }
        """
    variables = {"token": token}
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

    login_data = response.get("loginWithToken")
    if login_data is None:
        raise Error("Login failed: Unexpected response format")

    return LoginModel(token=token, **login_data)
