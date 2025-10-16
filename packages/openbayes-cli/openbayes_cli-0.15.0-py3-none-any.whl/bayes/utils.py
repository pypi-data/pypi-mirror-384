import base64
import datetime
import hashlib
import json
import logging
import os
import pathlib
import sys
import tempfile

import pytz
import toml

from bayes.model.file.settings import APP_NAME


class Utils:
    @staticmethod
    def byte_size(bytes: int, with_trim: bool) -> str:
        TB = 1024 ** 4
        GB = 1024 ** 3
        MB = 1024 ** 2
        KB = 1024
        B = 1

        unit = ""
        value = float(bytes)

        if bytes >= TB:
            unit = " TiB"
            value /= TB
        elif bytes >= GB:
            unit = " GiB"
            value /= GB
        elif bytes >= MB:
            unit = " MiB"
            value /= MB
        elif bytes >= KB:
            unit = " KiB"
            value /= KB
        elif bytes >= B:
            unit = " B"
        elif bytes == 0:
            return "0 B"

        result = f"{value:.2f}"
        if with_trim:
            result = result.rstrip('0').rstrip('.')

        return result + unit

    @staticmethod
    def date_from_now(t: datetime.datetime) -> str:
        now = datetime.datetime.now(tz=pytz.UTC)  # use UTC timezone
        duration = now - t
        year = 365.25 * 24 * 3600
        month = 30.44 * 24 * 3600
        day = 24 * 3600
        hour = 3600
        minute = 60
        second = 1

        if duration.total_seconds() // year > 0:
            return f"{int(duration.total_seconds() // year)}y"
        elif duration.total_seconds() // month > 0:
            return f"{int(duration.total_seconds() // month)}m"
        elif duration.total_seconds() // day > 0:
            return f"{int(duration.total_seconds() // day)}d"
        elif duration.total_seconds() // hour > 0:
            return f"{int(duration.total_seconds() // hour)}h"
        elif duration.total_seconds() // minute > 0:
            return f"{int(duration.total_seconds() // minute)}min"
        else:
            return f"{int(duration.total_seconds() // second)}sec"

    @staticmethod
    def format_quota_string(quota: int) -> str:
        if quota < 60:
            return f"{quota} 分钟"
        else:
            hours = quota // 60
            mins = quota % 60
            result = f"{hours} 小时"
            if mins > 0:
                result += f" {mins} 分钟"
            return result

    @staticmethod
    def generate_uid():
        id = os.urandom(16)
        return hashlib.sha256(id).hexdigest()

    @staticmethod
    def get_file_path(directory, filename):
        try:
            stat = os.stat(directory)
            stat_is_dir = os.path.isdir(directory)
        except OSError as err:
            logging.error(f"get_file_path error {err}")
            return ""

        if stat_is_dir:
            path = os.path.join(directory, filename)
        else:
            path = directory

        return path

    @staticmethod
    def generate_temp_zip_path():
        zip_name = Utils.generate_uid() + ".zip"
        prefix = os.path.join(tempfile.gettempdir(), APP_NAME)
        if not os.path.exists(prefix):
            os.makedirs(prefix, mode=0o755)
        return os.path.join(prefix, zip_name)

    @classmethod
    def base64_encode(cls, input):
        return base64.b64encode(input.encode()).decode()

    @staticmethod
    def is_empty_or_none(s):
        return s is None or s == ""

    @staticmethod
    def get_ssh_pub_key_path():
        ssh_path = get_ssh_path()
        return os.path.join(ssh_path, "openbayes.pub")

    @staticmethod
    def get_ssh_key_path():
        ssh_path = get_ssh_path()
        return os.path.join(ssh_path, "openbayes")

    @staticmethod
    def replace_last_id(url, new_id):
        last_slash_index = url.rindex('/')
        base_url = url[:last_slash_index + 1]
        return base_url + new_id

    @staticmethod
    def is_token_expired(token):
        try:
            payload_part = token.split(".")[1]
            padded_payload = payload_part + "=" * (4 - len(payload_part) % 4)
            decoded_payload = base64.urlsafe_b64decode(padded_payload).decode("utf-8")
            payload_data = json.loads(decoded_payload)

            exp = payload_data['exp']
            if exp is None:
                raise ValueError("Token does not contain expiration time.")

            # 将exp转换为datetime对象，使用UTC时区
            exp_datetime = datetime.datetime.utcfromtimestamp(exp)
            # 获取当前UTC时间
            now_datetime = datetime.datetime.utcnow()
            return now_datetime > exp_datetime
        except IndexError:
            print("Token 格式错误，无法解析 Payload")
            return None
        except (base64.binascii.Error, json.JSONDecodeError):
            print("Payload 解码失败")
            return None


def get_ssh_path() -> str:
    try:
        home = str(pathlib.Path.home())
    except Exception as e:
        print(f"Error getting home directory: {e}", file=sys.stderr)
        sys.exit(1)

    path = os.path.join(home, ".ssh")

    if not os.path.exists(path):
        try:
            os.makedirs(path, mode=0o755)
        except Exception as e:
            print(f"Error creating directory {path}: {e}", file=sys.stderr)
            sys.exit(1)

    return path
