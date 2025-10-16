# -*- coding: utf-8 -*-
"""
Created on Sun Jul 30 17:44:34 2023

@author: Administrator
"""

from elias import usual as u

logging = u.logger() 

def table_comment_read(table_name,hosts):
    '''
    

    Parameters
    ----------
    table_name : str
        数据源表名.
    hosts : dic
        数据源链接.

    Returns
    -------
    table_comment : TYPE
        DESCRIPTION.

    '''
    
    dbtype = hosts['dbtype']
    
    if dbtype == 'mysql':
        
        des_sql = f'''
        SELECT TABLE_COMMENT  as comment
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = '{hosts['db']}' 
        AND TABLE_NAME = '{table_name}'
        '''
        
        df = u.mysql_select(des_sql, hosts)
        table_comment = df['comment'][0]
    
    elif dbtype == 'clickhouse':
        
        des_sql = f'''
            SELECT name, engine, comment
            FROM system.tables
            WHERE database = '{hosts['db']}'
            AND name = '{table_name}';
        '''
        
        df = u.clickhouse_select(des_sql, hosts)
        table_comment = df['comment'][0]
    
    elif dbtype == 'maxcompute':
        from odps import ODPS
        access_id = hosts['access_id']
        access_key = hosts['access_key']
        project_name = hosts['project_name']
        endpoint = hosts['end_point']
        connection = ODPS(access_id, access_key, project_name, endpoint)
        # connection = ODPS(access_id = hosts['access_id'],access_key = hosts['access_key'], project = hosts['project_name'], endpoint = hosts['end_point'])
        table_obj = connection.get_table(f"{project_name}.{table_name}")
        # 获取表级别的注释
        table_comment = table_obj.comment
        
    return table_comment



def schema_read(table_name,hosts):
    '''
    

    Parameters
    ----------
    table_name : str
        需要读取schema的源表名.
    hosts : TYPE
        需要读取的源链接.

    Returns
    -------
    df : DataFrame
        读取的schema.

    '''
    try:
        dbtype = hosts['dbtype']
        if dbtype=='':
            logging.error("数据库类型未配置：dbtype==''")
            # raise SystemExit("数据库类型未配置，终止运行")
        logging.info(f"数据库类型：{dbtype}")
    except Exception as e:
        logging.error(f"数据库类型未配置：{e}")
        # raise e
        
    
    logging.info(f"开始链接 {dbtype}，读取`{table_name}`schema数据")
    if dbtype == 'mysql':
        
        describe_sql = f'''
        SELECT 
        -- TABLE_NAME, 
           COLUMN_NAME,
           DATA_TYPE,
        -- COLUMN_TYPE,
           COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{hosts['db']}' AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        '''
        
        df = u.mysql_select(describe_sql, hosts)
        df_final = df[['COLUMN_NAME','DATA_TYPE','COLUMN_COMMENT']]
        
    
    elif dbtype == 'clickhouse':
        
        describe_sql = f'''
        DESCRIBE TABLE {hosts['db']}.{table_name};
        '''
        
        df = u.clickhouse_select(describe_sql, hosts)
        df_final = df[['name','type','comment']]
        
    
    elif dbtype == 'maxcompute':
        from odps import ODPS
        access_id = hosts['access_id']
        access_key = hosts['access_key']
        project_name = hosts['project_name']
        endpoint = hosts['end_point']
        connection = ODPS(access_id, access_key, project_name, endpoint)
        # connection = ODPS(access_id = hosts['access_id'],access_key = hosts['access_key'], project = hosts['project_name'], endpoint = hosts['end_point'])
        table_obj = connection.get_table(f"{project_name}.{table_name}")
        column_info = [(column.name, column.type.name,column.comment) for column in table_obj.table_schema.columns]
        
        import pandas as pd
        df_final = pd.DataFrame(column_info)
    
    else:
        raise ValueError("Unsupported target database type.")
        
        
    df_final.columns = ['col_name','col_type','col_comment']
    df_final['db_type']=dbtype
    
    logging.info(f"df_schema\n\n{df_final}\n")
    logging.info("schema数据读取完成")
    
    return df_final
        
def compare_string_to_list(input_string, input_list):
    for item in input_list:
        if input_string == item or input_string in item or item in input_string:
            return True
    return False

def schema_transfer(df):
    '''
    

    Parameters
    ----------
    df : DataFrame
        数据源表 的 Schema.

    Returns
    -------
    df : TYPE
        DESCRIPTION.

    '''
    string_list = ['char', 'time', 'date','bool','string','varchar','timestamp','datetime']
    int_list = ['int','bigint','int64','int32']
    float_list = ['decimal', 'float', 'double','float32','float64']
    
    df['col_type_name']=None
    
    logging.info("开始读取 DataFrame 字符类型，并转换schema数据")
    for i in range(len(df)):
        if compare_string_to_list(df['col_type'][i].lower(), string_list):
            df['col_type_name'][i] = "string"
        
        elif compare_string_to_list(df['col_type'][i].lower(), int_list):
            df['col_type_name'][i] = "int"
        
        elif compare_string_to_list(df['col_type'][i].lower(), float_list):
            df['col_type_name'][i] = "float"
        
        else:
            df['col_type_name'][i] = "text"   
    logging.info("Schema数据转换完成")
    return df

        

