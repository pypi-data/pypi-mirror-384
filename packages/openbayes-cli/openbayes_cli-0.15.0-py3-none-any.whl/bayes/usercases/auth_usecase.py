import os
from typing import Optional

import typer

from bayes.client import user_client
from bayes.client.base import BayesGQLClient
from bayes.error import Error
from bayes.model.file.settings import BayesSettings, BayesEnvConfig


def get_default_credential_userinfo():
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, None)

    if not default_env.token:
        print("用户还未登陆")
        return None

    try:
        login_model = user_client.login_with_token(gql_client, default_env.token)
        # 登陆成功，获得用户信息，去修改文件
        BayesSettings().login(login_model.username, login_model.token)
        return login_model
    except Error as e:
        print("登陆失败，请重新使用密码或者新的令牌登录")
        raise typer.Exit(code=1)


def check_login():
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env
    gql_client = BayesGQLClient(default_env.graphQL, None)
    
    # 检查是否已登录
    if default_env.name and default_env.token:
        return True
    
    # 从环境变量获取信息
    token = os.getenv("OPENBAYES_TOKEN")
    org = os.getenv("OPENBAYES_ORG")
    user = os.getenv("OPENBAYES_USER")

    # print(f"从环境变量获取信息: token:{token}, org:{org}, user:{user}")
    
    if not token:
        return False
    
    try:
        login_model = user_client.login_with_token(gql_client, token)
        bayes_settings.login(login_model.username, token)
        # 更新 orgName
        if org and user:
            if org != user:
                bayes_settings.switch_org(org)

        return True
    except Error as e:
        print(f"登陆失败: {e}")
        print("请重新使用密码或者新的令牌登录")
        raise typer.Exit(code=1)


def is_working_on_org():
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    if default_env.token and default_env.orgName:
        return True
    else:
        return False