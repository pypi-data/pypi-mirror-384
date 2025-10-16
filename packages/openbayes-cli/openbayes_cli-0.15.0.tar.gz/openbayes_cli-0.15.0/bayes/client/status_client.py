from .base import BayesGQLClient


def health_check(endpoint):
    client = BayesGQLClient(endpoint, None)
    query = """
    query { __typename }
    """

    try:
        response = client.exec(query)
        return response is not None
    except Exception as e:
        return False
