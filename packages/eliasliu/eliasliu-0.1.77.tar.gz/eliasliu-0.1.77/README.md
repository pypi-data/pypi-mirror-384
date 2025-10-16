0 安装
找到终端，再终端内输入以下代码
安装
pip install elias
更新
pip install elias --upgrade

1 数据库相关
1.1 mysql
1.1.1 查询
输入：sql；hosts
输出：DataFrame（pandas DataFrame 后文简称 df）
from elias import usual as u
# mysql查询
df = u.mysql_select('show tables', hosts=u.all_hosts('test'))

1.1.2 写入
输入：df；tablename；hosts；update（在表内新增一个字段用于记录更新时间）
输出：None —— 实体表
（对应hosts里，会有一张叫tablename的实体表，内容是df）
from elias import usual as u
# mysql写入
u.mysql_write(df,'table_name',update = True, hosts=u.all_hosts('test'))

1.1.3 DDL

from elias import usual as u
u.mysql_ddl(sql,hosts)

1.1.4 加索引
from elias import usual as u
u.mysql_add_index(column,table,hosts)


1.1.5 加字段注释
from elias import usual as u
u.mysql_column_comment(table = 'dim_month',column = 'month_name',comment = '',hosts={},column_type = None)

1.2 clickhouse

1.2.1 查询
from elias import usual as u
df = u.clickhouse_select(sql,hosts)

1.2.2 写入 (测试中)
from elias.Scripts import py_clickhouse as c
# clickhouse 写入
c.ch_write(df,table_name = 'test_table',comment = 'test',hosts_write= u.all_hosts(name = 'ch_bi_report'),update = True)

1.2.3 DDL
from elias import usual as u
u.clickhouse_ddl(sql,hosts)

1.2.4 同步表（mysql --> clickhouse）
将其他mysql数据源的table，同步进clickhouse。
from elias import usual as u
from elias.Scripts import vm_clickhouse as vc

vc.auto_clickhouse(
                    origin_table_name = 'assets_ads_snd_receivable_amount_history_d_i',
                    origin_hosts= u.all_hosts('bi_data_warehouse'),
                    target_hosts = u.all_hosts('ch_bi_report')
                   )

1.3 Maxcompute
1.3.1 查询

from elias import usual as u
df = u.mc_select(sql,hosts)


1.3.2 DDL
from elias import usual as u
u.mc_ddl(sql,hosts)

2 Datax相关

2.1 自动建表
from elias.datax import auto_create_table as act
from elias import usual as u

origin_table_name = 'om_t_shop'
origin_hosts = u.all_hosts('om')
target_table_name = 'your_table_name7'
target_hosts = u.all_hosts('mc')

act.auto_create(origin_table_name,origin_hosts,target_table_name,target_hosts,updated = True)
2.2 生成json

from elias.datax import main
main.run({origin_table_name,origin_hosts,target_table_name,target_hosts})

2.2 同步数据
2.2.1 方法1
import os
from elias import usual as u
from elias import config_env_variable as ev
logger = u.logger()
config_path = ev.environ_get()
config = ev.elias_config()

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
        "targetname":'mc2',
        "targettable":'test_all_journal0'
        }
# 建表
file_path = main.run(data)

# 同步
u.run_cmd_os(rf"python {run_path} {file_path}")

2.2.2 方法2
import os
from elias import usual as u
from elias import config_env_variable as ev
logger = u.logger()
config_path = ev.environ_get()
config = ev.elias_config()

# =============================================================================
# 获取路径

# # 获取当前文件的路径
current_file_path = os.path.abspath("__file__")

# # 获取当前文件所在的目录
current_directory = os.path.dirname(current_file_path)
logger.info(f"当前文件的目录路径：{current_directory}")

# # 获取main.py所在的目录
main_path = os.path.join(current_directory,"main.py")
logger.info("main.py的绝对路径是：{}".format(main_path))


# # 获取DataX的路径
run_path = os.path.join(config.datax_path,r"bin\datax.py")
job_path = os.path.join(config.datax_path,r"job")


# =============================================================================
# 方法2
sourcename='financial_data'
sourcetable='rpa_ali_journal_data'
targetname='mc2'
targettable='test_all_journal7'


u.run_cmd_os('chcp 65001')

# 建表
u.run_cmd_os(rf"python {main_path} -s {sourcename} -st {sourcetable} -t {targetname} -tt {targettable}")


# 同步
from elias.datax import job
target_hosts = u.all_hosts(name = targetname)
file_name = job.get_filename(targettable, target_hosts)
u.run_cmd_os(rf"python {run_path} {job_path}\{file_name}")

3 其他
3.1 导入本地文件
from elias import config_env_variable as ev
oar = ev.file_import(file_path,'oar')
oar.main()
（导入本地任务）
from elias import config_env_variable as ev
import os

# 读取环境变量
env_value = ev.environ_get(env_variable_name = "elias_config")

# 指定文件路径
file_path = os.path.join(env_value,r'bi_data_warehouse\mission_assets\ch_assets_dws_order_receivable_amount_d_f.py')


# 导入包
oar = ev.file_import(file_path,'oar2')

# 调用方法
oar.main()

3.2 翻译
from elias import usual as u
chinese_input = '谢谢'
english_output = u.translate_chinese_to_english(chinese_input)
print("英文翻译：", english_output)



3.3 