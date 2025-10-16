import os
import queue
import sys
import threading
import time
from typing import Optional, Tuple

import typer
import requests
from urllib.parse import quote

from bayes.client import gear_client
from bayes.client.base import BayesGQLClient
from bayes.client.gear_client import DownloadInfoPayload
from bayes.model.file.settings import BayesSettings
from bayes.usercases import archive_usecase
from bayes.utils import Utils
from bayes.usercases import auth_usecase

# 定义要忽略的系统文件模式
IGNORE_PATTERNS = {
        # Windows系统文件
        'Thumbs.db',
        'desktop.ini',
        '~$',           # Office临时文件前缀
        
        # macOS系统文件
        '.DS_Store',
        '._',           # 以._开头的文件
        '.Spotlight-',
        '.Trashes',
        '.fseventsd',
        
        # Linux系统文件（一般以.开头）
        '.directory',
        '.Trash'
    }   

def is_folder_empty(target):
    if not os.path.exists(target):
        return True
    
    # 获取目录中的所有文件
    files = os.listdir(target)
    
    # 过滤系统文件
    non_system_files = []
    system_files = []
    
    for file in files:
        is_system_file = False
        # 检查文件是否匹配任何忽略模式
        for pattern in IGNORE_PATTERNS:
            if file.startswith(pattern) or file == pattern:
                system_files.append(file)
                is_system_file = True
                break
        
        if not is_system_file:
            non_system_files.append(file)
    
    # 打印调试信息
    if files:
        if system_files:
            print(f"目录中的系统文件: {system_files}")
        if non_system_files:
            print(f"目录中包含非系统文件，删除后才能进行解压在此目录")
        elif not non_system_files:
            print(f"目录中只包含系统文件，将被视为空目录")
    
    # 只检查非系统文件
    return len(non_system_files) == 0


def get_target_file_name(target, job_id, party_name, download_from):
    # 获取任务信息以获取任务名称
    default_env = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    
    job, _ = gear_client.get_job_info_by_id(gql_client, job_id, party_name)
    if job is None:
        print(f"未找到任务 {job_id}")
        raise typer.Exit(code=1)
    
    # 根据是否为根目录确定文件名
    if download_from == "/" or not download_from:
        # 根目录: 使用任务名称(替换斜杠为连字符)作为文件名
        job_name = job.name if job.name else job_id
        filename = job_name.replace("/", "-") + ".output.zip"
    else:
        # 子目录: 使用路径的最后一个元素作为文件名
        # 确保删除末尾的斜杠(如果有)
        path_parts = download_from.rstrip("/").split("/")
        # 获取最后一个元素
        dir_name = path_parts[-1]
        filename = dir_name + ".output.zip"
    
    # 返回完整路径
    return os.path.join(target, filename)


def is_file_exist(filename):
    if os.path.exists(filename):
        return True
    else:
        return False


def is_continuing(filename: str) -> bool:
    is_continuing = typer.prompt(f"{filename} 已存在在目标路径中，是否需要覆盖？ [y/N]")
    if not is_continuing:
        print("Operation cancelled by the user.")
        sys.exit(1)
    if is_continuing.lower() in ("y", "yes"):
        return True
    return False


def rename_zip(zip_name, filename):
    is_exist, err = archive_usecase.is_file_exist(zip_name, filename)
    if is_exist and err is None:
        new_file_name = zip_name.replace(".zip", "_" + Utils.generate_uid() + ".zip")
        os.rename(zip_name, new_file_name)
        return new_file_name
    return zip_name


def unzip(source, target):
    try:
        # 确保源文件存在
        if not os.path.exists(source):
            return Exception(f"源文件不存在: {source}")
            
        # 解压文件
        err = archive_usecase.unzip(source, target)
        if err:
            return err
            
        print(f"解压成功: 文件已解压到 {target}")  
        
        # 确保文件解压成功后再删除
        try:
            os.remove(source)
            print(f"已删除源文件: {source}")
        except PermissionError:
            return Exception(f"没有权限删除文件: {source}")
        except OSError as e:
            if e.errno == 13:  # Permission denied
                return Exception(f"文件被占用，无法删除: {source}")
            else:
                return Exception(f"删除文件时出错: {e}")
                
        return None
    except Exception as e:
        print(f"解压或删除文件时出错: {e}")
        return e


def download(target, party_name, job_id, download_from) -> Tuple[Optional[str], Optional[Exception]]:
    default_env = BayesSettings().default_env
    url = f"{default_env.endpoint}/api/users/{party_name}/jobs/{job_id}/output/all"
    
    
    # 添加key参数（如果不是根目录）
    if download_from and download_from != "/":
        url += f"?key={download_from}"
    
    auth_token = default_env.token
    
    # 获取目标文件名
    filename = get_target_file_name(target, job_id, party_name, download_from)
    
    # 创建队列用于线程通信
    is_finished = queue.Queue()
    
    print("正在下载中，请稍候")
    
    # 定义显示下载进度的函数
    def download_process():
        is_done = False
        while not is_done:
            if not is_finished.empty():
                result = is_finished.get()
                if isinstance(result, tuple):
                    is_done, err = result
                else:
                    raise TypeError("Queue item is not a tuple")
                
                if is_done:
                    print(f"\r下载完成，文件保存在 {filename}")
                else:
                    print(f"\r下载失败: {err}")
                print()
                break
            else:
                try:
                    file_stat = os.stat(filename)
                    size = Utils.byte_size(file_stat.st_size, False)
                    print(f"\r已下载 {size}", end="")
                except FileNotFoundError:
                    pass
                time.sleep(1)
    
    # 启动显示进度的线程
    download_thread = threading.Thread(target=download_process)
    download_thread.start()
    
    # 执行下载
    try:
        # 发送GET请求，流式处理响应
        response = requests.get(
            url, 
            headers={"Authorization": f"Bearer {auth_token}"}, 
            stream=True
        )
        
        # 检查响应状态码
        if response.status_code != 200:
            error_msg = f"下载请求失败: 状态码 {response.status_code}"
            if response.content:
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_msg += f" - {error_json['message']}"
                except:
                    error_msg += f" - {response.text}"
            
            is_finished.put((False, error_msg))
            return None, error_msg
        
        # 将响应内容写入文件
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # 下载成功
        is_finished.put((True, None))
        return filename, None
        
    except requests.RequestException as e:
        error_msg = f"下载请求异常: {e}"
        print(error_msg)
        is_finished.put((False, error_msg))
        return None, e
    except Exception as e:
        error_msg = f"下载过程中出现未知错误: {e}"
        print(error_msg)
        is_finished.put((False, error_msg))
        return None, e
