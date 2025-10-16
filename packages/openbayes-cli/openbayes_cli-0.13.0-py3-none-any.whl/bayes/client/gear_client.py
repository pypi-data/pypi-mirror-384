import json
import sys
from datetime import datetime
from typing import List, Optional, Union, Tuple

import requests
from gql.transport.exceptions import TransportQueryError
from pydantic import BaseModel, Field

from bayes.client.base import BayesGQLClient
from bayes.error import Error


class DownloadInfoPayload(BaseModel):
    url: Optional[str]
    type: Optional[str]
    name: Optional[str]

    def is_file(self) -> bool:
        return self.type == "file"

    def get_file_name(self) -> str:
        if self.is_file():
            return self.name

        if self.name.endswith(".zip"):
            return self.name
        return self.name + ".zip"


class Resource(BaseModel):
    name: str


class Runtime(BaseModel):
    framework: str
    version: str


class Link(BaseModel):
    name: str
    value: Optional[str]


class DataBinding(BaseModel):
    __typename: str
    mountPath: Optional[str] = None
    semanticBindingName: Optional[str] = None
    isDeleted: Optional[bool] = None


class DatasetBinding(DataBinding):
    bindingAuth: Optional[str] = None


class JobOutputBinding(DataBinding):
    id: str


class SourceCode(BaseModel):
    id: str


