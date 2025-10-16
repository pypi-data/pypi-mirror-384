# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 15:15:46 2023
ads_daifa_order_details_d_f
@author: nlsm
"""


from elias import usual as u
from elias import wechat as w


# # ===============================================================================================================================
# from elias import usual as u
# from elias import wechat as w
# from elias import sql as s
# import time
# print(f"\n\n\n##########################################################\n\n{u.today()}\n")
# # --------------------------------------------------------------------------------------------

# # 表名
# name = 'ads_daifa_order_details_d_f'

# # 表注释
# comment = '代发订单明细'

# # sql
# sql = s.mysql.ads_daifa_order_details_d_f()

# # host
# hosts_read = u.all_hosts(name = 'spider')
# hosts_write = u.all_hosts(name = 'bi_report')

# # robot
# robot_key = w.robots(name='nl_bi_details')

# # run_info
# mission_name = 'om'
# m_id = 'om_004'



def mysql_etl(m_id,mission_name,name,comment,sql,hosts_read,hosts_write,hosts_records,robot_key,index_columns_list=[],wtype='r',astype_dic={}): # 
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '查询sql：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        df = u.mysql_select(sql, hosts_read)
        print('数据量为：',len(df))
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    plan = '修改字符类型：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        # df = df.astype(astype_dic)
        # df.info()
        for i in astype_dic:
            if astype_dic[i] == int:
                import numpy as np
                df[i] = df[i].replace([np.inf, -np.inf], np.nan) 
                df[i] = df[i].fillna(0)
                df[i] = df[i].round().astype(astype_dic[i])
            else:
                df[i] = df[i].astype(astype_dic[i])
        print('数据量为：',len(df))
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    # eval(df.principal[0])
    
    
    # 写入mysql
    
    # 全量表
    plan =  '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        print(plan,f'-{len(df)} success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行：{plan}\n')
    alter_sql = f"alter table `{name}` comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')

def same_mysql_etl(m_id,mission_name,name,comment,sql,hosts_read,hosts_write,hosts_records,robot_key,index_columns_list=[],wtype='r',astype_dic={},division=False): # 
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    plan = '清空表：{}'.format(name)
    print(f'\n开始执行 - {plan}')
    
    # 全量表
    try:
        # drop_sql = f'''drop table if exists {hosts_write['db']}.{name} '''
        drop_sql = f'''truncate table {hosts_write['db']}.{name} '''
        del_rows = u.mysql_ddl(drop_sql,hosts = hosts_write)
        print('数据量为：',del_rows)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,del_rows))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    plan = '创建或插入表：{}'.format(name)
    print(f'\n开始执行 - {plan}')
    # division=True
    # 全量表
    try:
        try:
            print('尝试直接查询建表')
            create_sql = f'''CREATE TABLE {hosts_write['db']}.{name} as \n {sql}'''
            row = u.mysql_ddl(sql = create_sql,hosts = hosts_write,division=division)
        except:
            print('表已存在，直接尝试插入数据')
            insert_sql = f'''insert into {hosts_write['db']}.{name} \n {sql}'''
            row = u.mysql_ddl(sql = insert_sql,hosts = hosts_write,division=division)
        # df.info()
        print('写入成功')
        print('数据量为：',row)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    # eval(df.principal[0])
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行 - {plan}')
    alter_sql = f"alter table {hosts_write['db']}.{name} comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=row
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行 - {plan}')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')


def excel_to_mysql(m_id,mission_name,name,comment,file,sheet,skiprows,hosts_write,hosts_record,robot_key,index_columns_list=[],wtype='r',excel_type = 'excel',encoding='utf-8',col_translate = True):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import pandas as pd
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
    logger = u.logger()
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    logger.info(m_name)
    logger.info(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '读取excel：{}'.format(u.file_get(file))
    logger.info(f'\n开始执行：{plan}\n')
    # file = file_path
    
    # 全量表
    try:
        if excel_type == 'excel':
            if sheet == None:
                df = pd.read_excel(file, skiprows = skiprows)
            else:
                df = pd.read_excel(file, sheet, skiprows = skiprows)
        elif excel_type == 'csv':
            df = pd.read_csv(file,skiprows = skiprows,encoding = encoding)
        else:
            raise ValueError("Unsupported excel_type.(Only excel & csv)")
        # -----------
        logger.info(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        logger.error('dq_Error:', str(e))
        logger.error(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    if col_translate == True:
        # 转换字段名
        plan = '转换字段名：{}'.format(name)
        logger.info(f'\n开始执行：{plan}\n')
        try:
            list_col_tr = [u.get_name(col) for col in df.columns]
            logger.info('数据量为：',len(df))
            dic_col = {}
            for col in df.columns:
                dic_col[u.get_name(col)]=col
            df.columns = list_col_tr
        except Exception as e:
            logger.error(plan,' fail\n')
            m_list.append('{},fail'.format(plan))
            if status == 0:
                w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                status = status + 1
            else:
                pass
    else:
        pass

    # 写入mysql
    
    # 全量表
    plan =  '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        logger.info(plan,f'-{len(df)} success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        logger.error(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行：{plan}\n')
    alter_sql = f"alter table {name} comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        logger.info(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        logger.error(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            logger.info(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                logger.info(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                logger.error(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        logger.info('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    logger.info(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    logger.info('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    logger.info(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_record)
        
        # -----------
        logger.info(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        logger.error(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    logger.info(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    logger.info('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    logger.info(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        logger.info('\n任务执行日报发送成功')




def mysql_to_clickhouse(m_id,mission_name,name,comment,sql,hosts_read,hosts_write,hosts_record,robot_key):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    from elias.Scripts import py_clickhouse as c
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    n = 5
    while n != 0 :
        plan = '查询sql：{}'.format(name)
        print(f'\n开始执行：{plan}\n')
        
        # 全量表
        try:
            df = u.mysql_select(sql, hosts_read)
            print('数据量为：',len(df))
            
            # -----------
            print(plan,' success\n')
            f_c = f_c + 1
            m_list.append('{},success'.format(plan))
        except Exception as e:
            print('dq_Error:', str(e))
            print(plan,' fail\n')
            m_list.append('{},fail'.format(plan))
            if status == 0:
                w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                status = status + 1
            else:
                pass
        
        
        
        
        # 确认查询结果
        l = len(df)
        s = ''
        s = f'【第{6-n}次】查询结果数据：{l}行\n'
        if l==0:
            s = s+'查询失败！'
            w.run_warning(title = name,text = s, user='yiting.liu',key = robot_key)
            n=n-1
        else:
            s = s+'查询成功！'
            w.run_warning(title = name,text = s, user='yiting.liu',key = robot_key)
            n = 0
            
        
        
    
    time.sleep(1)
    
    # 写入clickhouse
    
    rn = 5
    while rn != 0:
    
        # 全量表
        plan = f'【第{6-rn}次】写入数据:{name}'
        print(f'\n开始执行：{plan}\n')
        try:
            result_sql = c.ch_write(df,table_name=name,comment=comment,hosts_write= hosts_write,update = True)
            # u.mysql_write(df,name,update = True,hosts = hosts_write)
            
            # -----------
            print(plan,f'-{len(df)} success\n')
            f_c = f_c + 1
            m_list.append('{},success'.format(plan))
        except Exception as e:
            print(plan,' fail\n', "Error:",str(e))
            m_list.append('{},fail'.format(plan))
            if status == 0:
                w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                status = status + 1
            else:
                pass
        
        time.sleep(5)
        print('\n开始验证写入结果 ……')
        time.sleep(5)
        
        # 验证写入结果
        plan = f'【第{6-rn}次】验证写入结果:{name}'
        print(f'\n开始执行：{plan}\n')
        try:
            r_count = c.result_verify(table_name=name,hosts = hosts_write)
            
            # -----------
            print(plan,' success\n')
            f_c = f_c + 1
            m_list.append('{},success'.format(plan))
        except Exception as e:
            print(plan,' fail\n', "Error:",str(e))
            m_list.append('{},fail'.format(plan))
            if status == 0:
                w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                status = status + 1
            else:
                pass
            r_count = 0
            
        
        # time.sleep(5)
        # print(f'验证完成，确认数据：{r_count}条')
        
        
        rs = ''
        rs = f'【第{6-rn}次】写入结果数据：{r_count}行\n'
        print('\n',rs)
        if r_count == 0:
            rs = rs+'数据写入失败！'
            w.run_warning(title = name,text = rs, user='yiting.liu',key = robot_key)
            rn = rn-1
        else:
            rs = rs+'数据写入成功！'
            w.run_warning(title = name,text = rs, user='yiting.liu',key = robot_key)
            rn = 0
    
    # # 添加表注释
    
    # '''
    # clickhouse 语法
    # comment  on  column  表名.字段名   is  '注释内容';
    # comment on table 表名  is  '注释内容';
    # '''
    
    # plan = '添加表注释：{}'.format(comment)
    
    # # mysql
    # # alter_sql = f"alter table {name} comment '{comment}'"
    
    # # clickhouse
    # alter_sql = f"ALTER TABLE comment on table `{hosts_write['db']}`.`{name}`  is '{comment}'"
    # alter_sql = f'''ALTER TABLE `{hosts_write['db']}`.`{name}` COMMENT '{comment}';'''
    
    
    # try:
    #     # u.mysql_ddl(alter_sql,hosts = hosts_write)
    #     c.clickhouse_ddl(sql = alter_sql,hosts = hosts_write)
        
    #     # -----------
    #     print(plan,' success\n')
    #     f_c = f_c + 1
    #     m_list.append('{},success'.format(plan))
    # except Exception as e:
    #     print(plan,' fail\n', "Error:",str(e))
    #     m_list.append('{},fail'.format(plan))
    #     if status == 0:
    #         w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
    #         status = status + 1
    #     else:
    #         pass
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    
    
    try:
        sql = sql+result_sql
    except:
        sql=sql
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_record,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')

def clickhouse_to_mysql(m_id,mission_name,name,comment,sql,hosts_read,hosts_write,hosts_record,robot_key,index_columns_list=[],wtype='r'):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    from elias.Scripts import py_clickhouse as c
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '查询sql：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        df = u.clickhouse_select(sql, hosts_read)
        print('数据量为：',len(df))
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    
    # 写入mysql
    
    # 全量表
    plan = '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        print(plan,f'-{len(df)} success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行：{plan}\n')
    alter_sql = f"alter table {name} comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_record,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')

def clickhouse_to_mysql_i(m_id,mission_name,name,comment,del_sql,sql,hosts_read,hosts_write,hosts_record,robot_key,index_columns_list=[],wtype='r'):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    from elias.Scripts import py_clickhouse as c
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '删除数据：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        r = u.mysql_ddl(del_sql, hosts_write)
        print(r)
        
        # -----------
        print(plan,f'- {r} success\n')
        f_c = f_c + 1
        m_list.append('{}- {},success'.format(plan,r))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    plan = '查询sql：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        df = u.clickhouse_select(sql, hosts_read)
        print('数据量为：',len(df))
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    
    # 写入mysql
    
    # 全量表
    plan = '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        print(plan,f'-{len(df)} success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行：{plan}\n')
    alter_sql = f"alter table {name} comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_record,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')

def mysql_ddl(m_id,mission_name,name,comment,sql,hosts_read,hosts_write,hosts_record,robot_key,index_columns_list=[],wtype='r'):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '执行sql：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        df = u.mysql_ddl(sql, hosts_read)
        print('数据量为：',df)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    
    # # 添加表注释
    
    # plan = '添加表注释：{}'.format(comment)
    # alter_sql = f"alter table {name} comment '{comment}'"
    # try:
    #     u.mysql_ddl(alter_sql,hosts = hosts_write)
        
    #     # -----------
    #     print(plan,' success\n')
    #     f_c = f_c + 1
    #     m_list.append('{},success'.format(plan))
    # except Exception as e:
    #     print(plan,' fail\n', "Error:",str(e))
    #     m_list.append('{},fail'.format(plan))
    #     if status == 0:
    #         w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
    #         status = status + 1
    #     else:
    #         pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=df
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_record,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')


def mysql_ddl_list(m_id,mission_name,name,comment,sql_list,hosts_read,hosts_write,hosts_record,robot_key,index_columns_list=[],wtype='r'):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    sql_num = 0
    for sql in sql_list:
        sql_num = sql_num+1
        plan = '执行sql-{}：{}'.format(sql_num,name)
        print(f'\n开始执行：{plan}\n')
    
        # 全量表
        try:
            df = u.mysql_ddl(sql, hosts_read)
            print('数据量为：',df)
            
            # -----------
            print(plan,' success\n')
            f_c = f_c + 1
            m_list.append('{},success'.format(plan))
        except Exception as e:
            print('dq_Error:', str(e))
            print(plan,' fail\n')
            m_list.append('{},fail'.format(plan))
            if status == 0:
                w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                status = status + 1
            else:
                pass
    
    
    
    # # 添加表注释
    
    # plan = '添加表注释：{}'.format(comment)
    # alter_sql = f"alter table {name} comment '{comment}'"
    # try:
    #     u.mysql_ddl(alter_sql,hosts = hosts_write)
        
    #     # -----------
    #     print(plan,' success\n')
    #     f_c = f_c + 1
    #     m_list.append('{},success'.format(plan))
    # except Exception as e:
    #     print(plan,' fail\n', "Error:",str(e))
    #     m_list.append('{},fail'.format(plan))
    #     if status == 0:
    #         w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
    #         status = status + 1
    #     else:
    #         pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=df
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_record,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')


def df_etl(m_id,mission_name,name,comment,df,hosts_write,hosts_records,robot_key,index_columns_list=[],wtype='r'):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    sql = 'DataFrame'
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # # --------------------------------------------------------------------------------------------
    # # 查询sql
    
    # plan = '查询sql：{}'.format(name)
    
    # # 全量表
    # try:
    #     df = u.mysql_select(sql, hosts_read)
    #     print('数据量为：',len(df))
        
    #     # -----------
    #     print(plan,' success\n')
    #     f_c = f_c + 1
    #     m_list.append('{},success'.format(plan))
    # except Exception as e:
    #     print('dq_Error:', str(e))
    #     print(plan,' fail\n')
    #     m_list.append('{},fail'.format(plan))
    #     if status == 0:
    #         w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
    #         status = status + 1
    #     else:
    #         pass
    
    
    
    # 写入mysql
    
    # 全量表
    plan =  '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        print(plan,f'-{len(df)} success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行：{plan}\n')
    alter_sql = f"alter table {name} comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')



def mysql_etl_i(m_id,mission_name,name,comment,del_sql,sql,hosts_read,hosts_write,hosts_records,robot_key,index_columns_list=[],wtype='r',astype_dic={}):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '删除数据：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        r = u.mysql_ddl(del_sql, hosts_write)
        print(r)
        
        # -----------
        print(plan,f'- {r} success\n')
        f_c = f_c + 1
        m_list.append('{}- {},success'.format(plan,r))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
        
    
    plan = '查询sql：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        df = u.mysql_select(sql, hosts_read)
        print('数据量为：',len(df))
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    plan = '修改字符类型：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        # df = df.astype(astype_dic)
        # df.info()
        for i in astype_dic:
            if astype_dic[i] == int:
                import numpy as np
                df[i] = df[i].replace([np.inf, -np.inf], np.nan) 
                df[i] = df[i].fillna(0)
                df[i] = df[i].round().astype(astype_dic[i])
            else:
                df[i] = df[i].astype(astype_dic[i])
        print('数据量为：',len(df))
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    
    # 写入mysql
    
    # 全量表
    plan =  '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        print(plan,f'-{len(df)} success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # 添加表注释
    
    plan = '添加表注释：{}'.format(comment)
    print(f'\n开始执行：{plan}\n')
    alter_sql = f"alter table {name} comment '{comment}'"
    try:
        u.mysql_ddl(alter_sql,hosts = hosts_write)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    if index_columns_list==[]:
        pass
    else:
        for column in index_columns_list:
    
            # 添加字段索引
            
            plan = '添加字段索引：{}'.format(column)
            print(f'\n开始执行：{plan}\n')
            try:
                u.mysql_add_index(column, table=name, hosts = hosts_write)
                
                # -----------
                print(plan,' success\n')
                f_c = f_c + 1
                m_list.append('{},success'.format(plan))
            except Exception as e:
                print(plan,' fail\n', "Error:",str(e))
                m_list.append('{},fail'.format(plan))
                if status == 0:
                    w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
                    status = status + 1
                else:
                    pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')


def clickhouse_del_insert_i(m_id,mission_name,name,comment,del_sql,sql_insert,hosts_read,hosts_write,hosts_records,robot_key,index_columns_list=[],wtype='r'):
 
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    from elias.Scripts import py_clickhouse as c
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()


    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    
    # --------------------------------------------------------------------------------------------
    # 查询sql
    
    plan = '删除数据：{}'.format(name)
    
    # 全量表
    try:
        r = c.clickhouse_ddl(sql = del_sql,hosts = hosts_write)
        print(r)
        
        # -----------
        print(plan,f'- {r} success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    
    # 写入mysql
    
    # 全量表
    plan =  '写入数据:{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    try:
        c.clickhouse_ddl(sql = sql_insert,hosts = hosts_write)
        # u.mysql_write(df,name,update = True,hosts = hosts_write,wtype=wtype)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
        
    
    plan = '验证插入：{}'.format(name)
    print(f'\n开始执行：{plan}\n')
    
    # 全量表
    try:
        num_df = u.clickhouse_select(sql = f'select count(*) as c from {name}',hosts = hosts_write)
        print('数据量为：',num_df['c'][0])
            
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,num_df['c'][0]))
    except Exception as e:
        print('dq_Error:', str(e))
        print(plan,' fail\n')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # # 添加表注释
    
    # plan = '添加表注释：{}'.format(comment)
    # alter_sql = f"alter table {name} comment '{comment}'"
    # try:
    #     u.mysql_ddl(alter_sql,hosts = hosts_write)
        
    #     # -----------
    #     print(plan,' success\n')
    #     f_c = f_c + 1
    #     m_list.append('{},success'.format(plan))
    # except Exception as e:
    #     print(plan,' fail\n', "Error:",str(e))
    #     m_list.append('{},fail'.format(plan))
    #     if status == 0:
    #         w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
    #         status = status + 1
    #     else:
    #         pass
    
    
    # if index_columns_list==[]:
    #     pass
    # else:
    #     for column in index_columns_list:
    
    #         # 添加字段索引
            
    #         plan = '添加字段索引：{}'.format(column)
    #         try:
    #             u.mysql_add_index(column, table=name, hosts = hosts_write)
                
    #             # -----------
    #             print(plan,' success\n')
    #             f_c = f_c + 1
    #             m_list.append('{},success'.format(plan))
    #         except Exception as e:
    #             print(plan,' fail\n', "Error:",str(e))
    #             m_list.append('{},fail'.format(plan))
    #             if status == 0:
    #                 w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
    #                 status = status + 1
    #             else:
    #                 pass
    
    
    
    
    
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=num_df['c'][0]
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = f'{del_sql}\n-----\n{sql_insert}\n-----\nselect count(*) from {name}')
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]


    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')


def sql_to_mail(m_id,mission_name,name,robot_key,sql,hosts,username,password,receivers=[],accs=[],links={},subject='test',contents='test',hosts_records = u.all_hosts('bi_report'),date=u.yesterday()):
    '''
    
    功能：
    从sql取数，导出成excel文件，上传邮箱附件，并发送给指定收件人，最后本地导出的删除文件。
    

    Parameters
    ----------
    m_id : TYPE
        任务id.
    mission_name : TYPE
        任务类别名称.
    name : TYPE
        任务名称（文件名）.
    robot_key : TYPE
        任务情况发送的机器人.
    sql : TYPE
        文件的取数sql.
    hosts : TYPE
        取数的数据库服务器.
    username : TYPE
        邮件发送账号.
    password : TYPE
        邮件发送账号的密码.
    receivers : TYPE, optional
        邮件收件人. The default is [].
    accs : TYPE, optional
        邮件抄送人. The default is [].
    links : TYPE, optional
        超链接. The default is {}.
    subject : TYPE, optional
        邮件主题. The default is 'test'.
    contents : TYPE, optional
        邮件内容. The default is 'test'.
    hosts_records : TYPE, optional
        任务记录的数据库服务器. The default is u.all_hosts('bi_report').

    Returns
    -------
    result : TYPE
        机器人发送的报告文本.
    list
        任务记录存储的记录.

    '''
    
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    from loguru import logger
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()
    
    
    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    # ------------------------------------------------------------------------------
    # 查询数据

    
    plan = '查询数据：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    
    try:
        df = u.mysql_select(sql, hosts)
    
        # -----------
        logger.info(f'{plan} success！')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        logger.warning(f'报错原因：{str(e)}')
        logger.info(f'{plan} fail')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # ------------------------------------------------------------------------------
    # 导出文件

    
    plan = '查询数据：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    if len(df)==0:
        raise ValueError('DataFrame 没有数据！')
        
    
    
    
    
    
    # ------------------------------------------------------------------------------
    # 导出文件

    
    plan = '文件导出：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    try:
    
        file_name = f"{name}_{date.replace('-','')}.xlsx"
        df.to_excel(file_name,index=False)
        
        # -----------
        logger.info(f'{plan} success！')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        logger.warning(f'报错原因：{str(e)}')
        logger.info(f'{plan} fail')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
      
    # ------------------------------------------------------------------------------
    # 发送邮件 

    
    plan = '邮件发送：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    try:
        u.Email_send(username, password, subject, contents, receivers=receivers, accs=accs, links=links, file_pathname=file_name, smtp='exmail')
        
        # -----------
        logger.info(f'{plan} success！')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        logger.warning(f'报错原因：{str(e)}')
        logger.info(f'{plan} fail')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    
    
    
       
      
    # ------------------------------------------------------------------------------
    # 删除文件
    
    import os 

    
    plan = '文件删除：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    try:
        os.remove(file_name)
        
        # -----------
        logger.info(f'{plan} success！')
        f_c = f_c + 1
        m_list.append('{}-{},success'.format(plan,len(df)))
    except Exception as e:
        logger.warning(f'报错原因：{str(e)}')
        logger.info(f'{plan} fail')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
     
    
    
    
        
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=len(df)
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = sql)
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]
    
    
    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')

def proxy_mysql_to_clickhouse(m_id,mission_name,name,origin_table_name,origin_hosts,target_hosts,hosts_records,robot_key):

    
    # ===============================================================================================================================
    from elias import usual as u
    from elias import wechat as w
    from elias.Scripts import vm_clickhouse as vc
    from loguru import logger
    import time 
    print(f"\n\n\n##########################################################\n\n{u.today()}\n")
    # --------------------------------------------------------------------------------------------
        
    # table = f'{name}'
    m_name =f'{m_id}_{name}'
    ee = None
    
    # --------------------------------------------------------------------------------------------
    
    status = 0
    mission = f'{m_name}'
    plan = ''
    f_c = 0
    m_list = []
    
    
    
    # --------------------------------------------------------------------------------------------
    start = time.time()
    
    
    print(m_name)
    print(u.Stamp_to_Datetime(start))
    
    
    # ------------------------------------------------------------------------------
    # 查询数据

    
    plan = '代理数据：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    
    try:
        vc.auto_clickhouse(
                            origin_table_name = origin_table_name,
                            origin_hosts = origin_hosts,
                            target_hosts = target_hosts
                           )
    
        # -----------
        logger.info(f'{plan} success！')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        logger.warning(f'报错原因：{str(e)}')
        logger.info(f'{plan} fail')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
    # ------------------------------------------------------------------------------
    # 导出文件

    
    plan = '查询数据：{}'.format(name)
    logger.info(f'\n开始执行：{plan}\n')
    
    
    try:
        
        df = u.clickhouse_select(f'select count(*) as c from `ch_{origin_table_name}`', target_hosts)
        dfnum = df['c'][0]
        if dfnum==0:
            raise ValueError('DataFrame 没有数据！')
        # -----------
        logger.info(f'{plan} success！')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        logger.warning(f'报错原因：{str(e)}')
        logger.info(f'{plan} fail')
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
    
    
        
    # --------------------------------------------------------------------------------------------
    
    try:
        rows=dfnum
        print('rows:',rows)
    except:
        rows=0
        pass
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = round(end-start, 2)
    print('usetime:', round(end-start, 2), 'seconds')
    
    
    # --------------------------------------------------------------------------------------------
    
    # 执行结果写入
    plan = '执行结果写入records'
    print(f'\n开始执行：{plan}\n')
    try:
        if len(m_list)-f_c==0:
            r='success'
        else:
            r='fail'
        u.py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts=hosts_records,sql = f'select * from `{origin_table_name}`')
        
        # -----------
        print(plan,' success\n')
        f_c = f_c + 1
        m_list.append('{},success'.format(plan))
    except Exception as e:
        if ee == None:
            ee = str(e)
        print(plan,' fail\n', "Error:",str(e))
        m_list.append('{},fail'.format(plan))
        if status == 0:
            w.warning_mission(mission=mission,plan=plan,e=e,key=robot_key)
            status = status + 1
        else:
            pass
      
        
    # --------------------------------------------------------------------------------------------
    
    end = time.time()
    print(u.Stamp_to_Datetime(end))
    usetime = str(round(end-start, 2))+ ' seconds'
    print('usetime:', round(end-start, 2), 'seconds')
    
    # --------------------------------------------------------------------------------------------
    # 统计任务执行日报
    all_c = len(m_list)
    success_c = f_c
    fail_c = all_c - success_c
    title = "%s - %s"%(mission,usetime)
    content = '\n'.join(m_list)
    
    result = u.py_mission_robot_message(mission,start,end,all_c,fail_c,success_c)
    print(result)
    
    return result,[title,content,fail_c,success_c,all_c]
    
    
    # 发送任务执行日报
    if __name__ == '__main__' or fail_c>0:
        w.run_report(title = title,text = content,fail_count=fail_c,success_count=success_c,all_count=all_c,key=robot_key,user='刘益廷')
        print('\n任务执行日报发送成功')
