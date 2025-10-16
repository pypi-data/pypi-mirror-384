from typing import Tuple

from pydantic import BaseModel
import os
import hashlib
from datetime import datetime


class BayesFile(BaseModel):
    Path: str
    Name: str
    Size: int
    MD5: str

    @classmethod
    def new_file_info_from_file_path(cls, path: str) -> Tuple['BayesFile', Exception]:
        if not os.path.exists(path):
            raise FileNotFoundError("The specified path does not exist")

        if not os.path.isfile(path):
            raise Exception("The provided path is a directory, not a file")

        try:
            stat = os.stat(path)
            content = f"{path}{os.path.basename(path)}{stat.st_size}{datetime.fromtimestamp(stat.st_mtime)}"
            hash_md5 = hashlib.md5(content.encode('utf-8')).hexdigest()

            bayes_file = cls(
                Path=path,
                Name=os.path.basename(path),
                Size=stat.st_size,
                MD5=hash_md5
            )
            # print(f"from_path bayes_file:{bayes_file}")

            return bayes_file, None
        except Exception as e:
            raise Exception(f"An error occurred while processing the file: {e}")


