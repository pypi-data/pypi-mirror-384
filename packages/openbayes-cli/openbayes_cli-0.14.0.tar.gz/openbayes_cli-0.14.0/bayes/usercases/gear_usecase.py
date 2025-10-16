import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Tuple

import typer
from rich import filesize
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    ProgressColumn,
)

from bayes.client import gear_client, job_run_client
from bayes.client.base import BayesGQLClient
from bayes.client.gear_client import Job, ProjectModel
from bayes.error import Error
from bayes.model.file.openbayes_gear import (
    OpenBayesGearSettings,
    FILE_NAME as GEAR_FILE_NAME,
)
from bayes.model.file.openbayes_ignore import OpenBayesIgnoreSettings
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.usercases import dataset_version_usecase
from bayes.usercases.org_usecase import display_table
from bayes.utils import Utils


def get_project_by_id_or_name(party_name, id_or_name, tagsNames, page, perPage):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return gear_client.get_party_project_by_id_or_name(
        gql_client, party_name, id_or_name, tagsNames, page, perPage
    )


def create_project(party_name, name, desc, tags):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    return gear_client.create_project(gql_client, party_name, name, desc, tags)


def init_project(current_path, pid, project_name):
    gear_settings = OpenBayesGearSettings()
    gear_settings.create_or_update(current_path, pid, project_name)
    OpenBayesIgnoreSettings(Path(current_path)).load_or_create_default_yaml()


def get_party_projects(party_name, tags, page):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    return gear_client.get_party_projects(gql_client, party_name, tags, page)


def process_project_datas(project_data_list: List[ProjectModel]):
    if project_data_list is None:
        project_data_list = []

    data = [
        [
            project.latestJob.status if project.latestJob is not None else None,
            project.id,
            project.name,
            project.latestVersion,
            Utils.byte_size(project.size, True),
            Utils.date_from_now(project.updatedAt),
        ]
        for project in project_data_list
    ]
    return data


def list_projects_display_table(project_data_list):
    headers = ["STATUS", "PROJECT", "NAME", "VERSIONS", "SIZE", "UPDATED AT"]
    result = process_project_datas(project_data_list)
    display_table(result, headers)


def get_project_jobs_by_id(party_name, project_id, page):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    return gear_client.get_project_jobs_by_id(gql_client, party_name, project_id, page)


def process_project_jobs_data(project: ProjectModel):
    data = []

    if project.jobs and project.jobs.data:
        for job in project.jobs.data:
            ssh_info = "SSH可用" if job.is_running() and job.get_ssh_link() else "-"
            data.append(
                [
                    job.status,
                    job.id,
                    job.version,
                    job.mode,
                    job.resource.name,
                    job.runtime.framework,
                    Utils.byte_size(job.size, True),
                    ssh_info,
                    Utils.date_from_now(job.createdAt),
                ]
            )
    return data


def list_project_jobs_display_table(project: ProjectModel):
    headers = [
        "STATUS",
        "ID",
        "VERSION",
        "MODE",
        "RESOURCE",
        "RUNTIME",
        "SIZE",
        "SSH",
        "UPDATED AT",
    ]
    result = process_project_jobs_data(project)
    return display_table(result, headers)


def list_binding_datasets(party_name, flag, query):
    return dataset_version_usecase.get_dataset_version_for_gear_binding(
        party_name, flag, query
    )


def list_binding_datasets_display_table(binding_datasets):
    headers = ["TYPE", "NAME", "CREATED_AT", "USAGE"]
    return display_table(binding_datasets, headers)


def get_cur_path_string():
    return os.getcwd()


def get_download_target(download_target):
    if download_target == "":
        return get_cur_path_string()

    if not os.path.exists(download_target):
        try:
            os.makedirs(download_target, mode=0o755)
        except OSError as e:
            print(e)
            return get_cur_path_string()

    return download_target


def stopJob(id, party_name):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    return gear_client.stopJob(gql_client, id, party_name)


def follow_status(id, party_name, stop_with_running):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
    ) as progress:
        task = progress.add_task(f"[purple]Checking job status...", start=False)

        while True:
            # 获取最新的任务状态
            job = gear_client.get_job_by_id(gql_client, id, party_name)
            if job is None:
                progress.update(task, description=f"[red]Failed to fetch job details.")
                break

            # 更新任务描述
            progress.update(task, description=f"[cyan]{job.status}")

            # 判断任务是否已完成或应该停止
            if job.is_finished() or (stop_with_running and job.is_running()):
                progress.stop_task(task)
                # 清空进度条中的旋转器和描述
                progress.update(task, description="")
                progress.remove_task(task)
                break

            # 模拟时间延迟
            for _ in range(50):
                time.sleep(0.1)


def print_last_status(id, party_name):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    job = gear_client.get_job_by_id(gql_client, id, party_name)
    if job.is_finished():
        print("容器已关闭")
    elif job.is_running():
        print("容器运行中")
    else:
        print(f"容器状态：{job.status}")


def read(directory: str) -> Tuple[str, str, str, Exception]:
    try:
        gear_settings = OpenBayesGearSettings(config_path=directory / GEAR_FILE_NAME)
        gear_settings.load_from_file()
        gear = gear_settings.configuration
        
        # 检查 gear 是否为 None
        if gear is None:
            return "", "", "", Exception("未找到容器配置信息")
            
        return gear.id, gear.jid, gear.name, None
        
    except Exception as e:
        return "", "", "", e


def get_jobId_from_curPath(id):
    if id is not None:
        return id

    cur_path = Path(os.getcwd())
    _, jid, _, err = read(cur_path)
    
    # 处理错误情况
    if err is not None:
        print(f"未输入任务编码ID，且无法获取容器信息: {err}")
        print("请使用以下方式指定任务ID:")
        print("  1. 直接在命令中指定任务ID")
        print("  2. 在已初始化的容器目录下执行命令")
        raise typer.Exit(code=1)
        
    if Utils.is_empty_or_none(jid):
        print("未输入任务编码ID，且容器中未找到任务ID")
        print("请使用以下方式指定任务ID:")
        print("  1. 直接在命令中指定任务ID")
        print("  2. 先执行任务后再下载输出")
        raise typer.Exit(code=1)

    return jid


def get_job_by_id(id, party_name):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return gear_client.get_job_by_id(gql_client, id, party_name)

def get_job_info_by_id(id, party_name) -> Tuple[Optional[Job], Optional[str]]:
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    return gear_client.get_job_info_by_id(gql_client, id, party_name)

def update_job_description(party_name, jid, message):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    job_run_client.update_job_description(gql_client, party_name, jid, message)
