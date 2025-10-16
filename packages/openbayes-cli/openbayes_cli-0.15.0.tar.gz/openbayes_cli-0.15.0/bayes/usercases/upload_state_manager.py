import json
import os
import hashlib
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any
import time


class UploadStateManager:
    """管理文件上传状态，支持断点续传"""

    def __init__(self, state_dir=None):
        """初始化上传状态管理器

        Args:
            state_dir: 状态文件存储目录，默认为用户主目录下的 .bayes/upload_states
        """
        if state_dir is None:
            # 默认在用户主目录下创建 .bayes/upload_states 目录
            state_dir = os.path.join(str(Path.home()), '.bayes', 'upload_states')

        # 确保状态目录存在
        os.makedirs(state_dir, exist_ok=True)
        self.state_dir = state_dir
        self.lock = threading.Lock()

    def _get_state_file_path(self, file_path: str, bucket: str, key: str) -> str:
        """获取状态文件路径"""
        # 使用文件路径、桶名和键的组合生成唯一的状态文件名
        file_id = hashlib.md5(f"{file_path}:{bucket}:{key}".encode()).hexdigest()
        return os.path.join(self.state_dir, f"{file_id}.json")

    def save_state(self, file_path: str, bucket: str, key: str,
                   upload_id: str, parts: List[Dict[str, Any]]) -> None:
        """保存上传状态

        Args:
            file_path: 本地文件路径
            bucket: MinIO桶名
            key: 对象键名
            upload_id: 分块上传ID
            parts: 已上传的分块信息列表
        """
        state_file = self._get_state_file_path(file_path, bucket, key)
        state = {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'file_mtime': os.path.getmtime(file_path),
            'bucket': bucket,
            'key': key,
            'upload_id': upload_id,
            'parts': parts,
            'updated_at': time.time()
        }

        with self.lock:
            with open(state_file, 'w') as f:
                json.dump(state, f)

    def get_state(self, file_path: str, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """获取上传状态

        Args:
            file_path: 本地文件路径
            bucket: MinIO桶名
            key: 对象键名

        Returns:
            如果存在有效的上传状态，返回状态字典，否则返回None
        """
        state_file = self._get_state_file_path(file_path, bucket, key)

        if not os.path.exists(state_file):
            return None

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            # 验证状态有效性
            if (os.path.getsize(file_path) != state.get('file_size') or
                    os.path.getmtime(file_path) != state.get('file_mtime')):
                print(f"文件已被修改，无法恢复上传状态: {file_path}")
                self.clear_state(file_path, bucket, key)
                return None

            return state
        except Exception as e:
            print(f"读取上传状态出错: {e}")
            return None

    def clear_state(self, file_path: str, bucket: str, key: str) -> None:
        """清除上传状态

        Args:
            file_path: 本地文件路径
            bucket: MinIO桶名
            key: 对象键名
        """
        state_file = self._get_state_file_path(file_path, bucket, key)

        with self.lock:
            if os.path.exists(state_file):
                os.remove(state_file)