def schema_add_updated(df):
    import pandas as pd
    if "updated" not in df['col_name']:
        new_record = {
            "col_name":"updated",
            "col_type":None,
            "col_comment":"更新时间",
            "db_type":df['db_type'][0],
            "col_type_name":"string"
            }
        new_df = pd.DataFrame(new_record, index=[0])
        final_df = pd.concat([df,new_df], ignore_index=True)
    else:
        pass
    return final_df
    

def schema_map(df,target_db_type='mysql'):
    '''
    

    Parameters
    ----------
    df : DataFrame
        数据源表 的 Schema.
    target_db_type : TYPE, optional(mysql,clickhouse,maxcompute)
        目标表的数据库类型. The default is 'mysql'.

    Returns
    -------
    df : TYPE
        DESCRIPTION.

    '''
    df['col_type_map']=None
    
    schema_dic = {
        'mysql':{
            'string':'varchar(255)',
            'int':'bigint',
            'float':'double',
            'text':'longtext'
            },
        'clickhouse':{
            'string':'String',
            'int':'Int64',
            'float':'Float32',
            'text':'String'
            },
        'maxcompute':{
            'string':'string',
            'int':'bigint',
            'float':'double',
            'text':'string'
            }
        }
    
    
    for i in range(len(df)):
        
        df['col_type_map'][i]=schema_dic[target_db_type][df['col_type_name'][i]]
    
    return df



def create_sql(df,table_comment,table_name,hosts):
    '''
    

    Parameters
    ----------
    df : DataFrame
        数据源表 的 Schema.
    table_comment : str
        数据源表 的 表注释.
    table_name : str
        目标表的表名.
    hosts : dic
        目标表的数据库链接.

    Returns
    -------
    None.

    '''
    # from elias.Scripts import py_clickhouse as c
    
    target_db_type = hosts['dbtype']
    # target_db = hosts['db']
    
    if target_db_type == 'mysql':
        target_db = hosts['db']
        schema_list = [f"`{df['col_name'][i]}` {df['col_type_map'][i]} COMMENT '{df['col_comment'][i]}'" for i in range(len(df))]
        schema_str =  ',\n    '.join(schema_list)
        create_table_sql = f"CREATE TABLE  `{target_db}`.`{table_name}` (\n    {schema_str}\n)\nCOMMENT='{table_comment}'"

        logging.info(f"{target_db_type}目标表建表语句，已生成")
        return create_table_sql
            
    elif target_db_type == 'clickhouse':
        target_db = hosts['db']
        first_col_name = df['col_name'][0]
        schema_list = [f"`{df['col_name'][i]}` {df['col_type_map'][i]} COMMENT '{df['col_comment'][i]}'" for i in range(len(df))]
        schema_str =  ',\n    '.join(schema_list)
        create_table_sql = f"CREATE TABLE  `{target_db}`.`{table_name}`  on cluster default  (\n    {schema_str}\n)\n ENGINE = ReplicatedMergeTree() \nORDER BY (`{first_col_name}`) \nCOMMENT '{table_comment}'"
        
        logging.info(f"{target_db_type}目标表建表语句，已生成")
        return create_table_sql
            
    elif target_db_type == 'maxcompute':
        first_col_name = df['col_name'][0]
        schema_list = [f"`{df['col_name'][i]}` {df['col_type_map'][i]} COMMENT '{df['col_comment'][i]}'" for i in range(len(df))]
        schema_str =  ',\n    '.join(schema_list)
        create_table_sql = f"CREATE TABLE  `{table_name}` (\n    {schema_str}\n)\nCOMMENT '{table_comment}'"
        
        logging.info(f"{target_db_type}目标表建表语句，已生成")
        return create_table_sql
            
    
    else:
        raise ValueError("Unsupported target database type.")

