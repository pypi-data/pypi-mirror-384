from typing import Optional

from bayes.client.base import BayesGQLClient
from bayes.client import dataset_version_client
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.utils import Utils


def get_dataset_version_for_gear_binding(party_name, flag, query):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    list_data = []

    # 先得到 PUBLIC
    public_dataset_version_list = dataset_version_client.get_public_dataset_version_for_gear_binding(gql_client, query)

    if public_dataset_version_list is not None:
        for dataset_version in public_dataset_version_list.data:
            data = [
                "PUBLIC",
                dataset_version.semanticBindingName,
                Utils.date_from_now(dataset_version.createdAt),
                f"{flag} {dataset_version.semanticBindingName}:/input[0-4]"
            ]
            list_data.append(data)

    # user PRIVATE
    party_dataset_version_list = dataset_version_client.get_party_private_dataset_version_for_gear_binding(gql_client,
                                                                                                           party_name,
                                                                                                           query)

    if party_dataset_version_list and len(party_dataset_version_list.data) > 0:
        list_data.append(["-"])

    if party_dataset_version_list is not None:
        for dataset_version in party_dataset_version_list.data:
            data = [
                "PRIVATE",
                dataset_version.semanticBindingName,
                Utils.date_from_now(dataset_version.createdAt),
                f"{flag} {dataset_version.semanticBindingName}:/input[0-4]"
            ]
            list_data.append(data)

    if query is None or query == "":
        # job output
        party_job_output_list = dataset_version_client.get_party_job_output_for_gear_binding(gql_client, party_name)

        if party_job_output_list and len(party_job_output_list.data) > 0:
            list_data.append(["-"])

        if party_job_output_list is not None:
            for job_output in party_job_output_list.data:
                data = [
                    "OUTPUT",
                    job_output.output.path,
                    Utils.date_from_now(job_output.createdAt),
                    f"{flag} {job_output.output.path}:/output"
                ]
                list_data.append(data)

    return list_data
