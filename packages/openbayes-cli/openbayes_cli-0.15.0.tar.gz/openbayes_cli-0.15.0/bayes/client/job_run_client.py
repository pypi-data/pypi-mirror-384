import json
import sys
from enum import Enum
from typing import Tuple, Optional, List

import pydantic
import typer
from gql.transport.exceptions import TransportQueryError
from pydantic import BaseModel, Field

from bayes.client.base import BayesGQLClient
from bayes.client.gear_client import Job, JobOutputBinding, DatasetBinding
from bayes.model.file.openbayes_yaml import ParameterSpec, HyperTuning, DEFAULT_PARALLEL_COUNT
from bayes.model.file.settings import DefaultJobModeTask, DefaultBatchJobModeTask, DefaultJobModeWorkSpace, \
    DefaultBatchJobModeWorkSpace
from bayes.model.party import ModeEnum
from bayes.utils import Utils
from bayes.client.gear_client import DataBinding as job_dataBindings


class BindingAuthType(str, Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"


class DataBinding(BaseModel):
    path: str
    name: str
    bindingAuth: BindingAuthType


class BatchTask(BaseModel):
    size: int
    command: str
    code: str


class NewTaskInput(BaseModel):
    command: str
    code: str


class NewWorkspaceInput(BaseModel):
    code: str


class BatchWorkSpace(BaseModel):
    code: str
    size: int


class TagInput(BaseModel):
    name: Optional[str] = None


class VariableInput(BaseModel):
    mode: str
    projectId: str
    runtime: str
    resource: str
    newBatchTask: Optional[BatchTask] = None
    newTask: Optional[NewTaskInput] = None
    newWorkspace: Optional[NewWorkspaceInput] = None
    newBatchWorkspace: Optional[BatchWorkSpace] = None
    dataBindings: Optional[List[DataBinding]] = None
    tagNames: Optional[List[TagInput]] = None


class Algorithm(Enum):
    GRID = "Grid"
    RANDOM = "Random"
    BAYESIAN = "Bayesian"


class IntegerParameterSpecInput(BaseModel):
    scaleType: str
    minValue: int
    maxValue: int


class DoubleParameterSpecInput(BaseModel):
    scaleType: str
    minValue: float
    maxValue: float


class DiscreteParameterSpecInput(BaseModel):
    discreteValues: List[float]


class CategoryParameterSpecInput(BaseModel):
    categoricalValues: List[str]


class ParameterSpecInput(BaseModel):
    name: str
    integerParameterSpec: Optional[IntegerParameterSpecInput] = None
    doubleParameterSpec: Optional[DoubleParameterSpecInput] = None
    discreteParameterSpec: Optional[DiscreteParameterSpecInput] = None
    categoryParameterSpec: Optional[CategoryParameterSpecInput] = None


class CreateHypertuningInput(BaseModel):
    tagNames: Optional[List[TagInput]] = None
    runtime: str
    resource: str
    projectId: Optional[str] = None
    code: str
    command: str
    dataBindings: Optional[List[DataBinding]] = None
    maxJobCount: int
    parallelCount: int
    hyperparameterMetric: str
    sideMetrics: Optional[List[str]] = None
    goal: str
    algorithm: str
    parameterSpecs: List[ParameterSpecInput]


def build_command(command: str, parameters: dict) -> str:
    if not parameters:
        return command
    else:
        param_str = " ".join([f"--{k}={v}" for k, v in parameters.items()])
        return f"{command} {param_str}"


def get_graphql_binding_datasets(datasets: List[str]) -> List[DataBinding]:
    result = []

    for dataset in datasets:
        list_parts = dataset.split(":")
        if len(list_parts) == 2:
            result.append(DataBinding(
                name=list_parts[0],
                path=list_parts[1],
                bindingAuth=BindingAuthType.READ_ONLY
            ))
        elif len(list_parts) == 3:
            auth = list_parts[2].upper()
            if auth == "RO" or auth == "READ_ONLY":
                result.append(DataBinding(
                    name=list_parts[0],
                    path=list_parts[1],
                    bindingAuth=BindingAuthType.READ_ONLY
                ))
            elif auth == "RW" or auth == "READ_WRITE":
                result.append(DataBinding(
                    name=list_parts[0],
                    path=list_parts[1],
                    bindingAuth=BindingAuthType.READ_WRITE
                ))

    return result


def create(party_name, client: BayesGQLClient, mode, project_id, datasets: List[str], runtime, resource, code_id,
           command, parameters,
           node_count):
    input_data = VariableInput(
        mode=mode,
        projectId=project_id,
        runtime=runtime,
        resource=resource
    )
    input_data.tagNames = [TagInput(name="BUSINESS_CHANNEL_ML")]

    upper_mode = mode.upper()
    if upper_mode == DefaultJobModeTask or upper_mode == DefaultBatchJobModeTask:
        if node_count > 1:
            input_data.newBatchTask = BatchTask(
                size=node_count,
                code=code_id,
                command=build_command(command, parameters)
            )
            input_data.mode = "BATCH_TASK"
        else:
            input_data.mode = "TASK"
            input_data.newTask = NewTaskInput(
                code=code_id,
                command=build_command(command, parameters)
            )
    elif upper_mode == DefaultJobModeWorkSpace or upper_mode == DefaultBatchJobModeWorkSpace:
        if node_count > 1:
            input_data.mode = "BATCH_WORKSPACE"
            input_data.newBatchWorkspace = BatchWorkSpace(
                code=code_id,
                size=node_count
            )
        else:
            input_data.mode = "WORKSPACE"
            input_data.newWorkspace = NewWorkspaceInput(
                code=code_id
            )

    if datasets and len(datasets) > 0:
        input_data.dataBindings = get_graphql_binding_datasets(datasets)

    query = """
      mutation CreateJob($userId: String!, $input: CreateJobInput) {
      createJob(userId: $userId, input: $input) {
        id
        links {
          name
          value
        }
      }
    }
    """

    variables = {"userId": party_name, "input": input_data.model_dump()}
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
        raise ValueError(f"create job error: {full_error_message}")

    result = response.get("createJob")
    if result is None:
        raise ValueError("create job result is none")

    return Job(**result)


class UpdateJobInput(BaseModel):
    description: Optional[str] = None


def convert_to_parameter_spec_input(spec):
    if spec.type == 'DOUBLE':
        return ParameterSpecInput(
            name=spec.name,
            doubleParameterSpec=DoubleParameterSpecInput(
                scaleType=spec.scale_type,
                minValue=spec.min_value,
                maxValue=spec.max_value
            )
        )
    elif spec.type == 'INTEGER':
        return ParameterSpecInput(
            name=spec.name,
            integerParameterSpec=IntegerParameterSpecInput(
                scaleType=spec.scale_type,
                minValue=spec.min_value,
                maxValue=spec.max_value
            )
        )
    elif spec.type == 'DISCRETE':
        return ParameterSpecInput(
            name=spec.name,
            discreteParameterSpec=DiscreteParameterSpecInput(
                discreteValues=spec.discrete_values
            )
        )
    elif spec.type == 'CATEGORICAL':
        return ParameterSpecInput(
            name=spec.name,
            categoryParameterSpec=CategoryParameterSpecInput(
                categoricalValues=spec.categorical_values
            )
        )
    else:
        raise ValueError(f"Unsupported parameter spec type: {spec.type}")


class BindingAuth(str, Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"


class DataBindingInput(BaseModel):
    name: str
    path: str
    bindingType: Optional[str] = None
    bindingAuth: Optional[BindingAuth] = None


class JobParameterInput(BaseModel):
    name: str
    value: pydantic.Json


class RestartWorkspaceInput(BaseModel):
    dataBindings: List[DataBindingInput]
    runtime: str
    resource: str
    parameters: Optional[List[JobParameterInput]] = Field(default_factory=list)
    useRDMADevices: bool = False


class RestartBatchWorkspaceInput(BaseModel):
    dataBindings: List[DataBindingInput]
    runtime: str
    resource: str
    parameters: Optional[List[JobParameterInput]] = Field(default_factory=list)
    useRDMADevices: bool = False
    size: Optional[int] = None


def create_hypertuning(party_name, client: BayesGQLClient, project_id, datasets, runtime, resource, code_id,
                       command, hyper_tuning: HyperTuning):
    # 判断hyper_tuning的参数，不为空字符串和None
    if Utils.is_empty_or_none(hyper_tuning.hyperparameter_metric) or Utils.is_empty_or_none(
            hyper_tuning.algorithm) or Utils.is_empty_or_none(hyper_tuning.goal):
        print("请检查输入的 hupertuning 参数")
        raise typer.Exit(code=1)

    if Utils.is_empty_or_none(command):
        print("command 不能为空")
        raise typer.Exit(code=1)

    if Utils.is_empty_or_none(code_id):
        print("code_id 不能为空")
        raise typer.Exit(code=1)

    hyper_tuning_algorithm = Algorithm(hyper_tuning.algorithm.capitalize())

    parameter_specs = hyper_tuning.get_parameter_specs()
    parameter_specs_input = [convert_to_parameter_spec_input(spec) for spec in parameter_specs]

    input_data = CreateHypertuningInput(
        projectId=project_id,
        runtime=runtime,
        resource=resource,
        command=command,
        code=code_id,
        maxJobCount=hyper_tuning.max_job_count,
        hyperparameterMetric=hyper_tuning.hyperparameter_metric,
        goal=hyper_tuning.goal,
        algorithm=hyper_tuning_algorithm,
        parameterSpecs=parameter_specs_input,
        sideMetrics=hyper_tuning.side_metrics,
        parallelCount=max(DEFAULT_PARALLEL_COUNT, hyper_tuning.parallel_count)
    )

    if datasets and len(datasets) > 0:
        input_data.dataBindings = get_graphql_binding_datasets(datasets)

    input_data.tagNames = [TagInput(name="BUSINESS_CHANNEL_ML")]

    query = """
    mutation CreateHypertuning($userId: String!, $input: CreateHypertuningInput!) {
      createHypertuning(userId: $userId, input: $input) {
        id
        links {
          name
          value
        }
      }
    }
    """
    variables = {"userId": party_name, "input": input_data.model_dump()}

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

    result = response.get("createHypertuning")
    if result is None:
        raise ValueError("create hypertuning result is none")

    return Job(**result)


def update_job_description(client: BayesGQLClient, party_name, job_id, message):
    query = """
        mutation UpdateJob($username: String!, $jobId: String!, $input: UpdateJobInput!) {
          updateJob(userId: $username, jobId: $jobId, input: $input) {
            id
          }
        }
    """
    input_data = UpdateJobInput(description=message)
    variables = {"username": party_name, "jobId": job_id, "input": input_data.model_dump()}
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

    result = response.get("updateJob")
    if result is None:
        raise ValueError("updateJob result is none")

    return Job(**result)


def get_restart_job_graphql_dataBindings(dataBindings: List[str]) -> DataBindingInput:
    result = []
    for dataBinding in dataBindings:
        list_parts = dataBinding.split(":")
        if len(list_parts) == 2:
            name = list_parts[0]
            path = list_parts[1]

            binding_type = "OUTPUT" if name.endswith("/output") else None
            result.append(DataBindingInput(
                name=name,
                path=path,
                bindingAuth=BindingAuthType.READ_ONLY,
                bindingType=binding_type
            ))
        elif len(list_parts) == 3:
            name = list_parts[0]
            path = list_parts[1]

            binding_type = "OUTPUT" if name.endswith("/output") else None

            auth = list_parts[2].upper()
            if auth == "RO" or auth == "READ_ONLY":
                result.append(DataBindingInput(
                    name=name,
                    path=path,
                    bindingAuth=BindingAuthType.READ_ONLY
                ))
            elif auth == "RW" or auth == "READ_WRITE":
                result.append(DataBindingInput(
                    name=name,
                    path=path,
                    bindingAuth=BindingAuthType.READ_WRITE
                ))

    return result


def restart_workspace(client: BayesGQLClient, party_name, jid, runtime, resource, dataBindings, parameters):
    query = """
    mutation RestartWorkspace($userId: String!, $jobId: String!, $input: RestartWorkspaceInput!) {
      restartWorkspace(userId: $userId, jobId: $jobId, input: $input) {
        id
        status
        links {
          name
          value
        }
      }
    }
    """

    input_data = RestartWorkspaceInput(
        runtime=runtime,
        resource=resource,
        parameters=parameters,
        dataBindings=get_restart_job_graphql_dataBindings(dataBindings) if dataBindings else []
    )

    variables = {"userId": party_name, "jobId": jid, "input": input_data.model_dump()}

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

    result = response.get("restartWorkspace")
    if result is None:
        raise ValueError("restartWorkspace result is none")

    return Job(**result)


def restart_batch_workspace(client: BayesGQLClient, party_name, jid, runtime, resource, dataBindings, parameters):
    query = """
    mutation RestartBatchWorkspace($userId: String!, $jobId: String!, $input: RestartBatchWorkspaceInput!) {
      restartBatchWorkspace(userId: $userId, jobId: $jobId, input: $input) {
        id
        status
        links {
          name
          value
        }
      }
    }
    """

    input_data = RestartBatchWorkspaceInput(
        runtime=runtime,
        resource=resource,
        parameters=parameters,
        dataBindings=get_restart_job_graphql_dataBindings(dataBindings) if dataBindings else []
    )

    variables = {"userId": party_name, "jobId": jid, "input": input_data.model_dump()}

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

    result = response.get("restartBatchWorkspace")
    if result is None:
        raise ValueError("restartBatchWorkspace result is none")

    return Job(**result)