# hosts = target_hosts
# table_name = target_table_name
def create_table(df,table_comment,table_name,hosts):
    '''
    

    Parameters
    ----------
    df : DataFrame
        数据源表 的 Schema.
    table_comment : str
        数据源表 的 表注释.
    table_name : str
        目标表的表名.
    hosts : dic
        目标表的数据库链接.

    Returns
    -------
    None.

    '''
    # from elias.Scripts import py_clickhouse as c
    
    target_db_type = hosts['dbtype']
    # target_db = hosts['db']
    
    if target_db_type == 'mysql':
        target_db = hosts['db']
        schema_list = [f"`{df['col_name'][i]}` {df['col_type_map'][i]} COMMENT '{df['col_comment'][i]}'" for i in range(len(df))]
        schema_str =  ',\n    '.join(schema_list)
        create_table_sql = f"CREATE TABLE  `{target_db}`.`{table_name}` (\n    {schema_str}\n)\nCOMMENT='{table_comment}'"
        try:
            u.mysql_ddl(create_table_sql,hosts)
            logging.info(f"{target_db_type}目标表建表完成")
        except Exception as e:
            logging.error(f"{target_db_type}目标表建表失败：{e}")
            logging.error(f"create_table_sql：\n{create_table_sql}")
            
    elif target_db_type == 'clickhouse':
        target_db = hosts['db']
        first_col_name = df['col_name'][0]
        schema_list = [f"`{df['col_name'][i]}` {df['col_type_map'][i]} COMMENT '{df['col_comment'][i]}'" for i in range(len(df))]
        schema_str =  ',\n    '.join(schema_list)
        create_table_sql = f"CREATE TABLE  `{target_db}`.`{table_name}`  on cluster default  (\n    {schema_str}\n)\n ENGINE = ReplicatedMergeTree() \nORDER BY (`{first_col_name}`) \nCOMMENT '{table_comment}'"
        try:
            u.clickhouse_ddl(create_table_sql,hosts)
            logging.info(f"{target_db_type}目标表建表完成")
        except Exception as e:
            logging.error(f"{target_db_type}目标表建表失败：{e}")
            logging.error(f"create_table_sql：\n{create_table_sql}")
            
    elif target_db_type == 'maxcompute':
        first_col_name = df['col_name'][0]
        schema_list = [f"`{df['col_name'][i]}` {df['col_type_map'][i]} COMMENT '{df['col_comment'][i]}'" for i in range(len(df))]
        schema_str =  ',\n    '.join(schema_list)
        create_table_sql = f"CREATE TABLE  `{table_name}` (\n    {schema_str}\n)\nCOMMENT '{table_comment}'"
        try:
            u.mc_ddl(create_table_sql,hosts)
            logging.info(f"{target_db_type}目标表建表完成")
        except Exception as e:
            logging.error(f"{target_db_type}目标表建表失败：{e}")
            logging.error(f"create_table_sql：\n{create_table_sql}")
            
    
    else:
        raise ValueError("Unsupported target database type.")





# ---------------------------------------------------------------------------------- 
   
def auto_schema(origin_table_name,origin_hosts,target_table_name,target_hosts,updated = True):
    
            
    try:
        df = schema_read(origin_table_name,origin_hosts)   
    except Exception as e:
        logging.error(f"schema_read未知错误：{e}")
        raise e
    
    try:
        df = schema_transfer(df) 
    except Exception as e:
        logging.error(f"schema_transfer未知错误：{e}")
        raise e
    
    if updated == True:
        try:
            df = schema_add_updated(df)
        except Exception as e:
            logging.error(f"\nschema_add_updated未知错误：{e}\n")
            raise e
    else:
        pass
        
    try:  
        df = schema_map(df,target_db_type=target_hosts['dbtype'])
    except Exception as e:
        logging.error(f"schema_map未知错误：{e}")
        raise e
    
    return df





# ---------------------------------------------------------------------------------- 
   
def auto_create(origin_table_name,origin_hosts,target_table_name,target_hosts,updated = True):
    
    
        
    try:  
        table_comment = table_comment_read(origin_table_name,origin_hosts)
        logging.info("\n table_comment_read : success\n")
    except Exception as e:
        logging.error(f"\n table_comment_read 未知错误：{e}\n")
        raise e
        
    try:
        df = schema_read(origin_table_name,origin_hosts)  
        logging.info("\n schema_read : success\n") 
    except Exception as e:
        logging.error(f"\n schema_read 未知错误：{e}\n")
        raise e
    
    try:
        df = schema_transfer(df) 
        logging.info("\n schema_transfer : success\n")
    except Exception as e:
        logging.error(f"\n schema_transfer 未知错误：{e}\n")
        raise e
    
    if updated == True:
        try:
            df = schema_add_updated(df)
            logging.info("\n schema_add_updated : success\n")
        except Exception as e:
            logging.error(f"\n schema_add_updated 未知错误：{e}\n")
            raise e
    else:
        logging.warning("\n pass schema_add_updated : pass\n")
        pass
    
    
    
    try:  
        df = schema_map(df,target_db_type=target_hosts['dbtype'])
        logging.info("\n schema_map : success\n")
    except Exception as e:
        logging.error(f"\n schema_map 未知错误：{e}\n")
        raise e

    try: 
        create_table(df,table_comment,target_table_name,target_hosts)
        logging.info("\n create_table : success\n")
    except Exception as e:
        logging.error(f"\n create_table未知错误：{e}\n")
        raise e


# ==================================================================================
if __name__ == "__main__":
    
    from elias import usual as u 
    
    origin_table_name = 'om_t_shop'
    
    origin_hosts = u.all_hosts('om')
    # origin_hosts = u.all_hosts('ch_bi_report')
    # origin_hosts = u.all_hosts('mc')
    
    target_table_name = 'your_table_name7'
    
    # target_hosts = u.all_hosts('om')
    # target_hosts = u.all_hosts('ch_bi_report')
    target_hosts = u.all_hosts('mc')
    
    auto_create(origin_table_name,origin_hosts,target_table_name,target_hosts)
