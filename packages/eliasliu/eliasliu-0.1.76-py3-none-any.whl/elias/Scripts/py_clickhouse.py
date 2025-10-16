# -*- coding: utf-8 -*-
"""
Created on Sun Apr  9 10:29:29 2023

@author: nlsm
"""

#------------------------------------------------------------------------------
from elias import usual as u
from elias import wechat as w
# import pandas as pd

# df = df3
# df_colums = df.columns





# hosts_read= u.all_hosts(name = 'ch_bi_report')
# hosts_write= u.all_hosts(name = 'ch_bi_report')
# db = hosts_write['db']

# table_name = 'test_table'


def get_create_sql_ch(df,table_name = 'test_table',comment='',hosts_write= u.all_hosts(name = 'ch_bi_report'),engine = ''):
    
    df_colums = df.columns
    column_dtype = ''
    
    for i in range(len(df_colums)):
        if df[df_colums[i]].dtypes=='int64' or df[df_colums[i]].dtypes=='int32' :
            column_dtype = column_dtype+f'`{df_colums[i]}` Int'
        
        elif df[df_colums[i]].dtypes=='float64':
            column_dtype = column_dtype+f'`{df_colums[i]}` Float'
        
        elif df[df_colums[i]].dtypes=='datetime64' or df[df_colums[i]].dtypes=='datetime' or df[df_colums[i]].dtypes=='date':
            column_dtype = column_dtype+f'`{df_colums[i]}` Datetime'
        
        else:
            column_dtype = column_dtype+f'`{df_colums[i]}` String'
        
        if i < len(df_colums)-1:
            column_dtype = column_dtype+',\n'
        else:
            pass
    
    # print(column_dtype)
    if engine == '':
        engine = f'MergeTree  ORDER BY `{df_colums[0]}`'
    elif engine == 'Memory':
        engine = 'Memory'
    elif engine == 'ReplicatedMergeTree':
        engine = f'ReplicatedMergeTree  ORDER BY `{df_colums[0]}`'
    elif engine == 'MergeTree':
        engine = f'MergeTree  ORDER BY `{df_colums[0]}`'
    
    
    create_sql = f'''
CREATE TABLE IF NOT EXISTS `{hosts_write['db']}`.`{table_name}`
(
{column_dtype}
 ) 
ENGINE = {engine}
comment '{comment}';
    '''
    
    # print(create_sql)
    return create_sql




def get_insert_sql_ch(df,table_name = 'test_table',hosts_write= u.all_hosts(name = 'ch_bi_report')):
    
    df_colums = df.columns
    
    insert_values = ''
    for index, row in df.iterrows():
        # print(index,row)
        
        row_value = ''
        for i in range(len(df_colums)):
            r = row[df_colums[i]]
            
            
            if df[df_colums[i]][index] == None:
                row_value = row_value + 'NULL'
            elif df[df_colums[i]].dtypes=='int64' or df[df_colums[i]].dtypes=='int32' :
                row_value = row_value + f"{r}"
            elif df[df_colums[i]].dtypes=='float64':
                row_value = row_value + f"{r}"
            else:
                row_value = row_value + f"'{r}'"
                         
            if i < len(df_colums)-1:
                row_value = row_value+','
            else:
                pass
        
        insert_values += f" ({row_value})"
        # print(row_value)
        
        if index < len(df)-1:
            insert_values += ",\n"
        else:
            pass
    # print(insert_values)    
    
    
    insert_sql = f'''
INSERT INTO `{hosts_write['db']}`.`{table_name}` FORMAT Values
{insert_values};
    '''.replace('%','%%')
    # .replace(':','\:')
    
    # print(insert_sql) 
    return insert_sql


def get_table_backup_name(table_name):
    from elias import usual as u
    backup_table_name = table_name+f'_backup_{u.Datetime_now(t=1)}'
    return backup_table_name


def get_altername_sql_ch(table_name = 'test_table',new_table_name = 'new_test_table',hosts_write= u.all_hosts(name = 'ch_bi_report')):
    altername_sql = f'''RENAME TABLE `{hosts_write['db']}`.`{table_name}` TO `{hosts_write['db']}`.`{new_table_name}`'''
    return altername_sql

def get_drop_sql_ch(table_name = 'test_table',hosts_write= u.all_hosts(name = 'ch_bi_report')):
    
    drop_sql = f'''DROP TABLE  `{hosts_write['db']}`.`{table_name}`'''
    return drop_sql



