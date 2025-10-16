import json
import sys

from gql.transport.exceptions import TransportQueryError
from pydantic import BaseModel

from bayes.client.base import BayesGQLClient
from bayes.error import Error


class PolicyModel(BaseModel):
    endpoint: str
    path: str
    accessKey: str
    secretKey: str


def get_datasetVersion_upload_policy(client: BayesGQLClient, party_name:str, datasetId:str, version:int, key:str) -> PolicyModel:
    query = """
    mutation CreateDatasetVersionUploadPolicy($userId: String!, $datasetId: String!, $version: Int!, $key: String!) {
        createDatasetVersionUploadPolicy(userId: $userId, datasetId: $datasetId, version: $version, key: $key) {
            endpoint
            accessKey
            secretKey
            path
        }
    }
    """
    variables = {
        "userId": party_name,
        "datasetId": datasetId,
        "version": version,
        "key": key
    }
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
    
    result = response.get("createDatasetVersionUploadPolicy", {})
    if result is None:
        raise Error("create project result is none")
    return PolicyModel(**result)


class SourceCodePolicyModel(BaseModel):
    id: str
    endpoint: str
    path: str
    accessKey: str
    secretKey: str


def get_source_code_upload_policy(client: BayesGQLClient, party_name: str, storageType: str) -> SourceCodePolicyModel:
    query = """
    mutation CreateSourceCodePolicy($userId: String!, $storageType: StorageType!) {
        createSourceCodePolicy(userId: $userId, storageType: $storageType) {
            id
            endpoint
            accessKey
            secretKey
            path
        }
    }
    """
    variables = {
        "userId": party_name,
        "storageType": storageType
    }
    try:
        response = client.exec(query, variables)
    except TransportQueryError as e:
        if e.errors:
            error_message = e.errors[0].get('message', 'Unknown error')
            extensions = e.errors[0].get('extensions', {})
            details = extensions.get('details', {})

            if details:
                details_str = json.dumps(details, ensure_ascii=False, indent=2)
                full_error_message = f"{error_message}. Details: {details_str}"
            else:
                full_error_message = error_message
        else:
            full_error_message = str(e)

        print(full_error_message, file=sys.stderr)
        sys.exit(1)
    
    result = response.get("createSourceCodePolicy", {})
    if result is None:
        raise Error("create source code policy result is none")
    return SourceCodePolicyModel(**result)