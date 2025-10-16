# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 16:08:22 2022
主要用途：数据同步
@author: Elias
"""

def data_delete(dst_conn,table_name):
    import time
    start = time.time()
    dst_cursor = dst_conn.cursor()
    dst_cursor.execute(f'truncate {table_name}' )
    dst_conn.commit()
    dst_cursor.close() 
    dst_conn.close()
    print(f'{table_name},数据清除成功！')
    end = time.time()
    print('usetime:', round(end-start, 2), 'seconds') # 用时测算


def data_move(goal_conn,origin_conn,table_name=''):# 逐条同步
    import time
    # 确认指针
    origin_cur = origin_conn.cursor()
    goal_cur = goal_conn.cursor()
    # 源数据查询
    select_sql = f'SELECT * FROM `{table_name}` a'
    origin_cur.execute(select_sql)
    
    # 逐条往目标连接插入
    table = 0
    n=0
    start = time.time()
    while table is not None:  
        table = origin_cur.fetchone()
        if table is not None:
            fieldstr = ','.join([str(i) for i in table])
            valuestr = tuple([table[key] for key in table])
            insert_sql = "insert into %s (%s) values %s;"%(table_name,fieldstr,valuestr)
            insert_sql = insert_sql.replace('None', 'NULL')
            try:
                goal_cur.execute(insert_sql)
                goal_conn.commit()
                n+=1
                # print(f"第{n}条数据，插入成功")
            except Exception as e:
                print(f"第{n}条数据，插入失败，{valuestr}")
                print('insert_sql:', str(insert_sql))
                print('dq_Error:', str(e))
                goal_conn.rollback()
                break
    end = time.time()
    print('success ',n,'条数据') # 数据成功插入计数
    # usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds') # 用时测算
    
    # 关闭游标
    goal_cur.close() 
    origin_cur.close() 
    
    # 关闭连接
    goal_conn.close() 
    origin_conn.close() 




def data_column(column_conn,table_name):
    # 源数据查询
    select_sql = f'SELECT * FROM `{table_name}`'
    
    # 确认字段名
    test_conn = column_conn
    test_cur = test_conn.cursor()

    test_cur.execute(select_sql)
    a = test_cur.fetchone()

    fieldstr = ''
    varstr = ''

    for i in range(len(list(a))):
        if i == 0:
            fieldstr = list(a)[i]
            varstr = '%s'
        else:
            fieldstr += "," + list(a)[i]
            varstr += ',%s'
    
    test_cur.close() 
    test_conn.close() 
    return fieldstr,varstr


# table_name = f'{name}'

def data_move_all(goal_conn,origin_conn,table_name='',goal_table_name='',limit=None):# 数据整体同步
    import time
    
    if goal_table_name=='':
        goal_table_name = table_name
    
    # 源数据查询
    if limit == None:
        limit = ''
    else:
        limit = 'limit '+str(limit)
    select_sql = f'SELECT * FROM `{table_name}` {limit}'
    
    # goal_conn = u.mysql_con(host_name=goal_host_name)
    # origin_conn = u.mysql_con(host_name=origin_host_name)
      
    # 确认指针
    origin_cur = origin_conn.cursor()
    goal_cur = goal_conn.cursor()
    
    # 执行sql
    origin_cur.execute(select_sql)
    
    # 整体数据提取
    n=0
    value_list =[]
    # start = time.time()
    start1 = time.time()
    a = origin_cur.fetchall()
    end1 = time.time()
    print('【数据导入内存】usetime:', round(end1-start1, 2), 'seconds') # 用时测算
    
    start2 = time.time()
    for data in a:
        # list_tuple = []
        # for key in data:
        #     if data[key] == None:
        #         data[key] = ''
        #     else:
        #         data[key] = data[key]
        #     list_tuple.append(data[key])
        # valuestr = tuple(list_tuple)
        
        
        valuestr = tuple([data[key] for key in data])
        
        # insert_sql = "insert into %s (%s) values %s;"%(table_name,fieldstr,valuestr)
        value_list.append(valuestr)
        n+=1
        if n%1000000==0:
            print(n,'条数据')
    end2 = time.time()
    print('【行数据转换元组】usetime:', round(end2-start2, 2), 'seconds') # 用时测算
    
    
    fieldstr = ''
    varstr = ''
    for i in range(len(list(a[0]))):
        if i == 0:
            fieldstr = f'`{list(a[0])[i]}`'
            varstr = '%s'
        else:
            fieldstr += "," + f'`{list(a[0])[i]}`'
            varstr += ',%s'
    
    
    start = time.time()
    # 往目标连接插入
    try:
        goal_cur.executemany("insert into " + goal_table_name + "(" + fieldstr + ") values(" + varstr + ");", value_list)
        # goal_cur.executemany(insert_sql)
        goal_conn.commit()
        result ='数据插入成功'
        # print(f"第{n}条数据，插入成功")
    except Exception as e:
        print(f"第{n}条数据，插入失败，{valuestr}")
        print('dq_Error:', str(e))
        result = f'''第{n}条数据，插入失败，{valuestr}\ndq_Error: {str(e)}'''
        goal_conn.rollback()
        # break
    # for data in origin_cur.fetchall(): 
    #     goal_cur.executemany("insert into " + table_name + "(" + fieldstr + ") values(" + varstr + ");", [data])
    #     n+=1

    end = time.time()
    print('success ',n,'条数据') # 数据成功插入计数
    # usetime = str(round(end-start, 2))+ ' seconds'
    print('【insert执行】usetime:', round(end-start, 2), 'seconds') # 用时测算

    # 关闭游标
    goal_cur.close() 
    origin_cur.close() 
    
    # 关闭连接
    goal_conn.close() 
    origin_conn.close() 
    
    return result







def data_move_extract(origin_conn,table_name='',limit=None,sql_type = "mysql"):
    import time
    
    # 源数据查询
    if sql_type == "mysql":
        if limit == None:
            limit = ''
        else:
            limit = 'limit '+str(limit)
        select_sql = f'SELECT * FROM {table_name} {limit}'
    elif sql_type=="sqlserver":
        if limit == None:
            select_sql = f'SELECT * FROM {table_name} '
        else:
            select_sql = f'SELECT Top {limit} * FROM {table_name} '
    
    # goal_conn = u.mysql_con(host_name=goal_host_name)
    # origin_conn = u.mysql_con(host_name=origin_host_name)
    # origin_conn = u.sqlserver_con(host_name=origin_host_name)
      
    # 确认指针
    origin_cur = origin_conn.cursor()
    
    # 执行sql
    origin_cur.execute(select_sql)
    
    # 整体数据提取
    start1 = time.time()
    a = origin_cur.fetchall()
    end1 = time.time()
    print('【数据导入内存】usetime:', round(end1-start1, 2), 'seconds') # 用时测算
    
    # 关闭游标
    origin_cur.close() 
    
    # 关闭连接
    origin_conn.close() 
    return a


def data_move_transform(a):
    import time
    start2 = time.time()
    
    n=0
    value_list =[]
    for data in a:
        # list_tuple = []
        # for key in data:
        #     if data[key] == None:
        #         data[key] = ''
        #     else:
        #         data[key] = data[key]
        #     list_tuple.append(data[key])
        # valuestr = tuple(list_tuple)
        
        key_list = []
        for key in data:
            # key = data[-10]
            print(key,type(key))
            if type(key)==str:
                key = key.strip().replace('\t', '').replace('\r', '')
                print(key)
            key_list.append(key)
        valuestr = tuple(key_list)    
        # valuestr = tuple([key for key in data])
        
        # insert_sql = "insert into %s (%s) values %s;"%(table_name,fieldstr,valuestr)
        value_list.append(valuestr)
        n+=1
        if n%1000000==0:
            print(n,'条数据')
        fieldstr = ''
        varstr = ''
    for i in range(len(list(a[0]))):
        if i == 0:
            fieldstr = f'`{list(a[0])[i]}`'
            varstr = '%s'
        else:
            fieldstr += "," + f'`{list(a[0])[i]}`'
            varstr += ',%s'
    
    end2 = time.time()
    print('【行数据转换元组】usetime:', round(end2-start2, 2), 'seconds') # 用时测算
    return fieldstr,varstr,value_list,n


def data_move_load(goal_conn,goal_table_name,fieldstr,varstr,value_list,n):
    import time
    start = time.time()
    
    
    # 确认指针
    goal_cur = goal_conn.cursor()
    
    # 往目标连接插入
    try:
        goal_cur.executemany("insert into " + goal_table_name + "(" + fieldstr + ") values(" + varstr + ");", value_list)
        # goal_cur.executemany(insert_sql)
        goal_conn.commit()
        result ='数据插入成功'
        # print(f"第{n}条数据，插入成功")
    except Exception as e:
        result = f'''数据插入失败，\ndq_Error: {str(e)}'''
        print(result)
        goal_conn.rollback()
        n = 0
        # break
    # for data in origin_cur.fetchall(): 
    #     goal_cur.executemany("insert into " + table_name + "(" + fieldstr + ") values(" + varstr + ");", [data])
    #     n+=1

    end = time.time()
    print('success ',n,'条数据') # 数据成功插入计数
    # usetime = str(round(end-start, 2))+ ' seconds'
    print('【insert执行】usetime:', round(end-start, 2), 'seconds') # 用时测算

    # 关闭游标
    goal_cur.close() 
    
    # 关闭连接
    goal_conn.close() 
    
    return result
