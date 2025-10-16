from typing import List, Optional

from bayes.client import runtime_client
from bayes.client.base import BayesGQLClient
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.model.runtime import ClusterRuntime
from bayes.usercases.org_usecase import display_table


def get_list_runtimes(partyId, type, labels, runtimeType) -> List[ClusterRuntime]:
    default_env = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    runtimes_list = runtime_client.get_runtimes(gql_client, partyId, type, labels, runtimeType)

    # 过滤掉已经废弃的运行时项
    filtered_runtimes = [runtime for runtime in runtimes_list if not runtime.deprecated]

    # 去重和标签过滤方法
    def remove_repeated_element(arr: List[ClusterRuntime]) -> List[ClusterRuntime]:
        new_arr = []
        runtime_keys = set()
        for runtime in arr:
            key = f"{runtime.framework}-{runtime.version}"
            if key not in runtime_keys:
                runtime_keys.add(key)
                if "MACHINE_LEARNING" in runtime.labels:
                    new_arr.append(runtime)
        return new_arr

    # 返回去重并过滤后的运行时列表
    return remove_repeated_element(filtered_runtimes)


def process_runtimes_data(runtimes: List[ClusterRuntime], flag: str) -> List[List[str]]:
    list_ = []
    last_framework = ""

    for runtime in runtimes:
        data = []
        framework = ""

        if last_framework != runtime.framework:
            last_framework = runtime.framework
            framework = runtime.framework

        data.append(framework)
        data.append(runtime.version_string())
        data.append(f"{flag} {runtime.usage()}")
        list_.append(data)

    return list_


def list_runtimes_display_table(runtimes: List[ClusterRuntime], flag):
    headers = ["FRAMEWORK", "VERSION", "USAGE"]
    result = process_runtimes_data(runtimes, flag)
    return display_table(result, headers)
