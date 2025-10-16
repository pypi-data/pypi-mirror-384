# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 11:43:50 2023

@author: Elias.Liu
"""
from elias import usual as u
logger = u.logger()


def replace_element_in_list(my_list, origin="updated",target="now()"):
    """
    将列表中的某个元素替换为指定的新元素。

    参数：
    my_list: list
        要修改的列表。
    target: any
        要替换的目标元素。
    updated: any
        要替换成的新元素。

    返回：
    无返回值。原列表会被直接修改。
    """
    for i in range(len(my_list)):
        if my_list[i] == origin:
            my_list[i] = target
            break
        
        
        
        

def maxcompute_reader(origin_table_name,origin_hosts = u.all_hosts('bi_data_warehouse'),split = '',where = ""):
    from elias.datax import auto_create_table as act 
    df_schema = act.schema_read(origin_table_name, origin_hosts)
    
    # 增加更新时间
    list_schema = list(df_schema['col_name'])
    if "updated" not in list_schema:
        list_schema.append("now()")
    else:
        replace_element_in_list(list_schema,"updated","now()")
        
    # json reader正文
    dic = {
        "reader": {
            "name": "odpsreader",
            "parameter": {
                "accessId": origin_hosts['access_id'],
                "accessKey": origin_hosts['access_key'],
                "project": origin_hosts['project_name'],
                "table": origin_table_name,
                "column": list_schema,
                # "where":where,
                # "splitPk": split,
                "odpsServer": origin_hosts['end_point']
                }
            }
        }
    if split == "" or split == None:
        pass
    else:
        dic['reader']['parameter']["splitPk"] = split
        
        
    if where == "" or where == None:
        pass
    else:
        dic['reader']['parameter']["where"] = where
    return dic


def mysql_reader(origin_table_name,origin_hosts = u.all_hosts('bi_data_warehouse'),split = '',where = ""):
    from elias.datax import auto_create_table as act 
    df_schema = act.schema_read(origin_table_name, origin_hosts)
    
    # 增加更新时间
    list_schema = list(df_schema['col_name'])
    if "updated" not in list_schema:
        list_schema.append("now()")
    else:
        replace_element_in_list(list_schema,"updated","now()")
    
    # json reader正文
    dic = {
        "reader": {
            "name": "mysqlreader",
            "parameter": {
                "username": origin_hosts['user'],
                "password": origin_hosts['code'],
                "column": list_schema,
                # "where":where,
                # "splitPk": split,
                "connection": [{
                    "table": [origin_table_name],
                    "jdbcUrl": [
                        f"jdbc:mysql://{origin_hosts['host']}:{origin_hosts['port']}/{origin_hosts['db']}"]
                    }]
                }
            }
        }
    if split == "" or split == None:
        pass
    else:
        dic['reader']['parameter']["splitPk"] = split
        
        
    if where == "" or where == None:
        pass
    else:
        dic['reader']['parameter']["where"] = where
    return dic


def clickhouse_reader(origin_table_name,origin_hosts = u.all_hosts('bi_data_warehouse'),split = "",where = ""):
    from elias.datax import auto_create_table as act 
    df_schema = act.schema_read(origin_table_name, origin_hosts)
    
    # 增加更新时间
    list_schema = list(df_schema['col_name'])
    if "updated" not in list_schema:
        list_schema.append("now()")
    else:
        replace_element_in_list(list_schema,"updated","now()")
    
    # json reader正文
    dic = {
        "reader": {
            "name": "clickhousereader",
            "parameter": {
                "username": origin_hosts['user'],
                "password": origin_hosts['code'],
                "column": list_schema,
                # "splitPk": split,
                # "where":where,
                "connection": [{
                    "table": [origin_table_name],
                    "jdbcUrl": [
                        f"jdbc:clickhouse://{origin_hosts['host']}:{origin_hosts['port']}/{origin_hosts['db']}"]
                    }]
                }
            }
        }
    if split == "" or split == None:
        pass
    else:
        dic['reader']['parameter']["splitPk"] = split
        
        
    if where == "" or where == None:
        pass
    else:
        dic['reader']['parameter']["where"] = where
        
    return dic






def reader(origin_table_name,origin_hosts = u.all_hosts('bi_data_warehouse'),split = "",where = ""):
    
    
    if origin_hosts['dbtype'] == 'maxcompute':
        dic = maxcompute_reader(origin_table_name,origin_hosts,split,where)
        return dic
    
    elif origin_hosts['dbtype'] == 'mysql':
        dic = mysql_reader(origin_table_name,origin_hosts,split,where)
        return dic
    
    elif origin_hosts['dbtype'] == 'clickhouse':
        dic = clickhouse_reader(origin_table_name,origin_hosts,split,where)
        return dic
        
    else:
        raise ValueError("Unsupported reader database type.")
        
        
        
        
        
        