# def clickhouse_ddl(sql = 'SHOW TABLES',hosts = u.all_hosts(name = 'ch_bi_report')):
#     from clickhouse_sqlalchemy import make_session
#     from sqlalchemy import create_engine
#     import pandas as pd
    
#     conf = {
#         "user": hosts['name'],
#         "password": hosts['code'],
#         "server_host": hosts['host'],
#         "port": hosts['port'],
#         "db": hosts['db']
#     }
    
#     # connection = 'clickhouse://{user}:{password}@{server_host}:{port}/{db}'.format(**conf)
#     connection = 'clickhouse://{user}:{password}@{server_host}:{port}/{db}?socket_timeout=600000'.format(**conf)
#     engine = create_engine(connection, pool_size=100, pool_recycle=3600, pool_timeout=20)
    
#     # sql = 'SHOW TABLES'
    
#     session = make_session(engine)
#     cursor = session.execute(sql)
#     try:
#         fields = cursor._metadata.keys
#         df = pd.DataFrame([dict(zip(fields, item)) for item in cursor.fetchall()])
#     finally:
#         cursor.close()
#         session.close()
#     return df

def clickhouse_ddl(sql = 'SHOW TABLES',hosts = u.all_hosts(name = 'ch_bi_report')): # 能良om正式环境
    from clickhouse_driver import Client
    
    host=hosts['host']
    database=hosts['db']
    user=hosts['user']
    password=hosts['code']
    
    # 创建一个客户端
    if user =='':
        # 无密码连接的客户端
        client = Client(host)
    else:
        # 有密码连接的客户端
        client = Client(host=host, database=database, user=user, password=password)
    # client = Client(ip)

    # 执行查询
    # result = client.execute('show tables')
    # df = client.query_dataframe(sql)
    r = client.execute(sql)
    import pandas as pd
    df = pd.DataFrame(r)
    # client.disconnect()
    return df

def result_verify(table_name = 'test_table',hosts = u.all_hosts(name = 'ch_bi_report')):
    verify_sql = f'''select count(*) as num from `{hosts['db']}`.`{table_name}`'''
    df_verify = clickhouse_ddl(sql = verify_sql,hosts = hosts)
    r = df_verify['num'][0]
    return r



# def db_write():
#     hosts = u.all_hosts(name = 'bi_report')
#     db_sql = f'''
# CREATE DATABASE IF NOT EXISTS `bi_test` 
# ENGINE = MySQL('{hosts['host']}  :   {hosts['port']} ', ['{hosts['db']}' | 你的数据库名称], '{hosts['name']}', '{hosts['code']}')
#     '''
#     clickhouse_ddl(db_sql,hosts)
#     print(db_sql)



