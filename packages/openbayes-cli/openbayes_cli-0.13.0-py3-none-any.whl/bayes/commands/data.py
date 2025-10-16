import sys
from typing import Optional

import typer

from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.usercases import auth_usecase, dataset_list_usecase, dataset_usecase, open_usecase, minio_storage_usecase

app = typer.Typer()


@app.command()
def create(ctx: typer.Context,
           name: str,
           message: str = typer.Option(None, "-m", "--message", help="数据集描述信息"),
           open: bool = typer.Option(False, "-o", "--open", help="创建数据集成功后，在浏览器打开")):
    """
    创建一个新的数据集

    用法：
        bayes data create [数据集名字] [选项]

    可用选项：

        -h, --help             查看 create 的帮助

        -m, --message string   [可选] 数据集描述信息

        -o, --open             [可选] 创建数据集成功后，在浏览器打开
    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)
    # 检查现在是处于 组织/用户 状态
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    party_name = ""
    if auth_usecase.is_working_on_org():
        party_name = default_env.orgName
        print(f"当前正在组织 {party_name} 上进行操作...")
    else:
        party_name = default_env.username
        print(f"当前正在个人账号 {party_name} 上进行操作...")
    try:
        dataset = dataset_usecase.create(party_name, name, message)
    except Exception as e:
        print(f"e:{e}")
        print("创建失败")
        raise typer.Exit(code=1)

    print(f"数据集 {name} ({dataset.id}) 创建成功")

    frontend_url = dataset.get_link_value("frontend")
    print(f"打开网页 {frontend_url} 可查看数据集 {name} ({dataset.id}) 的详细信息")
    if open:
        open_usecase.open_browser(frontend_url)


@app.command()
def new_version(ctx: typer.Context,
                         dataset_id: str = typer.Argument(...)):
    """
    创建一个新的空的数据集版本

    用法：
        bayes data new-version [数据集编号] [选项]

    可用选项：

        -h, --help     查看帮助
    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)
    # 检查现在是处于 组织/用户 状态
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    party_name = ""
    if auth_usecase.is_working_on_org():
        party_name = default_env.orgName
        print(f"当前正在组织 {party_name} 上进行操作...")
    else:
        party_name = default_env.username
        print(f"当前正在个人账号 {party_name} 上进行操作...")

    try:
        dataset_version = dataset_usecase.create_empty_version(party_name, dataset_id)
    except Exception as e:
        # print(f"e:{e}")
        print("创建空数据集失败")
        raise typer.Exit(code=1)

    print(f"数据集 {dataset_version.id} 创建成功")


@app.command()
def upload(ctx: typer.Context,
          id: str,
          open: bool = typer.Option(False, "-o", "--open", help="上传数据集成功后，在浏览器打开"),
          path: str = typer.Option("", "-p", "--path", help="数据集文件或文件夹的本地路径，不填则使用当前目录"),
          directory: str = typer.Option("/", "-d", "--directory", help="数据集文件上传的指定路径，不填则默认使用根目录"),
          version: int = typer.Option(..., "-v", "--version", help="需要上传的数据集版本号")):
    """
    上传本地数据到数据集

    用法：
        bayes data upload [数据集编号] [选项]

    可用选项：

        -h, --help          查看 upload 的帮助

        -v, --version int     需要上传的数据集版本号

        -o, --open          [可选] 上传数据集成功后，在浏览器打开

        -p, --path string   [可选] 数据集文件或文件夹的本地路径，不填则使用当前目录

        -d, --directory string   [可选] 数据集文件上传的指定路径，不填则默认使用根目录


    """
    # 检查版本号是否有效
    if version <= 0:
        print(f"版本号必须是正整数")
        raise typer.Exit(code=1)

    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)
    # 检查现在是处于 组织/用户 状态
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    party_name = ""
    if auth_usecase.is_working_on_org():
        party_name = default_env.orgName
        print(f"当前正在组织 {party_name} 上进行操作...")
    else:
        party_name = default_env.username
        print(f"当前正在个人账号 {party_name} 上进行操作...")

    abs_dataset_path, error = dataset_usecase.get_absolute_path(path)
    if error is not None:
        print(f"路径 {path} 不存在")
        raise typer.Exit(code=1)

    file_info, error = dataset_usecase.stat_file(abs_dataset_path)
    if error is not None:
        print(f"路径 {abs_dataset_path} 不存在")
        raise typer.Exit(code=1)

    print(f"当前工作目录 {abs_dataset_path}")

    # 使用 boto3 minio upload
    minio_storage_usecase.upload(party_name, id, abs_dataset_path, version, directory)

    if open:
        dataset_usecase.open_dataset(id)


@app.command()
def ls(ctx: typer.Context,
       page: int = typer.Option(1, "-p", "--page", help="跳转页码"),
       user: str = typer.Option("", "-u", "--user", help="用户名")):
    """
    显示用户的数据集

    用法：
        bayes data ls [选项]

    可用选项：

        -h, --help          查看 ls 的帮助

        -p, --page string   [可选] 跳转页码

        -u, --user string   [可选] 用户名

    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)
    # 检查现在是处于 组织/用户 状态
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    party_name = ""
    if auth_usecase.is_working_on_org():
        party_name = default_env.orgName
        print(f"当前正在组织 {party_name} 上进行操作...")
    else:
        party_name = default_env.username
        print(f"当前正在个人账号 {party_name} 上进行操作...")

    if user == "":
        user = party_name
    datasets = dataset_list_usecase.list_datasets(user, page)
    dataset_list_usecase.list_datasets_display_table(datasets)


@app.command()
def versions(ctx: typer.Context, id: str):
    """
    显示用户的数据集的版本列表

    用法：
       bayes data versions [数据集编号] [选项]

    可用选项：

        -h, --help   查看 versions 的帮助
    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)
    # 检查现在是处于 组织/用户 状态
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    party_name = ""
    if auth_usecase.is_working_on_org():
        party_name = default_env.orgName
        print(f"当前正在组织 {party_name} 上进行操作...")
    else:
        party_name = default_env.username
        print(f"当前正在个人账号 {party_name} 上进行操作...")

    dataset_versions = dataset_list_usecase.list_dataset_versions(id)
    dataset_list_usecase.list_dataset_versions_display_table(dataset_versions)


@app.command()
def open(ctx: typer.Context, id: str):
    """
    在浏览器打开数据集页面
    
    用法：
        bayes data open [数据集编号] [选项]

    可用选项：

        -h, --help   查看 open 的帮助

    """
    # 检查用户是否已登录
    login = auth_usecase.check_login()
    if not login:
        print("尚未授权，请先登录")
        raise typer.Exit(code=1)
    # 检查现在是处于 组织/用户 状态
    bayes_settings = BayesSettings()
    default_env: Optional[BayesEnvConfig] = bayes_settings.default_env

    party_name = ""
    if auth_usecase.is_working_on_org():
        party_name = default_env.orgName
        print(f"当前正在组织 {party_name} 上进行操作...")
    else:
        party_name = default_env.username
        print(f"当前正在个人账号 {party_name} 上进行操作...")

    dataset_usecase.open_dataset(id)
