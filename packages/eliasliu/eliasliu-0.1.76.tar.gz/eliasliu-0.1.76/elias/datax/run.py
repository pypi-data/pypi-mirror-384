# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 19:18:54 2023

@author: Administrator
"""

import os
from elias import usual as u
from elias import config_env_variable as ev
config_path = ev.environ_get()
config = ev.elias_config()
# =============================================================================

logger = u.logger()

# =============================================================================
# 获取路径

# 获取当前文件的路径
current_file_path = os.path.abspath("__file__")

# 获取当前文件所在的目录
current_directory = os.path.dirname(current_file_path)
logger.info(f"当前文件的目录路径：{current_directory}")

# 获取main.py所在的目录
main_path = os.path.join(current_directory,"main.py")
logger.info("main.py的绝对路径是：{}".format(main_path))


# 获取DataX的路径
run_path = os.path.join(config.datax_path,r"bin\datax.py")
job_path = os.path.join(config.datax_path,r"job")


# =============================================================================
# 方法1

from elias.datax import main

data = {
        "sourcename":'financial_data',
        "sourcetable":'rpa_ali_journal_data',
        "targetname":'mc',
        "targettable":'test_all_journal0'
        }
# 建表
file_path = main.run(data)

# 同步
u.run_cmd_os(rf"python {run_path} file_path")

# =============================================================================
# 方法2
u.run_cmd_os('chcp 65001')

# 建表
u.run_cmd_os(rf"python {main_path} -s financial_data -st rpa_ali_journal_data -t mc -tt test_all_journal0")


# 同步
u.run_cmd_os(rf"python {run_path} {job_path}\【maxcompute】prj_yingshou_20230629.test_all_journal0.json")