def ch_write(df,table_name = 'test_table',comment = 'test',hosts_write= u.all_hosts(name = 'ch_bi_report'),update = True):
    import pandas as pd
    import datetime

    if update == True:
        now = datetime.datetime.now().strftime('%F %T')
        df['updated'] = [now for i in range(len(df))]


    # hosts_write= u.all_hosts(name = 'ch_bi_report')
    # table_name = 'test_table'
    backup_table_name = get_table_backup_name(table_name)
    
    create_sql = get_create_sql_ch(df,table_name = table_name,comment = comment,hosts_write = hosts_write)
    insert_sql= get_insert_sql_ch(df,table_name = table_name,hosts_write = hosts_write)
    altername_sql = get_altername_sql_ch(table_name = table_name,new_table_name = backup_table_name,hosts_write = hosts_write)
    
    df_tables = u.clickhouse_select(sql = 'SHOW TABLES',hosts = hosts_write)
    if table_name in list(df_tables['name']):
        clickhouse_ddl(altername_sql,hosts_write)
    else:
        pass
    
    ee = ''
    try:
        df_create = clickhouse_ddl(create_sql,hosts_write)
    except Exception as e:
        print(e)
        ee = ee+'建表失败'+'\n'
    
    
    try:
        df_insert = clickhouse_ddl(insert_sql,hosts_write)
    except Exception as e:
        print(e)
        ee = ee+'数据写入失败'+'\n'
        
    if ee=='':
        try:
            drop_sql = get_drop_sql_ch(table_name = backup_table_name,hosts_write = hosts_write)
            clickhouse_ddl(drop_sql,hosts_write)
        except:
            pass
    else:
        
        # 便于debug
        insert_sql_list = []
        for i in range(len(df)):
            df2 = df.iloc[i:i+1]
            insert_sql= get_insert_sql_ch(df2,table_name = table_name,hosts_write = hosts_write)
            try:
                df_insert = clickhouse_ddl(insert_sql,hosts_write)
                result = 'success'
            except Exception as e:
                print(e)
                print(i,'数据写入失败\n\n')
                ee = ee+str(i)+'数据写入失败'+'\n'
                result = 'fail'
            insert_sql_list.append([i,insert_sql,result])
            
    
        import pandas as pd
        df_insert_sql = pd.DataFrame(insert_sql_list)
        df_insert_sql.columns = ['id','insert_sql','result']
        df_insert_sql_fail = df_insert_sql[df_insert_sql['result']=='fail']
        
        print(f'失败：{len(df_insert_sql_fail)}')
        
        from elias import wechat as w
        u.df_send_file(df_insert_sql_fail
                        ,fname = f'【写入失败{len(df_insert_sql_fail)}条记录】_{u.today()}_df_insert_sql_fail'
                        ,key = w.robots('nl_file_output')
                        )
        
        # 数据回滚
        drop_sql = get_drop_sql_ch(table_name = table_name,hosts_write = hosts_write)
        clickhouse_ddl(drop_sql,hosts_write)
        return_sql = get_altername_sql_ch(table_name = backup_table_name,new_table_name = table_name,hosts_write = hosts_write)
        clickhouse_ddl(return_sql,hosts_write)
        print(f'{table_name}，数据写入失败，回滚成功')
    
    print(f'{table_name}，数据写入成功')
    result_sql = f'\n-----------\ncreate_sql:\n{create_sql}\n\n-----------\ninsert_sql:\n{insert_sql}\n\n-----------\naltername_sql:\n{altername_sql}\n\n'
    
    return result_sql
        

# table_name = name
def ch_write_row(df,table_name = 'test_table',comment = 'test',hosts_write= u.all_hosts(name = 'ch_bi_report'),update = True):
    import pandas as pd
    import datetime

    if update == True:
        now = datetime.datetime.now().strftime('%F %T')
        df['updated'] = [now for i in range(len(df))]
    

    # hosts_write= u.all_hosts(name = 'ch_bi_report')
    # table_name = 'test_table'
    backup_table_name = get_table_backup_name(table_name)
    
    create_sql = get_create_sql_ch(df,table_name = table_name,comment = comment,hosts_write = hosts_write)
    altername_sql = get_altername_sql_ch(table_name = table_name,new_table_name = backup_table_name,hosts_write = hosts_write)
    
    df_tables = u.clickhouse_select(sql = 'SHOW TABLES',hosts = hosts_write)
    if table_name in list(df_tables['name']):
        clickhouse_ddl(altername_sql,hosts_write)
    else:
        pass
    
    ee = ''
    try:
        df_create = clickhouse_ddl(create_sql,hosts_write)
    except Exception as e:
        print(e)
        ee = ee+'建`表失败'+'\n'
    
        
    len_rows = len(df)
    s_rows = 0
    f_rows = 0
    for rows in range(len(df)):
        print(rows)
        df_row = df[rows:rows+1]
        
        insert_sql= get_insert_sql_ch(df,table_name = table_name,hosts_write = hosts_write)
        
        
        try:
            df_insert = clickhouse_ddl(insert_sql)
            s_rows = s_rows+1
        except Exception as e:
            print(e)
            ee = ee+'数据写入失败'+'\n'
            f_rows = f_rows+1
        
    # if ee=='':
    #     drop_sql = get_drop_sql_ch(table_name = backup_table_name,hosts_write = hosts_write)
    #     clickhouse_ddl(drop_sql)
    #     pass
    # else:
        
    #     # 便于debug
    #     insert_sql_list = []
    #     for i in range(len(df)):
    #         df2 = df.iloc[i:i+1]
    #         insert_sql= get_insert_sql_ch(df2,table_name = table_name,hosts_write = hosts_write)
    #         try:
    #             df_insert = clickhouse_ddl(insert_sql)
    #             result = 'success'
    #         except Exception as e:
    #             print(e)
    #             print(i,'数据写入失败\n\n')
    #             ee = ee+str(i)+'数据写入失败'+'\n'
    #             result = 'fail'
    #         insert_sql_list.append([i,insert_sql,result])
            
    
    # import pandas as pd
    # df_insert_sql = pd.DataFrame(insert_sql_list)
    # df_insert_sql.columns = ['id','insert_sql','result']
    # df_insert_sql_fail = df_insert_sql[df_insert_sql['result']=='fail']
    
    # print(f'失败：{len(df_insert_sql_fail)}')
    
    # from elias import wechat as w
    # u.df_send_file(df_insert_sql_fail
    #                 ,fname = f'【写入失败{len(df_insert_sql_fail)}条记录】_{u.today()}_df_insert_sql_fail'
    #                 ,key = w.robots('nl_file_output')
    #                 )
    
    # # 数据回滚
    # drop_sql = get_drop_sql_ch(table_name = table_name,hosts_write = hosts_write)
    # clickhouse_ddl(drop_sql)
    # return_sql = get_altername_sql_ch(table_name = backup_table_name,new_table_name = table_name,hosts_write = hosts_write)
    # clickhouse_ddl(return_sql)
    # print(f'{table_name}，数据写入失败，回滚成功')
    
    # print(f'{table_name}，数据写入成功')
    # result_sql = f'\n-----------\ncreate_sql:\n{create_sql}\n\n-----------\ninsert_sql:\n{insert_sql}\n\n-----------\naltername_sql:\n{altername_sql}\n\n'
    
    return len_rows,s_rows,f_rows


