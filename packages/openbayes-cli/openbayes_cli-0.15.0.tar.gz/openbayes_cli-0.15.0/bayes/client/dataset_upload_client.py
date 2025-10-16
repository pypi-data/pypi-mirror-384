from typing import Tuple, Optional

import requests
from pydantic import BaseModel, Field

from bayes.model.file.settings import BayesSettings


class DatasetRequestUploadUrl(BaseModel):
    upload_url: str
    token: str
    version: int
    clean_session_url: str = Field(default=None)


def upload_request(did) -> Tuple[Optional[DatasetRequestUploadUrl], Optional[Exception]]:
    # https://beta.openbayes.com/api/users/Qion1/datasets/upload-request?dataset=did&protocol=tusd
    default_env = BayesSettings().default_env
    url = f"{default_env.endpoint}/api/users/{default_env.username}/datasets/upload-request?dataset={did}&protocol=tusd"
    print(f"dataset upload_request url:{url}")
    auth_token = default_env.token

    try:
        response = requests.post(url, headers={"Authorization": f"Bearer {auth_token}"})
    except requests.RequestException as e:
        print(f"upload_request exception:{e}")
        return None, e

    print(f"upload_request response.content:{response.content}")

    if response.status_code != 200:
        return None, Exception(f"Request failed with status code {response.status_code}")

    try:
        result = response.json()
        upload_request = DatasetRequestUploadUrl(**result)
        return upload_request, None
    except ValueError as e:
        return None, e


