# bayes/utils/__init__.py
# 此文件使 utils 目录成为 Python 包

import os
import sys
import importlib.util

# 直接从 bayes/utils.py 加载 Utils 类
utils_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils.py")
spec = importlib.util.spec_from_file_location("utils_module", utils_file)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

# 导出 Utils 类
Utils = utils_module.Utils
get_ssh_path = utils_module.get_ssh_path

# 导出 add_no_upgrade_option 函数
from .add_global_param import add_no_upgrade_option 