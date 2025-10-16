# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 11:52:38 2023

@author: Elias.Liu
"""
from elias import usual as u
logger = u.logger()



def maxcompute_writer(target_table_name,target_hosts = u.all_hosts('mc')):
    from elias.datax import auto_create_table as act 
    df_schema = act.schema_read(target_table_name, target_hosts)
    dic = {
        "writer": {
            "name": "odpswriter",
            "parameter": {
                "accessId": target_hosts['access_id'],
                "accessKey": target_hosts['access_key'],
                "project": target_hosts['project_name'],
                "table": target_table_name,
                "column": list(df_schema['col_name']),
                "odpsServer": target_hosts['end_point'],
                "truncate": True
                }
            }
        }
    return dic


def mysql_writer(target_table_name,target_hosts = u.all_hosts('bi_data_warehouse')):
    from elias.datax import auto_create_table as act 
    df_schema = act.schema_read(target_table_name, target_hosts)
    dic = {
        "writer": {
            "name": "mysqlwriter",
            "parameter": {
                "writeMode": "replace",
                "username": target_hosts['user'],
                "password": target_hosts['code'],
                "preSql": [
                    f"truncate table `{target_hosts['db']}`.`{target_table_name}`"
                ],
                "column": list(df_schema['col_name']),
                "connection": [{
                    "jdbcUrl": f"jdbc:mysql://{target_hosts['host']}:{target_hosts['port']}/{target_hosts['db']}?useSSL=false&verifyServerCertificate=false",
                    "table": [target_table_name]

                    }]
                }
            }
        }
    return dic


def clickhouse_writer(target_table_name,target_hosts = u.all_hosts('bi_data_warehouse')):
    from elias.datax import auto_create_table as act 
    df_schema = act.schema_read(target_table_name, target_hosts)
    dic = {
            "writer": {
                "name": "clickhousewriter",
                "parameter": {
                    "batchByteSize": 134217728,
                    "batchSize": 65536,
                    "column": list(df_schema['col_name']),
                    "preSql": [f"truncate table `{target_hosts['db']}`.`{target_table_name}` "],
                    "connection": [
                        {
                            "jdbcUrl": f"jdbc:clickhouse://{target_hosts['host']}:{target_hosts['port']}/{target_hosts['db']}",
                            "table": [target_table_name]
                        }
                    ],
                    "password": target_hosts['code'],
                    "username": target_hosts['user'],
                    "writeMode": "insert"
                }
            }
        }
    return dic






def writer(target_table_name,target_hosts = u.all_hosts('bi_data_warehouse')):
    
    
    if target_hosts['dbtype'] == 'maxcompute':
        dic = maxcompute_writer(target_table_name,target_hosts)
        return dic
    
    elif target_hosts['dbtype'] == 'mysql':
        dic = mysql_writer(target_table_name,target_hosts)
        return dic
    
    elif target_hosts['dbtype'] == 'clickhouse':
        dic = clickhouse_writer(target_table_name,target_hosts)
        return dic
        
    else:
        raise ValueError("Unsupported writer database type.")
        
        
        
        
        
        