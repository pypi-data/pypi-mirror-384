from typing import Optional, List

from bayes.client import resource_client
from bayes.client.base import BayesGQLClient
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.model.resource import ComputingResouce, ResourceData
from bayes.usercases.org_usecase import display_table
from bayes.utils import Utils


def get_resource_list(partyId, type, labels) -> List[ComputingResouce]:
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    resources = resource_client.get_resources(gql_client, partyId, type, labels)
    resource_quota = resource_client.get_resource_quota(gql_client, partyId)
    resource_limitation = resource_client.get_resource_limitation(gql_client, partyId)

    # 转换为字典列表
    resources = [resource.model_dump() for resource in resources]
    # 将资源配额转化为字典
    quota_dict = {}
    if resource_quota.computationQuota:
        for quota in resource_quota.computationQuota:
            quota_dict[quota.key] = quota.value.availableMinutes

    # 将资源限制转化为字典
    limitation_dict = {}
    for limitation in resource_limitation.resources:
        limitation_dict[limitation.key] = limitation.value.limit

    result_list = []
    for resource in resources:
        resource_data = ResourceData(**resource)
        data = ComputingResouce(
            resource=resource_data,
            quota=quota_dict.get(resource['name'], 0),  # 默认值为0
            limitation=limitation_dict.get(resource['name'], 1)  # 默认值为1
        )
        result_list.append(data)

    return result_list


def process_resource_list_data(resource_list, flag):
    result = []

    for item in resource_list:
        line = []
        line.append(item.resource.name)
        line.append(item.resource.gpu_string())
        line.append(item.resource.cpu_string())
        line.append(item.resource.memory_string())
        line.append(item.resource.disk_string())
        line.append(item.resource.get_resource_desc())

        if getattr(item, 'quota', 0) > 0:
            line.append(Utils.format_quota_string(item.quota))
        else:
            line.append("N/A")

        line.append(str(item.limitation))
        line.append(f"{flag} {item.resource.name}")
        result.append(line)

    return result


def list_resources_display_table(flag: str, partyId, type, labels):
    resource_list = get_resource_list(partyId, type, labels)
    headers = ["NAME", "GPU", "CPU", "MEMORY", "DISK", "DESC", "QUOTA", "LIMITATION", "USAGE"]
    result = process_resource_list_data(resource_list, flag)
    return display_table(result, headers)