class Job(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    mode: Optional[str] = None
    resource: Optional[Resource] = None
    runtime: Optional[Runtime] = None
    subStatus: Optional[str] = None
    status: Optional[str] = None
    size: Optional[int] = None
    version: Optional[int] = None
    createdAt: Optional[datetime] = None
    links: Optional[List[Link]] = Field(default_factory=list)
    project: Optional['ProjectModel'] = None  # Forward reference
    dataBindings: Optional[List[Union[DataBinding, DatasetBinding, JobOutputBinding]]] = Field(default_factory=list)
    sourceCode: Optional[SourceCode] = None
    command: Optional[str] = None
    children: Optional[List['Job']] = Field(default_factory=list)
    batchParentId: Optional[str] = None

    def __init__(self, **data):
        data['dataBindings'] = self._parse_data_bindings(data.get('dataBindings', []))
        super().__init__(**data)

    def children_count(self) -> int:
        return len(self.children)

    def get_link_value(self, link_name: str) -> Optional[str]:
        for link in self.links:
            if link.name == link_name:
                return link.value
        return None

    def get_ssh_link(self) -> Optional[str]:
        """Get SSH connection link if available"""
        return self.get_link_value("ssh")

    def get_runtime(self) -> str:
        return f"{self.runtime.framework}-{self.runtime.version}"

    def is_running(self) -> bool:
        return self.status == "RUNNING"

    def is_finished(self) -> bool:
        return self.status in {"SUCCEEDED", "CANCELLED", "FAILED"}

    def get_job_dataBindings(self) -> List[str]:
        datasets = []
        for binding in self.dataBindings or []:
            # api server 数据绑定的格式 "^/output|/input[01234]|(/openbayes/input/input[01234])|(/openbayes/home)$"
            # 如果是 datset 就拼接成 Qion1/serving数据集/1:/input1:ro 要带上 bindingAuth:分割后有三部分部分
            # 如果是 output 就拼接成 Qion1/jobs/8.19-vli-1/2/2/output:/input1 :分割后只有两部分
            if isinstance(binding, DatasetBinding):
                data = f"{binding.semanticBindingName}:{binding.mountPath}:{binding.bindingAuth}"
                datasets.append(data)
            else:
                data = f"{binding.semanticBindingName}:{binding.mountPath}"
                datasets.append(data)
        return datasets

    @staticmethod
    def _parse_data_bindings(bindings):
        if bindings is None:
            return []

        parsed_bindings = []
        for item in bindings:
            typename = item.get('__typename')
            if typename == 'DatasetBinding':
                parsed_bindings.append(DatasetBinding(**item))
            elif typename == 'JobOutputBinding':
                parsed_bindings.append(JobOutputBinding(**item))
            else:
                parsed_bindings.append(DataBinding(**item))
        return parsed_bindings


class JobsData(BaseModel):
    data: List[Job] = []


class LatestJob(BaseModel):
    status: Optional[str] = None


class ProjectModel(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    links: Optional[List[Link]] = Field(default_factory=list)
    size: Optional[float] = None
    updatedAt: Optional[datetime] = None
    latestVersion: Optional[int] = None
    latestJob: Optional[LatestJob] = None
    jobs: Optional[JobsData] = None

    def get_link_value(self, link_name: str) -> Optional[str]:
        for link in self.links:
            if link.name == link_name:
                return link.value
        return None


def get_party_project_by_id_or_name(client: BayesGQLClient, party_id, id_or_name, tagsNames, page,
                                    perPage) -> ProjectModel:
    query = """
        query Projects($partyId: ID!, $q: String!, $page: Int!, $tagNames: [String!], $perPage: Int!) {
          party(id: $partyId) {
            projects(q: $q, page: $page, tagNames: $tagNames, perPage: $perPage) {
              data {
                id
                name
                links {
                  name
                  value
                }
              }
            }
          }
        }
    """
    variables = {"partyId": party_id, "q": id_or_name, "page": page, "tagNames": list(tagsNames), "perPage": perPage}
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

    result = response.get("party", {}).get("projects", {}).get("data", [])
    if result is None or not result:
        return None

    if isinstance(result, list) and isinstance(result[0], dict):
        return ProjectModel(**result[0])
    else:
        raise Error("Returned project data is not in the expected format.")


def create_project(client: BayesGQLClient, party_name, name, desc, tags):
    query = """
        mutation CreateProject($userId: String!, $name: String!, $description: String, $tagNames: [TagInput]) {
          createProject(userId: $userId, name: $name, description: $description, tagNames: $tagNames) {
            id
            name
            links {
              name
              value
            }
          }
        }
    """
    variables = {"userId": party_name, "name": name, "description": desc, "tagNames": list(tags)}
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

    result = response.get("createProject")
    if result is None:
        raise Error("create project result is none")

    return ProjectModel(**result)


def get_party_projects(client: BayesGQLClient, party_name, tags, page):
    query = """
        query Projects($partyId: ID!, $page: Int!, $tagNames: [String!]) {
          party(id: $partyId) {
            projects(page: $page, tagNames: $tagNames) {
              data {
                id
                name
                links {
                  name
                  value
                }
                size
                updatedAt
                latestVersion
                latestJob {
                  status
                }
              }
            }
          }
        }
    """
    variables = {"partyId": party_name, "page": page, "tagNames": list(tags)}

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

    project_data_list = response.get("party", {}).get("projects", {}).get("data", [])
    if not project_data_list:
        return None

    return [ProjectModel(**project_data) for project_data in project_data_list]


def get_project_jobs_by_id(client: BayesGQLClient, party_name, project_id, page):
    query = """
    query Project($projectId: String!, $userId: String!, $page: Int!) {
      project(projectId: $projectId) {
        jobs(userId: $userId, page: $page, projectId: $projectId) {
          data {
            id
            mode
            resource {
              name
            }
            runtime {
              framework
              version
            }
            status
            size
            version
            createdAt
            links {
              name
              value
            }
          }
        }
        id
        name
      }
    }

    """
    variables = {"userId": party_name, "projectId": project_id, "page": page}
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

    project_jobs_list = response.get("project", {})
    if not project_jobs_list:
        return None

    return ProjectModel(**project_jobs_list)


def get_logs(client: BayesGQLClient, jobId, party_name):
    query = """
    query jobLogs($userId: String!,$jobId: String!){
        jobLogs(userId: $userId, jobId: $jobId)
    }
    """
    variables = {"userId": party_name, "jobId": jobId}
    try:
        response = client.exec(query, variables)
        result = response.get("jobLogs", {})
        return result
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
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def get_job_by_id(client: BayesGQLClient, id, party_name):
    query = """
     query Job($userId: String!, $jobId: String!) {
      job(userId: $userId, jobId: $jobId) {
        id
        mode
        resource {
          name
        }
        runtime {
          framework
          version
        }
        subStatus
        status
        size
        version
        createdAt
        links {
            name
            value
        }
        dataBindings {
          mountPath
          semanticBindingName
          isDeleted
          ... on DatasetBinding {
            bindingAuth
          }
        }
        project {
          name
          id
        }
        ... on Task {
          sourceCode {
            id
          }
          command
        }
        ... on BatchTask {
          sourceCode {
            id
          }
          command
          size
          children {
            id
          }
        }
        batchParentId
      }
    }
    """
    variables = {"userId": party_name, "jobId": id}
    try:
        response = client.exec(query, variables)
    except Exception as e:
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
        return None

    result = response.get("job", {})
    if result is None or not result:
        return None

    return Job(**result)

def get_job_info_by_id(client: BayesGQLClient, id, party_name) -> Tuple[Optional[Job], Optional[str]]:
    query = """
        query Job($userId: String!, $jobId: String!) {
          job(userId: $userId, jobId: $jobId) {
            id
            name
            status
            links {
              value
              name
            }
          }
        }
    """
    variables = {"userId": party_name, "jobId": id}
    try:
        response = client.exec(query, variables)
    except Exception as e:
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

        return None, full_error_message

    result = response.get("job", {})
    if result is None or not result:
        return None, None
        
    return Job(**result), None


def get_output_download_link(client: BayesGQLClient, id, party_name, download_from):
    query = """
        mutation createJobOutputDownloadUrl($userId: String!, $jobId: String!, $key: String!) {
            createJobOutputDownloadUrl(userId: $userId, jobId: $jobId, key: $key) {
                url
                type
                name
            }
        }

    """
    variables = {"userId": party_name, "jobId": id, "key": download_from}
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

    result = response.get("createJobOutputDownloadUrl", {})
    if result is None or not result:
        return None

    return DownloadInfoPayload(**result)


def download(url, filename, is_finished):
    try:
        response = requests.get(url, stream=True)
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
    except Exception as err:
        print(f"Error: {err}")
        is_finished.put((False, err))
        return err

    is_finished.put((True, None))
    return None


def stopJob(client: BayesGQLClient, id, party_name):
    query = """
        mutation StopJob($userId: String!, $jobId: String!) {
          stopJob(userId: $userId, jobId: $jobId) {
            id
            links {
              name
              value
            }
            project {
              name
            }
          }
        }
    """
    variables = {"userId": party_name, "jobId": id}
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

    result = response.get("stopJob", {})
    if result is None or not result:
        return None

    return Job(**result)
