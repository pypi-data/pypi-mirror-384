from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


class BayesGQLClient:
    def __init__(self, endpoint, token) -> None:
        headers = {
            "Origin": endpoint
        }
        if token is not None:
            headers['Authorization'] = f'Bearer {token}'

        transport = AIOHTTPTransport(
            url=endpoint,
            headers=headers,
            ssl=True  # 显式启用SSL证书验证
        )
        self.client = Client(transport=transport)

    def exec(self, query, variable_values={}):
        return self.client.execute(gql(query), variable_values=variable_values)