# print('''
#       INSERT INTO `bi_report`.`test_table` FORMAT Values
#  ('2021-06-12','何玺','谭文龙',NULL,'师伟','能良电器>>家电数码一部>>京东运营','雅迪（yadea）','雅迪能良专卖店','京东商城','雅迪（yadea）:M6冠能版/60V22A灰色靠背版','雅迪（yadea）:M6冠能版/60V22A灰色靠背版 M6冠能版/60V22A灰色靠背版');
#       ''')

# sql = r'''
# INSERT INTO `bi_report`.`test_table` FORMAT Values
#  ('2021-06-12','梅权坤','谭文龙',NULL,'师伟','能良电器>>家电数码一部>>天猫智能家居','xiaovv','能良数码官方旗舰店','天猫商城','xiaovv户外云台摄像机P1 白色2K','xiaovv户外云台摄像机P1 白色2K 白色');
#   '''
# clickhouse_ddl(sql)  





# from elias import usual as u
# sql = '''
# SELECT
#  	-- w.id,
#  	w.snd_date AS 日期,
#  	e4.`name` AS 四级经营者,
#  	e3.`name` AS 三级经营者,
#  	e2.`name` AS 二级经营者,
#  	e1.`name` AS 一级经营者,
#  	w.venture_name AS 经营体,
#  	w.g_brand AS 品牌,
#  	s.shop_name AS 店铺,
#  	s.shop_type AS 平台,
#  	w.goods_name as 商品,
# -- 	g.goods_name as g_goods_name,
# -- 	g.spec_name as g_spec_name,
#  	CONCAT(g.goods_name,' ',g.spec_name) as SKU
# FROM
#  	order_wide_tab w
#  	LEFT JOIN om_org_employee e4 ON w.principal = e4.id
#  	LEFT JOIN om_org_employee e3 ON w.per_id_level_low_name = e3.id
#  	LEFT JOIN om_org_employee e2 ON w.per_id_level_middle_name = e2.id
#  	LEFT JOIN om_org_employee e1 ON w.per_id_level_top_name = e1.id 
#  	LEFT JOIN om_t_shop s ON s.shop_id = w.shop_id
#  	LEFT JOIN om_t_goods g ON g.goods_id = w.goods_id
# WHERE 
#  	( e4.`name` IS NULL
#  	OR e3.`name` IS NULL
#  	OR e2.`name` IS NULL
#  	OR e1.`name` IS NULL
#  	OR w.venture_name IS NULL
#  	OR w.g_brand  IS NULL
#  	OR s.shop_name IS NULL
#  	OR s.shop_type IS NULL
#  	OR w.goods_name IS NULL
#  	OR g.goods_name IS NULL
#  	OR g.spec_name IS NULL)
#     limit 100
# '''


# fname = '维度字段缺失情况'
# hosts_read= u.all_hosts(name = 'om')
# key = w.robots('nl_file_output')

# df = u.mysql_select(sql, hosts = hosts_read)
# ch_write(df,table_name = 'test_table',comment = 'test',hosts_write= u.all_hosts(name = 'ch_bi_report'))
