# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 16:23:37 2023

@author: Administrator
"""


from elias import usual as u
from loguru import logger

def quality_check_records(df_records,output_table_name,output_hosts):
    if output_hosts=={}:
        logger.warning(f'output_hosts is not configed. Table "{output_table_name}" will not be recorded.')
        pass
    else:
        show_df = u.mysql_select("show tables", output_hosts)
        show_df.columns = ['tables']
        if output_table_name not in list(show_df['tables']):
            logger.warning(f'Table "{output_table_name}" is not exits. Now creating ……')
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='r')
            
        else:
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='a')  

def integrity_check(table_name,hosts,where,output='integrity_rate',output_hosts={},output_table_name = 'quality_check_records_integrity'):
    '''
    完备性检查

    Parameters
    ----------
    table_name : TYPE
        DESCRIPTION.
    hosts : TYPE
        DESCRIPTION.

    Returns
    -------
    null_rows : TYPE
        DESCRIPTION.

    '''
    from elias.datax import auto_create_table as ac
    df = ac.schema_transfer(ac.schema_read(table_name,hosts))
    
    target_db_type = hosts['dbtype']
    
    if str(where) in ['-','','nan']:
        where = ''
        pass
    elif "where" not in where:
        where = f'where \n  {where}'
        
    if target_db_type == 'mysql':
        col_sql_list = []
        for i in range(len(df)):
            if df['col_type_name'][i] in ['int','float'] or df['col_type'][i] in ['date']:
                col_sql = f"`{df['col_name'][i]}` is null"
            elif df['col_type_name'][i] in ['string','text']:
                col_sql = f"`{df['col_name'][i]}`= '' or `{df['col_name'][i]}` is null"
            else:
                col_sql = f"`{df['col_name'][i]}`= '' or `{df['col_name'][i]}` is null"
            
            # col_sql = f"{col_sql1} or `{df['col_name'][i]}` is null"
            col_sql_list.append(col_sql)
        
        final_col_sql = '\n or '.join(col_sql_list)
        
        sql = f'''
        SELECT
        sum(if({final_col_sql},1,0)) as `null_rows`,
        count(*) as `rows`,
        sum(if({final_col_sql},1,0))/count(*) as `null_rate`,
        1-(sum(if({final_col_sql},1,0))/count(*)) as `integrity_rate`
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')
        
        df_null = u.mysql_select(sql, hosts)
    
    
    elif target_db_type == 'clickhouse':
        col_sql_list = []
        for i in range(len(df)):
            if df['col_type_name'][i] in ['int','float'] or df['col_type'][i] in ['Date']:
                col_sql = f"`{df['col_name'][i]}` is null"
            elif df['col_type_name'][i] in ['string','text']:
                col_sql = f"`{df['col_name'][i]}`= '' or `{df['col_name'][i]}` is null"
            else:
                col_sql = f"`{df['col_name'][i]}`= '' or `{df['col_name'][i]}` is null"
            
            # col_sql = f"{col_sql1} or `{df['col_name'][i]}` is null"
            col_sql_list.append(col_sql)
        
        final_col_sql = '\n or '.join(col_sql_list)
        
        sql = f'''
        SELECT
        sum(if({final_col_sql},1,0)) as `null_rows`,
        count(*) as `rows`,
        sum(if({final_col_sql},1,0))/count(*) as `null_rate`,
        1-(sum(if({final_col_sql},1,0))/count(*)) as `integrity_rate`
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')
        
        df_null = u.clickhouse_select(sql, hosts)
    
    
    elif target_db_type == 'maxcompute':
        col_sql_list = []
        for i in range(len(df)):
            if df['col_type_name'][i] in ['int','float'] or df['col_type'][i] in ['date']:
                col_sql = f"`{df['col_name'][i]}` is null"
            elif df['col_type_name'][i] in ['string','text']:
                if df['col_type'][i] == 'datetime':
                    col_sql = f"`{df['col_name'][i]}` is null"
                else:
                    col_sql = f"`{df['col_name'][i]}`= '' or `{df['col_name'][i]}` is null"
            else:
                col_sql = f"`{df['col_name'][i]}`= '' or `{df['col_name'][i]}` is null"
            
            # col_sql = f"{col_sql1} or `{df['col_name'][i]}` is null"
            col_sql_list.append(col_sql)
        
        final_col_sql = '\n or '.join(col_sql_list)
        
        sql = f'''
        SELECT
        sum(if({final_col_sql},1,0)) as `null_rows`,
        count(*) as `rows`,
        sum(if({final_col_sql},1,0))/count(*) as `null_rate`,
        1-(sum(if({final_col_sql},1,0))/count(*)) as `integrity_rate`
        FROM
        	`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')
        
        df_null = u.mc_select(sql, hosts)
    
    else:
        raise ValueError("Unsupported target database type.")
    
    logger.info(f"\n\nsql select finished\n\n rows:{ df_null['rows'][0]}\n null_rows:{ df_null['null_rows'][0]}\n null_rate:{ df_null['null_rate'][0]} integrity_rate:{ df_null['integrity_rate'][0]}\n")
    try:
        result = df_null[output][0]
    except Exception as e:
        raise ValueError(f"{e}\nUnsupported output type. Only ('rows' or 'null_rows' or 'null_rate' or 'integrity_rate'")
    
    # import pandas as pd 
    df_null['today']=u.today()
    df_null['table_name']=table_name
    
    df_records = df_null[['today','table_name','integrity_rate','null_rate','null_rows','rows']]
    
    if output_hosts=={}:
        logger.warning(f'output_hosts is not configed. Table "{output_table_name}" will not be recorded.')
        pass
    else:
        show_df = u.mysql_select("show tables", output_hosts)
        show_df.columns = ['tables']
        if output_table_name not in list(show_df['tables']):
            logger.warning(f'Table "{output_table_name}" is not exits. Now creating ……')
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='r')
            
        else:
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='a')    
    
    
    return result



def key_check(table_name,hosts,key,where,output='key_rate',output_hosts={},output_table_name = 'quality_check_records_key'):
    
    target_db_type = hosts['dbtype']
    if key == '-':
        a = {'rows':'无需主键','key_rows':'无需主键','key_rate':1}
        return a[output]
    else:
        if str(where) in ['-','','nan']:
            where = ''
            pass
        elif "where" not in where:
            where = f'where \n  {where}'
            
        if target_db_type == 'mysql':
            sql = f'''
            select 
            count(*) as `rows`,
            count(distinct `{key}`) as `key_rows`,
            count(distinct `{key}`)/count(*) as `key_rate`
            FROM
            	`{hosts['db']}`.`{table_name}` x
            {where}
            '''
            logger.info(f'sql generating …… \n\n {sql} \n\n')
            logger.info('sql selecting')
    
            df_key = u.mysql_select(sql, hosts)
            
        elif target_db_type == 'clickhouse':
            sql = f'''
            select 
            count(*) as `rows`,
            count(distinct `{key}`) as `key_rows`,
            count(distinct `{key}`)/count(*) as `key_rate`
            FROM
            	`{hosts['db']}`.`{table_name}` x
            {where}
            '''
            logger.info(f'sql generating …… \n\n {sql} \n\n')
            logger.info('sql selecting')
    
            df_key = u.clickhouse_select(sql, hosts)
            
        elif target_db_type == 'maxcompute':
            sql = f'''
            select 
            count(*) as `rows`,
            count(distinct `{key}`) as `key_rows`,
            count(distinct `{key}`)/count(*) as `key_rate`
            FROM
            	`{table_name}` x
            {where}
            '''
            logger.info(f'sql generating …… \n\n {sql} \n\n')
            logger.info('sql selecting')
    
            df_key = u.mc_select(sql, hosts)
        
        else:
            raise ValueError("Unsupported target database type.")
        
        
        # import pandas as pd 
        df_key['today']=u.today()
        df_key['table_name']=table_name
        
        df_records = df_key[['today','table_name','key_rate','key_rows','rows']]
        
        if output_hosts=={}:
            logger.warning(f'output_hosts is not configed. Table "{output_table_name}" will not be recorded.')
            pass
        else:
            show_df = u.mysql_select("show tables", output_hosts)
            show_df.columns = ['tables']
            if output_table_name not in list(show_df['tables']):
                logger.warning(f'Table "{output_table_name}" is not exits. Now creating ……')
                u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='r')
                
            else:
                u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='a')  
        
        logger.info(f"\n\nsql select finished\n\n rows:{ df_key['rows'][0]}\n null_rows:{ df_key['key_rows'][0]}\n null_rate:{ df_key['key_rate'][0]}\n")
        try:
            result = df_key[output][0]
        except Exception as e:
            raise ValueError(f"{e}\nUnsupported output type. Only ('rows' or 'key_rows' or 'key_rate'")
            
        return result




def is_valid_time(time_str, time_format):
    from datetime import datetime
    try:
        datetime.strptime(time_str, time_format)
        return True
    except Exception as e:
        raise ValueError(f"{e}\nUnsupported time_str. Only %H:%M:%S")
        return False


def time_check(table_name,hosts,updated,where,time_rule = '09:00:00',output='time_score',output_hosts={},output_table_name = 'quality_check_records_time'):
    
    col_name = updated
    time_rule_check = is_valid_time(time_rule, "%H:%M:%S")
    logger.info(f"time_rule is valid ( {time_rule} ：{time_rule_check} )")
    
    time_limit = u.today()+' '+time_rule
    
    target_db_type = hosts['dbtype']
    
    if str(where) in ['-','','nan']:
        where = ''
        pass
    elif "where" not in where:
        where = f'where \n  {where}'
        
    if target_db_type == 'mysql':
        sql = f'''
        select 
            max({col_name}) as `update_time`,
            TIMESTAMPDIFF(SECOND, max({col_name}),'{time_limit}') as time_gap,
            if(TIMESTAMPDIFF(SECOND, max({col_name}),'{time_limit}')>=0,1,0) as time_score
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_time = u.mysql_select(sql, hosts)
        
    elif target_db_type == 'clickhouse':
        sql = f'''
        select 
            max({col_name}) as `update_time`,
            toUnixTimestamp('{time_limit}') - toUnixTimestamp(max({col_name})) as time_gap,
            if(toUnixTimestamp('{time_limit}') - toUnixTimestamp(max({col_name}))>=0,1,0) as time_score
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_time = u.clickhouse_select(sql, hosts)
        
    elif target_db_type == 'maxcompute':
        sql = f'''
        select 
            max({col_name}) as `update_time`,
            UNIX_TIMESTAMP('{time_limit}') - UNIX_TIMESTAMP(max({col_name}))  as time_gap,
            if(UNIX_TIMESTAMP('{time_limit}') - UNIX_TIMESTAMP(max({col_name}))>=0,1,0) as time_score
        FROM
        	`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_time = u.mc_select(sql, hosts)
    
    else:
        raise ValueError("Unsupported target database type.")
    
    
    # import pandas as pd 
    df_time['today']=u.today()
    df_time['table_name']=table_name
    df_time['time_rules']=time_limit
    
    df_records = df_time[['today','table_name','time_rules','update_time','time_gap','time_score']]
    
    if output_hosts=={}:
        logger.warning(f'output_hosts is not configed. Table "{output_table_name}" will not be recorded.')
        pass
    else:
        show_df = u.mysql_select("show tables", output_hosts)
        show_df.columns = ['tables']
        if output_table_name not in list(show_df['tables']):
            logger.warning(f'Table "{output_table_name}" is not exits. Now creating ……')
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='r')
            
        else:
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='a')  
    
    logger.info(f"\n\nsql select finished\n\n update_time:{ df_time['update_time'][0]}\n time_gap:{ df_time['time_gap'][0]}\n time_score:{ df_time['time_score'][0]}\n")
    try:
        result = df_time[output][0]
    except Exception as e:
        raise ValueError(f"{e}\nUnsupported output type. Only ('update_time' or 'time_gap' or 'time_score'")
        
    return result


def same_check(table_name ,hosts,sum_list,count_list,where,source_table_name,source_hosts,source_sum_list,source_count_list,source_where,output='same_rate',output_hosts={},output_table_name = 'quality_check_records_same'):
    
    
    if len(sum_list)==len(source_sum_list): 
        pass
    else:
        raise ValueError("\nSum_list is not same between 'sum_list' and 'source_sum_list'.")
    if len(count_list)==len(source_count_list):
        pass
    else:
        raise ValueError("\nCount_list is not same between 'count_list' and 'source_count_list'.")
    
    # ----------------------------------------------------   
    # target
    
    sum_sql_a = ''
    for sum_col in sum_list:
        
        sum_sql = f"            round(sum(`{sum_col}`)) as `{sum_col}`,\n"
        sum_sql_a = sum_sql_a + sum_sql
    
    count_sql_a = ''
    for count_col in count_list:
        if count_col == "*":
            count_sql = "            count(*) as `rows`,\n"
        else:
            count_sql = f"            count(`{count_col}`) as `{count_col}`,\n"
        count_sql_a = count_sql_a + count_sql
    
    if str(where) in ['-','','nan']:
        where = ''
        pass
    elif "where" not in where:
        where = f'where \n  {where}'
    

    target_db_type = hosts['dbtype']
    
    if target_db_type == 'mysql':
        sql = f'''
        select 
            '{table_name}' as `table_name`,{sum_sql_a}{count_sql_a}            '{hosts['db']}' as `db`,
            '{hosts['dbtype']}' as `dbtype`
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_target = u.mysql_select(sql, hosts)
        
    elif target_db_type == 'clickhouse':
        sql = f'''
        select 
            '{table_name}' as `table_name`,{sum_sql_a}{count_sql_a}            '{hosts['db']}' as `db`,
            '{hosts['dbtype']}' as `dbtype`
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_target = u.clickhouse_select(sql, hosts)
        
    elif target_db_type == 'maxcompute':
        sql = f'''
        select 
            '{table_name}' as `table_name`,{sum_sql_a}{count_sql_a}            '{hosts['project_name']}' as `db`,
            '{hosts['dbtype']}' as `dbtype`
        FROM
        	`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_target = u.mc_select(sql, hosts)
    
    else:
        raise ValueError("Unsupported target database type.")
    
    
    # ----------------------------------------------------   
    # source
    
    source_sum_sql_a = ''
    for i in range(len(sum_list)):
        
        source_sum_sql = f"            round(sum(`{source_sum_list[i]}`)) as `{sum_list[i]}`,\n"
        source_sum_sql_a = source_sum_sql_a + source_sum_sql
    
    source_count_sql_a = ''
    for j in range(len(count_list)):
        if count_list[j] == "*":
            source_count_sql = "            count(*) as `rows`,\n"
        else:
            source_count_sql = f"            count(`{source_count_list[j]}`) as `{count_list[j]}`,\n"
        source_count_sql_a = source_count_sql_a + source_count_sql
    
    if str(source_where) in ['-','','nan']:
        source_where = ''
        pass
    elif "where" not in source_where:
        source_where = f'where \n  {source_where}'
    
    source_db_type = source_hosts['dbtype']
    
    if source_db_type == 'mysql':
        sql = f'''
        select 
            '{source_table_name}' as `table_name`,{source_sum_sql_a}{source_count_sql_a}            '{source_hosts['db']}' as `db`,
            '{source_hosts['dbtype']}' as `dbtype`
        FROM
        	`{source_hosts['db']}`.`{source_table_name}` x
        {source_where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_source = u.mysql_select(sql, source_hosts)
        
    elif source_db_type == 'clickhouse':
        sql = f'''
        select 
            '{source_table_name}' as `table_name`,{source_sum_sql_a}{source_count_sql_a}            '{source_hosts['db']}' as `db`,
            '{source_hosts['dbtype']}' as `dbtype`
        FROM
        	`{source_hosts['db']}`.`{source_table_name}` x
        {source_where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_source = u.clickhouse_select(sql, source_hosts)
        
    elif source_db_type == 'maxcompute':
        sql = f'''
        select 
            '{source_table_name}' as `table_name`,{source_sum_sql_a}{source_count_sql_a}            '{source_hosts['project_name']}' as `db`,
            '{source_hosts['dbtype']}' as `dbtype`
        FROM
        	`{source_table_name}` x
        {source_where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_source = u.mc_select(sql, source_hosts)
    
    else:
        raise ValueError("Unsupported target database type.")
    
    import pandas as pd
    df_all = pd.concat([df_same_target, df_same_source], ignore_index=True)
    
    success_list = []
    fail_list = []
    success_dic = {'target': {},'source': {}}
    fail_dic = {'target': {},'source': {}}
    for m in range(len(sum_list)):
        target = int(df_all[sum_list[m]][0])
        source = int(df_all[sum_list[m]][1])
        if target == source:
            success_list.append(sum_list[m])
            success_dic['target'][sum_list[m]] = target
            success_dic['source'][sum_list[m]] = source
        else:
            fail_list.append(sum_list[m])
            fail_dic['target'][sum_list[m]] = target
            fail_dic['source'][sum_list[m]] = source
        
    for n in range(len(count_list)):
        if count_list[n] == "*":
            col = 'rows'
        else:
            col = count_list[n]
        target = df_all[col][0]
        source = df_all[col][1]
        if target == source:
            success_list.append(col)
            success_dic['target'][col] = target
            success_dic['source'][col] = source
        else:
            fail_list.append(col)
            fail_dic['target'][col] = target
            fail_dic['source'][col] = source
    
        
    same_rate = len(success_list)/(len(success_list)+len(fail_list))
    result_list = {'success_dic':success_dic,'fail_dic':fail_dic,'same_rate':same_rate}
        
    logger.info(f"\n\nsql select finished\n\n success_dic:{success_dic}\n fail_dic:{fail_dic}\n same_rate:{same_rate}\n")
    

    count_col_list = []
    for n in range(len(count_list)):
        if count_list[n] == "*":
            col = 'rows'
        else:
            col = count_list[n]
        count_col_list.append(col)
    id_vars=['table_name', 'db', 'dbtype']
    value_vars=sum_list+count_col_list
    var_name='items'
    value_name='value'
    
    melted_df = pd.melt(df_all, id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name)
    
    melted_df['check_table'] = table_name
    melted_df['item_type'] = None
    melted_df['source'] = None
    for i in range(len(melted_df)):
        if melted_df['table_name'][i] == table_name:
            melted_df['source'][i] = source_table_name
        if melted_df['items'][i] in sum_list:
            melted_df['item_type'][i] = 'sum'
        elif melted_df['items'][i] in count_list or melted_df['items'][i]=='rows':
            melted_df['item_type'][i] = 'count'
    melted_df['today'] = u.today()
    col_sort = ['today','check_table','table_name','db','dbtype','items','value','item_type','source']
    df_fianl = melted_df[col_sort]
    
    if output_hosts=={}:
        logger.warning(f'output_hosts is not configed. Table "{output_table_name}" will not be recorded.')
        pass
    else:
        show_df = u.mysql_select("show tables", output_hosts)
        show_df.columns = ['tables']
        if output_table_name not in list(show_df['tables']):
            logger.warning(f'Table "{output_table_name}" is not exits. Now creating ……')
            u.mysql_write(df_fianl,output_table_name,update = True,hosts = output_hosts,wtype='r')
            
        else:
            u.mysql_write(df_fianl,output_table_name,update = True,hosts = output_hosts,wtype='a')
    try:
        result = result_list[output]
    except Exception as e:
        raise ValueError(f"{e}\nUnsupported output type. Only ('success_dic' or 'fail_dic' or 'same_rate'")
    return result




def validity_check(table_name,hosts,where,standard_dic,sum_list,count_list,output='validity_score',output_hosts = {},output_table_name='quality_check_records_validity'):   
    
    # standard_dic = {
    #         'sales':[0,50000000],
    #         'rows':[0,50000000]
    #     }
    total_list = sum_list+count_list
    for j in range(len(total_list)):
        if total_list[j] == '*':
            total_list[j] = 'rows'
    for i in standard_dic:
        if i in total_list:
            pass
        else:
            raise ValueError(f"\nThe {i} in standard_dic is not in 'sum_list' or 'count_list'.")
            
    
    
    # if len(sum_list)+len(count_list)==len(standard_dic): 
    #     pass
    # else:
    #     raise ValueError("\nThe length is not same between ('sum_list'+'count_list' and 'standard_dic'.")
    
    # ----------------------------------------------------   
    # target
    
    sum_sql_a = ''
    for sum_col in sum_list:
        
        sum_sql = f"            round(sum(`{sum_col}`)) as `{sum_col}`,\n"
        sum_sql_a = sum_sql_a + sum_sql
    
    count_sql_a = ''
    for count_col in count_list:
        if count_col == "*":
            count_sql = "            count(*) as `rows`,\n"
        else:
            count_sql = f"            count(`{count_col}`) as `{count_col}`,\n"
        count_sql_a = count_sql_a + count_sql
    
    
    target_db_type = hosts['dbtype']
    
    if str(where) in ['-','','nan']:
        where = ''
        pass
    elif "where" not in where:
        where = f'where \n  {where}'
        
    if target_db_type == 'mysql':
        sql = f'''
        select 
            '{table_name}' as `table_name`,{sum_sql_a}{count_sql_a}            '{hosts['db']}' as `db`,
            '{hosts['dbtype']}' as `dbtype`
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_target = u.mysql_select(sql, hosts)
        
    elif target_db_type == 'clickhouse':
        sql = f'''
        select 
            '{table_name}' as `table_name`,{sum_sql_a}{count_sql_a}            '{hosts['db']}' as `db`,
            '{hosts['dbtype']}' as `dbtype`
        FROM
        	`{hosts['db']}`.`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_target = u.clickhouse_select(sql, hosts)
        
    elif target_db_type == 'maxcompute':
        sql = f'''
        select 
            '{table_name}' as `table_name`,{sum_sql_a}{count_sql_a}            '{hosts['project_name']}' as `db`,
            '{hosts['dbtype']}' as `dbtype`
        FROM
        	`{table_name}` x
        {where}
        '''
        logger.info(f'sql generating …… \n\n {sql} \n\n')
        logger.info('sql selecting')

        df_same_target = u.mc_select(sql, hosts)
    
    else:
        raise ValueError("Unsupported target database type.")
    
    result_dic = {}
    success_dic = {}
    fail_dic = {}
    result_detail = []
    for i in standard_dic:
        value = int(df_same_target[i][0])
        standard = standard_dic[i]
        if value>=standard[0] and value<=standard[1]:
            score = 1
            success_dic[i] = {"value":value,'standard':standard,'score':score}
        else:
            score = 0
            fail_dic[i] = {"value":value,'standard':standard,'score':score}
        logger.info(f"\n'{i}':{value} —— 'standard':{standard} —— 'score':{score}")
        result_detail.append({'column':i,'value':value,'standard':standard,'score':score})
        result_dic[i] = score
    
    sum_score =0
    for i in result_dic:
        sum_score = sum_score + result_dic[i]
    validity_score = sum_score/len(result_dic)
    logger.info(f"\n'sum_score':{sum_score} \n'len':{len(result_dic)} \n'validity_score':{validity_score}")
    
    import pandas as pd
    records_dic = {
        'today':u.today(),
        'sum_score':sum_score,
                   'len':len(result_dic),
                   'validity_score':validity_score,
                   'result_dic':str(result_dic),
                   'result_detail':str(result_detail)
                   }
    df_records = pd.DataFrame([records_dic])
    
    if output_hosts=={}:
        logger.warning(f'output_hosts is not configed. Table "{output_table_name}" will not be recorded.')
        pass
    else:
        show_df = u.mysql_select("show tables", output_hosts)
        show_df.columns = ['tables']
        if output_table_name not in list(show_df['tables']):
            logger.warning(f'Table "{output_table_name}" is not exits. Now creating ……')
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='r')
            
        else:
            u.mysql_write(df_records, output_table_name,update=True,hosts=output_hosts,wtype='a')
    
    
    output_dic = {'success_dic':success_dic,'fail_dic':fail_dic,'validity_score':validity_score}
    try:
        result = output_dic[output]
    except Exception as e:
        raise ValueError(f"{e}\nUnsupported output type. Only ('success_dic' or 'fail_dic' or 'validity_score'")
        
    return result           
        
    

def quality_check(table_name,hosts,sum_list,count_list,where,key,time_rule,updated,standard_dic,source_table_name,source_hosts,source_sum_list,source_count_list,source_where,output_hosts):

    import pandas as pd

    # 完备性验证：非null值占比
    integrity_rate = integrity_check(table_name,hosts,where,output='integrity_rate',output_hosts = output_hosts)
    
    # 唯一性验证：主键非重复记录比例
    key_rate = key_check(table_name,hosts,key=key,where = where,output='key_rate',output_hosts = output_hosts)
    
    # 及时性验证：更新时间是否满足要求
    time_score = time_check(table_name,hosts,updated,where,time_rule,output='time_score',output_hosts = output_hosts)
    
    # 一致性验证
    same_rate = same_check(table_name ,hosts,sum_list,count_list,where,source_table_name,source_hosts,source_sum_list,source_count_list,source_where,output='same_rate',output_hosts = output_hosts)
    
    # 有效性验证
    validity_score = validity_check(table_name, hosts,where, standard_dic, sum_list, count_list,output='validity_score',output_hosts = output_hosts)
    
    
    total_score = integrity_rate+key_rate+time_score+same_rate+validity_score
    
    dbtype = hosts['dbtype']
    if dbtype == 'maxcompute': 
        db = hosts['project_name']
    else:
        db = hosts['db']
        
    source_dbtype = source_hosts['dbtype']
    if source_dbtype == 'maxcompute': 
        source_db = source_hosts['project_name']
    else:
        source_db = source_hosts['db']
        
    check_result = {
        'today':u.today(),
        'table_name':table_name,
        'db':db,
        'dbtype':hosts['dbtype'],
        'total_score':total_score,
        'integrity_rate':integrity_rate,
        'key_rate':key_rate,
        'time_score':time_score,
        'same_rate':same_rate,
        'validity_score':validity_score,
        'source_table_name':source_table_name,
        'source_db':source_db,
        'source_dbtype':source_dbtype
        }
    df_records = pd.DataFrame([check_result])
    output_table_name = 'quality_check_records'
    
    
    quality_check_records(df_records,output_table_name,output_hosts)
    return df_records    