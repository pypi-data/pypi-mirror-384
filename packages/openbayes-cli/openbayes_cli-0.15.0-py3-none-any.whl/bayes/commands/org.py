from typing import Optional

import typer

from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.usercases import org_usecase
from bayes.usercases import auth_usecase


app = typer.Typer()


@app.command()
def switch(name: str, ctx: typer.Context):
    """
    组织切换

    用法：
        bayes org switch [组织名] [选项]

    可用选项：

        -h, --help   查看 switch 的帮助

    """
    # 先检查登陆状态
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)

    # 检查用户是否尝试切换回用户模式（组织名称是否与用户名相同，忽略大小写）
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env
    switch_back_to_user = str.lower(name) == str.lower(default_env.username)

    # 如果不是切换回用户模式，则检查组织是否存在。如果组织不存在，打印相应的错误信息并退出程序
    if not switch_back_to_user:
        # 看这个用户下是否有这个组织(这个地方涉及到一个权限的问题，管理员能在命令行切换到其他人的组织吗？)
        if not org_usecase.user_contains_org(default_env.username, name):
            print("请输入当前登录用户下正确的组织名称")
            raise typer.Exit(code=1)
        # 切换到指定的组织
        result = bayes_settings.switch_org(name)
        if result:
            print(f"已成功切换到组织 {name}")
            raise typer.Exit()
    else:
        result = bayes_settings.switch_user(name)
        if result:
            print(f"已成功切换到个人账号 {name}")


@app.command()
def status(ctx: typer.Context):
    """
    组织信息

    用法：
        bayes org status [选项]

    可用选项：

       -h, --help   查看 status 的帮助
    """
    bayes_settings = ctx.obj
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    userinfo = auth_usecase.get_default_credential_userinfo()
    if userinfo is not None:
        print(f"当前环境: {default_env.endpoint}")
        print(f"当前组织: {default_env.orgName}")
        print(f"用户名: {default_env.username}")
        print(f"邮箱: {userinfo.email}")
    else:
        print(f"当前环境: {default_env.endpoint}")


@app.command()
def ls(ctx: typer.Context):
    """
    查看所属组织

    用法：
        bayes org ls [选项]

    可用选项：

        -h, --help   查看 ls 的帮助
    """
    # 先检查登陆状态
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)

    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    user_orgs_data = org_usecase.list_user_orgs(default_env.username)
    org_usecase.list_display_table(user_orgs_data)
