import os

import typer

from bayes.usercases import auth_usecase, ssh_usecase

app = typer.Typer()


@app.command()
def create(ctx: typer.Context):
    """
    创建新的 SSH key

    用法：
        bayes ssh create [选项]

    可用选项：

        -h, --help   查看 create 的帮助

    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)

    print("正在检查 SSH 公钥，请稍候...")

    isExist, err = ssh_usecase.is_finger_print_exist()
    if isExist:
        print("OpenBayes 服务器中已存在此设备的公钥")
        raise typer.Exit(code=1)

    print("OpenBayes 服务器中不存在关于此设备的公钥")

    # 直接使用空密码创建SSH key
    err = ssh_usecase.create_key("")
    if err is not None:
        raise typer.Exit(code=1)


@app.command()
def upload(ctx: typer.Context,
           pub_key_path: str,
           name: str = typer.Option("", "-n", "--name", help="SSH 名字，不填则默认使用 hostname")):
    """
    上传 SSH 公钥

    用法：
        bayes ssh upload [公钥] [选项]

    可用选项：

        -h, --help          查看 upload 的帮助

        -n, --name string   [可选] SSH 名字，不填则默认使用 hostname
    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)

    try:
        os.stat(pub_key_path)
    except FileNotFoundError:
        print(f"路径 {pub_key_path} 不存在")
        raise typer.Exit(code=1)

    err = ssh_usecase.upload_key(name, pub_key_path)
    if err is not None:
        raise typer.Exit(code=1)
