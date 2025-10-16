import json

import websocket
from websocket import WebSocketConnectionClosedException

from bayes.client import gear_client
from bayes.client.base import BayesGQLClient
from bayes.model.file.settings import BayesSettings


def get_logs(id, party_name):
    default_env = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    logs = gear_client.get_logs(gql_client, id, party_name)

    return logs


def get_logs_follow(id, party_name):
    default_env = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    job = gear_client.get_job_by_id(gql_client, id, party_name)
    if job:
        ws_url = job.get_link_value("websocket")
        if ws_url is None:
            return None, "不存在"
        # Establish WebSocket connection
        ws = websocket.WebSocket()
        ws.connect(ws_url)
        return ws, None
    else:
        return None, "不存在"


def receive_logs(ws: websocket.WebSocket, job_id: str):
    try:
        data = ws.recv()
    except (WebSocketConnectionClosedException, EOFError):
        return None, f"容器 {job_id} 已关闭，没有更多日志"
    except Exception as err:
        return None, err

    return data, None