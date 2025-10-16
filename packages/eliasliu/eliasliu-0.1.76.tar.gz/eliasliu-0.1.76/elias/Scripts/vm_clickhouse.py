# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 13:53:24 2023

clickhouse - 创建mysql代理表，在从代理表创建实体表

每次更新清空实体表，从代理表查询数据并往实体表插入。

该脚本实现全流程自动化，仅需输入5个参数 源表名和链接信息 & 目标表名（代理&实体）和链接信息

origin_table_name, origin_hosts,vm_table_name, target_table_name, target_hosts

@author: Administrator
"""



# from elias.Scripts import py_clickhouse as c 
from elias import usual as u 
from elias.datax import auto_create_table as act
import time

logger = u.logger(file = None) 
# =============================================================================
# 1 代理表
# 1.1 删除代理表
def df_vm_drop(vm_table_name,target_hosts):
    vm_drop_sql = f'''
    DROP TABLE `{target_hosts['db']}`.`{vm_table_name}` ON CLUSTER default;
    '''
    df_vm_drop = u.clickhouse_ddl(vm_drop_sql,target_hosts)
    return df_vm_drop


# 1.2 创建代理表
def engine_proxy_mysql(table_name,hosts = u.all_hosts('bi_data_warehouse')):
    # engine = f'''MySQL('rm-uf698x9pde1ytqxe890130.mysql.rds.aliyuncs.com:3306', '{hosts['db']}','{table_name}', '{hosts['user']}', '{hosts['code']}')'''
    engine = f'''MySQL('{hosts['proxy_host']}:{hosts['port']}', '{hosts['db']}','{table_name}', '{hosts['user']}', '{hosts['code']}')'''
    return engine

# vm_table_comment = table_comment
def df_vm_create(origin_table_name,origin_hosts,vm_table_name,target_hosts):
    
    # 获取字段结构与表注释
    df_schema = act.auto_schema(origin_table_name, origin_hosts, vm_table_name, target_hosts,updated=False)
    vm_table_comment = act.table_comment_read(origin_table_name,origin_hosts)
    
    
    engine = engine_proxy_mysql(origin_table_name,origin_hosts)
    target_db = target_hosts['db']
    schema_list = [f"`{df_schema['col_name'][i]}` {df_schema['col_type_map'][i]} COMMENT '{df_schema['col_comment'][i]}'" for i in range(len(df_schema))]
    schema_str =  ',\n    '.join(schema_list)
    vm_create_sql = f'''
CREATE TABLE  `{target_db}`.`{vm_table_name}`  on cluster default  
(\n    {schema_str}\n) 
ENGINE = {engine}
COMMENT '{vm_table_comment}'
    '''
    
    logger.info(f"目标表建表语句，已生成\n{vm_create_sql}")
    df_vm_create = u.clickhouse_ddl(vm_create_sql,target_hosts)
    logger.info("目标表建表语句，已成功")
    return df_vm_create
    


# =============================================================================
# 2 实体表
# 2.1 删除实体表
def df_drop(target_table_name,target_hosts):
    drop_sql = f'''
    DROP TABLE `{target_hosts['db']}`.`{target_table_name}` ON CLUSTER default;
    '''

    df_drop = u.clickhouse_ddl(drop_sql,target_hosts)
    return df_drop

 
# 2.2 创建实体表
def df_create(vm_table_name,target_table_name,target_hosts):
    
    # 获取字段结构与表注释
    df_schema = act.auto_schema(vm_table_name, target_hosts, target_table_name, target_hosts,updated = False)
    table_comment = act.table_comment_read(vm_table_name,target_hosts)
    
    target_db = target_hosts['db']
    first_col_name = df_schema['col_name'][0]
    schema_list = [f"`{df_schema['col_name'][i]}` {df_schema['col_type_map'][i]} COMMENT '{df_schema['col_comment'][i]}'" for i in range(len(df_schema))]
    schema_str =  ',\n    '.join(schema_list)
    create_sql = f'''
        CREATE TABLE  `{target_db}`.`{target_table_name}`  on cluster default  
        (\n    {schema_str},
        `updatetime` String  COMMENT 'clickhouse中更新时间'
         )  
        ENGINE = ReplicatedMergeTree() 
        ORDER BY (`{first_col_name}`) 
        COMMENT '{table_comment}'
    '''
    
    logger.info(f"目标表建表语句，已生成\n{create_sql}")
    df_create = u.clickhouse_ddl(create_sql,target_hosts)
    logger.info("目标表建表，已成功")
    return df_create



    
# 2.3 清空实体表
def df_truncate(target_table_name,target_hosts):
    truncate_sql = f'''
    TRUNCATE table `{target_hosts['db']}`.`{target_table_name}`;
    '''
    df_truncate = u.clickhouse_ddl(truncate_sql,target_hosts)
    return df_truncate

    

# 2.4 插入实体表
def df_insert(vm_table_name,target_table_name,target_hosts,updated = False):
    
    # 获取字段结构与表注释
    df_schema = act.auto_schema(vm_table_name, target_hosts, target_table_name, target_hosts,updated)
    # table_comment = act.table_comment_read(vm_table_name,target_hosts)
    
    col_name_list = list(df_schema['col_name'])
    str_schema = ',\n    '.join([f'`{col_name}`'for col_name in col_name_list] )
    
    insert_sql = f'''
    INSERT INTO `{target_hosts['db']}`.`{target_table_name}`
    SELECT
        {str_schema},
    	cast(toDateTime(now(),'Asia/Shanghai') as String) as updatetime 
    FROM `{target_hosts['db']}`.`{vm_table_name}`;
    '''
    
    logger.info(f"目标表插入语句，已生成\n{insert_sql}")
    logger.info("开始插入数据……")
    df_insert = u.clickhouse_ddl(insert_sql,target_hosts)
    logger.info("数据插入完成……")
    return df_insert   
    
# -------------------------------------------------------------------

def table_check(vm_table_name,target_hosts):
    sql = f'''show tables from `{target_hosts['db']}`'''
    df = u.clickhouse_select(sql,target_hosts)
    df.columns = ['name']
    df_list = list(df['name'])
    if vm_table_name in df_list:
        return True
    else:
        return False

# target_schema_check = schema_check(vm_table_name, target_hosts, target_table_name, target_hosts)
def schema_check(origin_table_name, origin_hosts, target_table_name, target_hosts):
    try:
        origin_df_schema = act.schema_transfer(act.schema_read(origin_table_name,origin_hosts))[['col_name','col_type_name','col_comment']]
        target_df_schema = act.schema_transfer(act.schema_read(target_table_name,target_hosts))[['col_name','col_type_name','col_comment']]
        
        origin_df_schema = origin_df_schema[origin_df_schema['col_name']!='updatetime']
        target_df_schema = target_df_schema[target_df_schema['col_name']!='updatetime']
        
        for i in range(len(origin_df_schema)):
            origin_df_schema['col_type_name'][i] = origin_df_schema['col_type_name'][i].replace('text','string')
        for i in range(len(target_df_schema)):
            target_df_schema['col_type_name'][i] = target_df_schema['col_type_name'][i].replace('text','string')
        
        logger.info(f'origin_df_schema:\n{origin_df_schema}')
        logger.info(f'target_df_schema:\n{target_df_schema}')
        logger.info(f'\n{origin_df_schema==target_df_schema}')
        
        origin_list_ = [(origin_df_schema['col_name'][i],origin_df_schema['col_type_name'][i].replace('text','string'),origin_df_schema['col_comment'][i]) for i in range(len(origin_df_schema))]
        target_list = [(target_df_schema['col_name'][i],target_df_schema['col_type_name'][i].replace('text','string'),target_df_schema['col_comment'][i]) for i in range(len(target_df_schema))]
        
        logger.info(origin_list_== target_list)
        if origin_list_== target_list:
            return True
        else:
            return False
    except:
        return False


# ======================================================================================
def auto_proxy_table(origin_table_name, origin_hosts,vm_table_name, target_table_name, target_hosts):
    
    # from elias.datax import auto_create_table as act 
    # import time
    
    # 获取字段结构与表注释
    # df_schema = act.auto_schema(origin_table_name, origin_hosts, target_table_name, target_hosts)
    # table_comment = act.table_comment_read(origin_table_name,origin_hosts)
    
    # 验证表是否存在
    logger.info("开始进行表存在验证……")
    logger.info("代理表验证……")
    vm_table_check = table_check(vm_table_name,target_hosts)
    logger.info(f"vm_table_check：{vm_table_check}")
    logger.info("实体表验证……")
    target_table_check = table_check(target_table_name,target_hosts)
    logger.info(f"target_table_check：{target_table_check}")
    logger.info("表存在验证结束")
    
    # # 如果表存在，则跳过；不存在，就建表
    # # 代理表验证
    # if vm_table_check==True:
    #     pass
    # else:
    #     df_vm_create(df_schema,table_comment,vm_table_name,target_hosts)
    
    
    # # 实体表验证
    # if target_table_check==True:
    #     pass
    # else:
    #     df_create(df_schema,table_comment,target_table_name,target_hosts)
        
    # 验证表结构是否一致
    logger.info("开始进行表结构验证……")
    logger.info("代理表验证……")
    vm_schema_check = schema_check(origin_table_name, origin_hosts, vm_table_name, target_hosts)
    
    logger.info(f''' \n
                     Table & Schema Check Result
                -------------------------------------
                | vm_table_check        | {str(vm_table_check).replace('True','True ')}     |
                -------------------------------------
                | vm_schema_check       | {str(vm_schema_check).replace('True','True ')}     |
                -------------------------------------

                \n''')
    
    
    
    
    
    # 如果表结构一致，则清空表、插入；如果表结构不一致，则删除表，并重建，然后插入
    # 代理表验证
    if vm_table_check==True and vm_schema_check==True:
        logger.info("代理表验证：通过 （表存在并且表结构一致）")
        pass
    else:
        logger.warning("代理表验证：不通过 （表不存在或表结构不一致）")
        logger.info("开始删除代理表……")
        try:
            df_drop(vm_table_name,target_hosts)
            logger.info("代理表删除操作成功 ！尝试创建代理表…… ")
        except:
            logger.warning("实体表不存在 ！尝试创建代理表…… ")
            is_drop = 0
            while is_drop==0:
                try:
                    logger.info("开始创建代理表……")
                    df_vm_create(origin_table_name,origin_hosts,vm_table_name,target_hosts)
                    logger.info("代理表创建成功 ！ ")
                    is_drop = 1
                except:
                    logger.warning("代理表副本删除还在删除中，代理表创建失败 ！480秒后进行重试 ")
                    time.sleep(480)
    
    
    logger.info(f"vm_schema_check：{vm_schema_check}")
    logger.info("实体表验证……")
    target_schema_check = schema_check(vm_table_name, target_hosts, target_table_name, target_hosts)
    logger.info(f"target_schema_check：{target_schema_check}")
    logger.info("表结构验证结束")
    
    logger.info(f''' \n
                     Table & Schema Check Result
                -------------------------------------
                | target_table_check    | {str(target_table_check).replace('True','True ')}     |
                -------------------------------------
                | target_schema_check   | {str(target_schema_check).replace('True','True ')}     |
                -------------------------------------
                \n''')
    
    # logger.info(f''' \n
    #                  Table & Schema Check Result
    #             -------------------------------------
    #             | vm_table_check        | {str(vm_table_check).replace('True','True ')}     |
    #             -------------------------------------
    #             | vm_schema_check       | {str(vm_schema_check).replace('True','True ')}     |
    #             -------------------------------------
    #             | target_table_check    | {str(target_table_check).replace('True','True ')}     |
    #             -------------------------------------
    #             | target_schema_check   | {str(target_schema_check).replace('True','True ')}     |
    #             -------------------------------------
    #             \n''')
    
    
    
    # 实体表验证
    if target_table_check==True and target_schema_check==True:
        logger.info("实体表验证：通过 （表存在并且表结构一致）")
        pass
    else:
        logger.warning("实体表验证：不通过 （表不存在或表结构不一致）")
        try:
            df_drop(target_table_name,target_hosts)
            logger.info("实体表删除操作成功 ！尝试创建实体表…… ")
        except:
            logger.warning("实体表不存在 ！尝试创建实体表…… ")
            
        is_drop = 0
        while is_drop==0:
            try:
                logger.info("开始创建实体表……")
                df_create(vm_table_name,target_table_name,target_hosts)
                # df_create(df_schema,table_comment,target_table_name,target_hosts)
                logger.info("实体表创建成功 ！ ")
                is_drop = 1
            except:
                logger.warning("实体表副本删除还在删除中，代理表创建失败 ！480秒后进行重试 ")
                time.sleep(480)
    
    # 清空表数据
    logger.info("开始清空实体表……")
    df_truncate(target_table_name,target_hosts)
    logger.info("实体表清空完成 ！")
    
    
    # 插入表数据
    logger.info("开始插入实体表……")
    df_insert(vm_table_name,target_table_name,target_hosts,updated = False)
    logger.info("实体表插入完成 ！")
    

def demo():    
    # ======================================================================================
    # from elias.datax import auto_create_table as act
    from elias import usual as u
    
    # ======================================================================================
    
    origin_table_name = 'assets_dwd_all_allowance_journal_d_f'
    vm_table_name = 'assets_dwd_all_allowance_journal_d_f'
    
    target_table_name = 'ch_assets_dwd_all_allowance_journal_d_f'
    
    # -------------------------------------------------------------------
    origin_hosts = u.all_hosts('bi_data_warehouse')
    # origin_hosts = u.all_hosts('ch_bi_report')
    # origin_hosts = u.all_hosts('mc')
    
    # -------------------------------------------------------------------
    
    # target_hosts = u.all_hosts('om')
    target_hosts = u.all_hosts('ch_bi_report')
    # target_hosts = u.all_hosts('mc')
    
    auto_proxy_table(origin_table_name, origin_hosts,vm_table_name, target_table_name, target_hosts)



def auto_clickhouse(origin_table_name,origin_hosts,target_hosts):    
    # ======================================================================================

    vm_table_name = origin_table_name
    
    target_table_name = f'ch_{vm_table_name}'
    
    auto_proxy_table(origin_table_name, origin_hosts,vm_table_name, target_table_name, target_hosts)
    
    
    
    
    
    
    
    