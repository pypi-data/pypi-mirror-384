import logging
from typing import List, Tuple, Dict, Any, Optional

import typer

from bayes.client import job_run_client, gear_client
from bayes.client.base import BayesGQLClient
from bayes.error import Error
from bayes.model.file.openbayes_yaml import OpenBayesYaml
from bayes.model.file.settings import BayesEnvConfig, BayesSettings, TypeHyperTuning, DefaultJobModeWorkSpace, \
    DefaultBatchJobModeWorkSpace, DefaultJobModeTask, DefaultBatchJobModeTask
from bayes.model.party import ModeEnum
from bayes.usercases import gear_usecase


def create(party_name, directory, project_id, mode, yaml: OpenBayesYaml, datasets: List[str], node_count: int, runtime,
           resource, code_id, command, message) -> Tuple[str, str, Exception]:
    if not project_id:
        project_id, _, project_name, err = gear_usecase.read(directory)
        if err:
            logging.error("Error reading project ID: %s", err)
            return "", "", err

    if len(datasets) == 0 and yaml is not None:
        datasets = yaml.get_dataset_bindings()
        # print(f"yaml.get_dataset_bindings(): {datasets}")

    if runtime == "" and yaml is not None:
        runtime = yaml.get_runtime()

    if resource == "" and yaml is not None:
        resource = yaml.resource

    if command == "" and yaml is not None:
        command = yaml.command

    if node_count <= 0 and yaml is not None and yaml.node >= 1:
        node_count = yaml.node
        if node_count < 1:
            node_count = 1

    parameters: Dict[str, Any] = {}
    if yaml is not None and yaml.parameters is not None:
        parameters = yaml.parameters

    if code_id is None and (mode == ModeEnum.task or mode == ModeEnum.hypertuning):
        return "", "", Error("源代码上传失败，无法创建容器")
    
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    frontend_value = ""
    job_id = ""
    #     如果是hypertuning
    if mode == ModeEnum.hypertuning:
        try:
            hypertuning = job_run_client.create_hypertuning(party_name, gql_client, project_id, datasets, runtime,
                                                            resource,
                                                            code_id, command, yaml.hyper_tuning)
            frontend_value = hypertuning.get_link_value("frontend")
            job_id = hypertuning.id
        except Exception as e:
            return "", "", e
    else:
        try:
            job = job_run_client.create(party_name, gql_client, mode, project_id, datasets, runtime, resource, code_id,
                                        command, parameters, node_count)

            frontend_value = job.get_link_value("frontend")
            job_id = job.id
        except Exception as e:
            return "", "", e

    if message != "":
        err = job_run_client.update_job_description(gql_client, party_name, job_id, message)
        if err is not None:
            return frontend_value, job_id, err

    return frontend_value, job_id, None


def restart(jid, party_name, data, runtime, resource, task_command, nodeCount, message):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    job = gear_client.get_job_by_id(gql_client, jid, party_name)
    if job is None:
        return None, f"job {jid} not found"

    mode = job.mode

    if len(data) == 0:
        data = job.get_job_dataBindings()

    if runtime == "":
        runtime = job.get_runtime()
    if resource == "":
        resource = job.resource.name

    frontend_value = ""
    job_id = ""
    if mode == DefaultJobModeWorkSpace:
        job = job_run_client.restart_workspace(gql_client, party_name, jid, runtime, resource, data, [])
        frontend_value = job.get_link_value("frontend")
        job_id = job.id
    elif mode == DefaultBatchJobModeWorkSpace:
        job = job_run_client.restart_batch_workspace(gql_client, party_name, jid, runtime, resource, data, [])
        frontend_value = job.get_link_value("frontend")
        job_id = job.id
    #     task 或者 batch task create
    elif mode == DefaultJobModeTask or DefaultBatchJobModeTask:
        if task_command == "" or task_command is None:
            if job.command == "" or job.command is None:
                print("task command 不能为空")
                raise typer.Exit(code=1)
            else:
                task_command = job.command

        if nodeCount == -1:
            nodeCount = job.children_count()

        frontend_value, job_id, _ = create(party_name, "", job.project.id, mode, None, data, nodeCount, runtime, resource, job.sourceCode.id, task_command, message)

    return frontend_value, job_id


