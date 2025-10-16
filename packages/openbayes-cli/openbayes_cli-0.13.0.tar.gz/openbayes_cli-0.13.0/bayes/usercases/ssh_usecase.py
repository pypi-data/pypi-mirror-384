import os
import socket
import subprocess
from typing import Tuple, Optional

from bayes.client import ssh_client
from bayes.client.base import BayesGQLClient
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.utils import Utils


def finger_print(pub_key_path):
    cmd = ["ssh-keygen", "-E", "md5", "-lf", pub_key_path]

    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        stdout = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(cmd)}' returned non-zero exit status {e.returncode}.")
        print(f"Error output: {e.stderr.strip()}")
        return "", e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "", e

    return stdout, None


def is_finger_print_exist() -> Tuple[bool, Exception]:
    pub_key = Utils.get_ssh_pub_key_path()
    
    # Check if the public key file exists first
    if not os.path.exists(pub_key):
        return False, None
    
    fingerprint, err = finger_print(pub_key)
    if err is not None:
        return False, err

    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    try:
        keys = ssh_client.get_keys(gql_client, default_env.username)
        if keys is None:
            return False, ValueError("No SSH keys returned from server")
            
        for key in keys:
            if fingerprint in key.fingerprint:
                return True, None
    except Exception as e:
        return False, e

    return False, None


def keygen(path: str, passphrase: str):
    try:
        result = subprocess.run(
            ["ssh-keygen", "-N", passphrase, "-f", path],
            check=True,
            text=True,
            capture_output=True
        )
        return None
    except subprocess.CalledProcessError as e:
        print("Error occurred during ssh-keygen:", e.stderr)
        return e


def upload_key(name, path) -> Exception:
    print("正在上传 SSH 公钥，请稍候...")

    if name == "":
        try:
            hostname = socket.gethostname()
            name = hostname
        except Exception as e:
            print("Error occurred while getting the hostname:", e)
            return e

    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    try:
        with open(path, 'r') as file:
            content = file.read()
            ssh_client.create_key(gql_client, default_env.username, name, str(content))
    except FileNotFoundError as e:
        print(f"Error: {path} does not exist.")
        return e
    except IOError as e:
        print(f"Error occurred while reading the file: {e}")
        return e

    print("上传成功")
    return None


def create_key(passphrase):
    print("正在创建 SSH key，请稍候...")
    private_key = Utils.get_ssh_key_path()
    pub_key = Utils.get_ssh_pub_key_path()

    # Check if files exist before removing them
    if os.path.exists(private_key):
        os.remove(private_key)
    if os.path.exists(pub_key):
        os.remove(pub_key)

    ssh_dir = os.path.dirname(private_key)
    os.makedirs(ssh_dir, exist_ok=True, mode=0o700)  # Secure permissions

    err = keygen(private_key, passphrase)
    if err is not None:
        return err

    print("创建成功")

    return upload_key("", pub_key)
    

    