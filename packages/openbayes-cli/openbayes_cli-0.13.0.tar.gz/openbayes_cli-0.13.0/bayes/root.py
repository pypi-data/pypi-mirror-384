from typing import Optional

import typer

from .client import user_client
from .client.base import BayesGQLClient

from .commands import gear, ssh, data, hpc
from .commands import org
from .error import credential_notfound_error, Error
from bayes.model.file.settings import BayesSettings, BayesEnvConfig
from bayes.usercases.switch_usercase import clean, is_exist
from .usercases import auth_usecase
from .utils import Utils
from .utils.add_global_param import add_no_upgrade_option

# 应用补丁，使所有命令忽略 --no-upgrade 参数
add_no_upgrade_option()

app = typer.Typer(
    help="OpenBayes 命令行工具",
    context_settings={"help_option_names": ["-h", "--help"]}
)

app.add_typer(ssh.app, name="ssh", help="SSH 相关操作")
app.add_typer(gear.app, name="gear", help="容器相关操作")
app.add_typer(org.app, name="org", help="组织相关操作")
app.add_typer(data.app, name="data", help="数据集相关操作")
app.add_typer(hpc.app, name="hpc", help="高性能计算相关操作")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
    ctx.obj = BayesSettings()


@app.command()
def login(ctx: typer.Context,
          username: str = typer.Argument(
              None, envvar="OPENBAYES_TOKEN", help="用户名 | 令牌"
          )):
    """
    登录

    用法：
        bayes login [用户名 | 令牌] [选项]

    可用选项：

        -h, --help   查看 login 的帮助
    """
    # 使用账户密码登录时：当用户名为 null 的时候要去 credentials 文件中看看 username 是否为null，因为登出的时候 username 是不覆盖为None
    # 如果 username is None，让用户输入，否则直接显示 请输入 xxx 的密码
    bayes_settings = ctx.obj
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    if username is None:
        env_username = default_env.username
        if env_username:
            username = env_username
        else:
            username = input("请输入用户名：")

    if username is not None and len(username) <= 39:
        if default_env.username == username and default_env.token and not Utils.is_token_expired(default_env.token):
            # 密码可能没有过期，但是因为修改了密码导致这个已有的 token 失效了，不能直接登陆，应该调用 login_with_token 登陆
            # print(f"{default_env.username} 已成功登入 {default_env.name}")
            login_with_token(bayes_settings, default_env, default_env.token)
            raise typer.Exit()
        else:
            login_with_password(bayes_settings, default_env, username)
            raise typer.Exit()
    elif username is not None and len(username) > 39:
        login_with_token(bayes_settings, default_env, username)
        raise typer.Exit()


def login_with_token(bayes_settings, default_env, username):
    try:
        gql_client = BayesGQLClient(default_env.graphQL, None)
        result = user_client.login_with_token(gql_client, username)
        bayes_settings.login(result.username, result.token)

        print(f"{result.username} 已成功登入 {default_env.name}")
    except Error as e:
        print(f"登录失败: {e}")
        print("请重新输入密码或者新的令牌登陆")
        raise typer.Exit(code=1)


def login_with_password(bayes_settings, default_env, username):
    password = typer.prompt(f"请输入 {username} 的密码", hide_input=True)
    try:
        gql_client = BayesGQLClient(default_env.graphQL, None)
        result = user_client.login(gql_client, username, password)
        bayes_settings.login(result.username, result.token)

        print(f"{result.username} 已成功登入 {default_env.name}")
    except Error as e:
        print(e.message)
        raise typer.Exit(code=1)


@app.command()
def logout(ctx: typer.Context):
    """
    注销

    用法:
        bayes logout [选项]

    可用选项:

      -h, --help   查看 logout 的帮助
    """
    bayes_settings = ctx.obj
    logout_result = bayes_settings.logout()
    if logout_result:
        print("已成功登出")
    else:
        print("登出失败")


@app.command()
def switch(ctx: typer.Context, name: str,
           endpoint: str = typer.Option(None, "--endpoint", "-e", help="填入 endpoint")):
    """
    切换服务端环境

    用法：
       bayes switch [配置名] [选项]

    可用选项：

      -e, --endpoint string   [可选] 填入 endpoint

      -h, --help              查看 switch 的帮助
    """

    if name == "default" and endpoint:
        print("配置名 default 已存在，且不能被修改，请选择其他配置名")
        raise typer.Exit(code=1)

    bayes_settings = ctx.obj

    if endpoint:
        # 临时创建一个新的环境，并判断是否可以访问
        new_env = BayesEnvConfig(name=name, endpoint=clean(endpoint))
        if not is_exist(new_env.graphQL):
            print(f"{endpoint} 无法访问，请再次确认你所输入的链接")
            raise typer.Exit(code=1)

        bayes_settings.add_new_env(name, new_env.endpoint)

    switch_result = bayes_settings.switch_default_env(name)
    if switch_result:
        print(f"已成功切换到 {name}")
    else:
        error = credential_notfound_error(name)
        print(error)


@app.command()
def status(ctx: typer.Context):
    """
    登录信息

    用法：
        bayes status [选项]

    可用选项：

        -h, --help   查看 status 的帮助
    """
    settings: BayesSettings = ctx.obj
    default_env: Optional[BayesEnvConfig] = settings.default_env
    userinfo = auth_usecase.get_default_credential_userinfo()
    if userinfo is not None:
        print(f"当前环境: {default_env.endpoint}")
        print(f"当前组织: {default_env.orgName}")
        print(f"用户名: {default_env.username}")
        print(f"邮箱: {userinfo.email}")
    else:
        print(f"当前环境: {default_env.endpoint}")
