from typing import Optional, List

import wcwidth
import unicodedata
from tabulate import tabulate
from bayes.error import Error
from bayes.client import org_client
from bayes.client.base import BayesGQLClient
from bayes.client.org_client import UserOrgsModel
from bayes.model.file.settings import BayesSettings, BayesEnvConfig


def is_exist(org_id):
    if org_id is None or org_id == "":
        return False

    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, None)
    try:
        org = org_client.get_org(gql_client, org_id)
        return org.id == org_id
    except Error as e:
        print(e.message)
        return False


def list_user_orgs(username):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    return org_client.get_user_orgs(gql_client, username)


def display_table(data, headers):
    # 计算每一个单元格的显示宽度
    def cell_width(cell):
        if cell is None:
            cell = ""
        return sum([wcwidth.wcwidth(c) for c in str(cell)])

    # 找到每一列的最大宽度
    max_cols = len(headers)
    data = [row[:max_cols] + [""] * (max_cols - len(row)) for row in data]

    col_widths = [max(cell_width(row[i]) for row in [headers] + data) for i in range(max_cols)]

    # 调整每个单元格的宽度到最大宽度
    adjusted_data = []
    for row in data:
        adjusted_row = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            pad_space = col_widths[i] - cell_width(cell_str)
            adjusted_row.append(cell_str + ' ' * pad_space)
        adjusted_data.append(adjusted_row)

    adjusted_headers = []
    for i, header in enumerate(headers):
        header_str = str(header)
        pad_space = col_widths[i] - cell_width(header_str)
        adjusted_headers.append(header_str + ' ' * pad_space)

    table = tabulate(adjusted_data, adjusted_headers, tablefmt="plain", stralign="left", numalign="left")
    print(table)
    return table


def list_display_table(user_orgs_data):
    headers = ["ROLE", "ID", "NAME"]
    result = process_user_orgs(user_orgs_data)
    display_table(result, headers)


def process_user_orgs(user_orgs: List[UserOrgsModel]):
    if user_orgs is None:
        user_orgs = []
    data = [[org.role, org.org.id, org.org.displayName] for org in user_orgs]
    return data


def user_contains_org(username, orgName):
    user_orgs = list_user_orgs(username)
    for user_org in user_orgs:
        if user_org.org.id == orgName:
            return True
    return False
