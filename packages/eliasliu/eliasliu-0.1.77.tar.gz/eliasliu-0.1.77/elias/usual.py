# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 00:01:46 2022

def list :

Part 0 all_hosts
    0.1 bs_%：黑鲨科技
    0.2 gd_%：高灯科技
    0.3 kk_%：自购阿里云
    
Part 1 change date & time
    1.1 Stamp_to_Datetime：默认当前日期时间 1655137843 -->'2022-06-14 00:31:46'
    1.2 Stamp_to_Date：默认当前日期 1655137843 -->'2022-06-14'
    1.3 Stamp_to_Hour：默认当前时间 1655137843 -->'00:29:52'
    1.4 unix_time：无默认，日期时间（str）--> 时间戳
    1.5 local_time：无默认，时间戳 --> 日期时间（str）
    1.6 to_hour：秒-->时分秒  5000 --> '01:23:20'
    1.7 today_add：n --> 今天增加n天后日期（str/datetime）
    1.8 datediff：返回日期间隔天数
    1.9 today：返回今天（str/datetime）
    1.10 yestoday：返回昨天（str/datetime）
    1.11 date_add：默认今天，date&n --> date 增加 n天后日期（str/datetime）
    1.12 timeStamp：默认今天，日期时间（str）--> 时间戳
    1.13 thismonth：返回当月月份
    1.14 this_month：返回当月始末日期
    1.15 last_month：返回上月始末日期——上个月的月初和月末（list类型）（三种格式：时间字符串、时间数组、时间戳）{'s':'时间字符串','timeArray':'时间数组','timeStamp':'时间戳'}
    1.16 last_week：返回上周每一天（列表）
    1.17 this_week：返回本周每一天（列表）
    1.18 Datetime_now：返回当前日期时间（Example:2022-7-15 22:20:05）
    1.19 Date_now: 返回当前日期（Example:2022-7-15）
    
Part 2 send_file
    2.1 df_send_file：从DataFrame，发送excel文件企微机器人
    2.2 sql_send_file：从sql查询数据库，将查询结果打包excel，发送企微机器人
    
Part 3 connect database    
    3.1 mysql_write：写入数据库
    3.2 mysql_select：查询数据库
    3.3 mysql_ddl：修改数据库（DDL）
    3.4 py_impala
    3.5 py_hive
    3.6 bs_impala
    3.7 sqlserver_select：输入sql查询，返回dataframe
    3.8 sqlserver_select_table：输入表名，整表查询，返回dataframe
    3.9 sqlserver_select_columns：输出字段名，str类型
    3.10 sqlserver_select_table_fixed：执行给定的SQL语句，解决中文乱码的问题
    3.11 clickhouse_select:clickhouse查询，返回DataFrame
    
Part 4 send Email
    4.1 Email_send：发送邮件
    4.2 Email_warn：用邮件发送警告模板
    
Part 5 spyder
    5.1 weather：爬取今日天气
    5.2 video_get：通过url视频获取，最小代码单元，仅用于测试
    5.3 url_request：通过url获取网页源码
    
Part 6 decode & encode
    6.1 url_encode：str --> url编码 ('中国' --> '%E4%B8%AD%E5%9B%BD')
    6.2 decode：'中国' --> '\\u4e2d\\u56fd'
    6.3 url_decode：url编码 --> str ('%E4%B8%AD%E5%9B%BD' --> '中国')
    
Part 7 system environment
    7.1 list_all_files：列出来当前目录下，所有的文件和文件夹
    7.2 to_txt：str写入txt
    7.3 file_get：从路径获取文件名（包含文件类型）
    7.4 filename_get：从路径获取文件名（不包含文件类型）
    7.5 zip_path：压缩文件夹，手动输入源路径和目标路径&文件名，无输出return
    7.6 zip_file：压缩文件夹，自动在上级目录创建文件，输出压缩文件路径
    7.7 desktop_path：获取桌面路径
    7.8 change_language：切换输入法
    7.9 name_to_html：文件名转换为html，用于网页另存为
    7.10 file_exists_rename：检测文件是否存在，如果存在重命名（在最后添加序号）
    7.11 file_path_fill：为文件名补全路径
    7.12 get_clipboard：读取剪贴板的数据
    7.13 set_clipboard：写入剪贴板数据
    7.14 save_html：系统控制浏览器打开网页，并保存到相应文件
    7.15 windows_items_find：遍历windows下 所有句柄及窗口名称
    7.16 title_verify_slide：根据title进行滑动验证判断
    7.17 get_ip：获取本机局域网ip
    7.18 get_out_ip：获取本机公网ip
    7.19 get_elias_path：获取本机elias代码仓库路径
    7.20 get_mission_list：获取本机elias代码仓库中，missions中所有mission_run脚本路径
    7.21 all_mission_doing：执行7.20获取的所有脚本（本机elias代码仓库中，missions中所有mission_run脚本路径）

# Part 8 DataFrame dealing
    8.1 py_mission_records:任务执行信息生成，存入阿里云records
    8.2 py_mission_robot_message：任务执行情况，机器人推送信息生成（不包含推送）
    
# Part 9 Str dealing
    9.1 find_chinese:从字符串中提取中文字符

@author: yiting.liu
"""


from elias import config_env_variable as ev
from loguru import logger
try:
    config_path = ev.environ_get()
    config = ev.elias_config()
    print('elias_config配置导入成功')
except:
    logger.warning('elias_config环境变量导入失败！请检查elias_config是否配置，如果已经配置完成。请重启后再试。')
    


# Part 0 all_hosts
# ====================================================================================
def log_path(logname = ''):
    # from elias import config
    import os
    
    folder_path = config.log_path
    
    if folder_path == '':
        package_file = config_path
        folder_path =  os.path.join(package_file, 'log')
        
    # 使用os模块创建文件夹
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    import os
    if logname == '': 
        logname = 'app.log'
    else:
        logname = logname + '.log'
        
    path = os.path.join(folder_path, logname)
    return path

def all_hosts(name = 'all'):#公司_数据库
    all_hosts = config.hosts
    if name == 'all':
        hosts = list(all_hosts)
    else:
        hosts = all_hosts[name]
    return hosts

def mysql_con(host_name, charset='utf8'):
    import pymysql
    host = all_hosts(host_name)['host']
    port = int(all_hosts(host_name)['port'])
    name = all_hosts(host_name)['user']
    code = all_hosts(host_name)['code']
    db = all_hosts(host_name)['db']
    if charset == '':
        connection = pymysql.connect(host=host, port=port, database=db, user=name, password=code, cursorclass=pymysql.cursors.SSDictCursor)
    else:
        connection = pymysql.connect(host=host, port=port, database=db, user=name, password=code, charset=charset, cursorclass=pymysql.cursors.SSDictCursor)
    return connection

def sqlserver_con(host_name,charset='utf8',as_dict=False):
    import pymssql
    config_dict = all_hosts(name = host_name)
    connection=pymssql.connect(**config_dict,charset=charset,as_dict=as_dict)
    return connection


# Part 1 change date & time
# ====================================================================================

import datetime
import time


# 1.1
def Stamp_to_Datetime(timeStamp = int(time.time())):
    import time
    timeArray = time.localtime(timeStamp)
    DateTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    # print(DateTime)
    return DateTime

# 1.2
def Stamp_to_Date(timeStamp = int(time.time())):
    import time
    timeArray = time.localtime(timeStamp)
    DateTime = time.strftime("%Y-%m-%d", timeArray)
    # print(DateTime)
    return DateTime

# 1.3
def Stamp_to_Hour(timeStamp = int(time.time())):
    import time
    timeArray = time.localtime(timeStamp)
    DateTime = time.strftime("%H:%M:%S", timeArray)
    # print(DateTime)
    return DateTime

# 1.4
def unix_time(dt):# 时间-->时间戳
     #转换成时间数组
     timeArray = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
     #转换成时间戳
     timestamp = time.mktime(timeArray)
     return timestamp

# 1.5   
def local_time(timestamp):# 时间戳-->时间
     #转换成localtime
     time_local = time.localtime(timestamp)
     #转换成新的时间格式(2016-05-05 20:28:54)
     dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
     return dt

# 1.6     
def to_hour(n=0):
    import datetime
    result = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    a = result + datetime.timedelta(seconds=n)
    return a.strftime("%H:%M:%S")
    
# 1.7
def today_add(n='str',day = 0):
    import datetime
    result_y = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    result = result_y + datetime.timedelta(days=day)
    list_t = {'datetime':result,'str':result.strftime("%Y-%m-%d")}
    return list_t[n]

# 1.8
def datediff(date1,date2):
    import datetime
    #%Y-%m-%d为日期格式，其中的-可以用其他代替或者不写，但是要统一，同理后面的时分秒也一样；可以只计算日期，不计算时间。
    #date1=time.strptime(date1,"%Y-%m-%d %H:%M:%S")
    #date2=time.strptime(date2,"%Y-%m-%d %H:%M:%S")
    
    date1=time.strptime(date1,"%Y-%m-%d")
    date2=time.strptime(date2,"%Y-%m-%d")
    
    #根据上面需要计算日期还是日期时间，来确定需要几个数组段。下标0表示年，小标1表示月，依次类推...
    #date1=datetime.datetime(date1[0],date1[1],date1[2],date1[3],date1[4],date1[5])
    #date2=datetime.datetime(date2[0],date2[1],date2[2],date2[3],date2[4],date2[5])
    
    date1=datetime.datetime(date1[0],date1[1],date1[2])
    date2=datetime.datetime(date2[0],date2[1],date2[2])
    
    #返回两个变量相差的值，就是相差天数
    delta = (date2-date1).days
    return delta

# 1.9
def today(n='str'):
    import datetime
    result = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    list_t = {'datetime':result,'str':result.strftime("%Y-%m-%d")}
    return list_t[n]

# 1.10
def yesterday(n='str'):
    import datetime
    result = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    result_y = result - datetime.timedelta(days=1)
    list_y = {'datetime':result_y,'str':result_y.strftime("%Y-%m-%d")}
    return list_y[n]

# 1.10
def yestoday(n='str'):
    import datetime
    result = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    result_y = result - datetime.timedelta(days=1)
    list_y = {'datetime':result_y,'str':result_y.strftime("%Y-%m-%d")}
    return list_y[n]

# 1.11
def date_add(date = today(),day = 0,n='str'):
    import datetime
    # year = int(date[:4])
    # month = int(date[5:7])
    # day = int(date[8:])
    result_y = datetime.datetime.now().replace(year= int(date[:4]) ,month = int(date[5:7]),day = int(date[8:]),hour=0, minute=0, second=0, microsecond=0)
    result = result_y + datetime.timedelta(days=day)
    list_t = {'datetime':result,'str':result.strftime("%Y-%m-%d")}
    return list_t[n]

# 1.12
def timeStamp(date = today()):
    import datetime
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        timeArray_date = time.strptime(date, "%Y-%m-%d")
        timeStamp_date = int(time.mktime(timeArray_date))
    except:
        date = today.strftime("%Y-%m-%d")
        timeArray_date = time.strptime(date, "%Y-%m-%d")
        timeStamp_date = int(time.mktime(timeArray_date))
        print("日期异常,默认返回当日时间戳！\n如果有误，请输入 '%Y-%m-%d'格式！！！")
    return timeStamp_date

# 1.13
def thismonth(n = 's',end = 'today'): 
    import datetime
    # 获取本月
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    s_month = today.strftime("%Y-%m")
    return s_month

# 1.14
def this_month(n = 's',end = 'today'): 
    import datetime
    # 获取本月日期
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.datetime.now().replace(month=today.month,day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = datetime.datetime.now().replace(month=today.month+1,day=1, hour=0, minute=0, second=0, microsecond=0)
    if end == 'today':
        month_end = today
    elif end == 'yesterday':
        month_end = yesterday(n='datetime')
    else:
        month_end = next_month - datetime.timedelta(days=1)
    
    s_month_start = month_start.strftime("%Y-%m-%d")
    timeArray_month_start = time.strptime(s_month_start, "%Y-%m-%d")
    timeStamp_month_start = int(time.mktime(timeArray_month_start))
    
    s_month_end = month_end.strftime("%Y-%m-%d")
    timeArray_month_end = time.strptime(s_month_end, "%Y-%m-%d")
    timeStamp_month_end = int(time.mktime(timeArray_month_end))
    
    if n == 's':
        return [s_month_start,s_month_end]
    elif n == 'timeArray':
        return [timeArray_month_start,timeArray_month_end]
    elif n == 'timeStamp':
        return [timeStamp_month_start,timeStamp_month_end]
    else:
        print("参数不完整：需要填写{'s':'时间字符串','timeArray':'时间数组','timeStamp':'时间戳'} \n 默认调用 's':'时间字符串'，如有异常，请重新调用 ")
        return [s_month_start,s_month_end]

# 1.15  
def last_month(n = 's'): 
    import datetime
    # 获取本月日期
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.datetime.now().replace(month=today.month-1,day=1, hour=0, minute=0, second=0, microsecond=0)
    thismonth = datetime.datetime.now().replace(month=today.month,day=1,hour=0, minute=0, second=0, microsecond=0)
    month_end = thismonth - datetime.timedelta(days=1)
    
    s_month_start = month_start.strftime("%Y-%m-%d")
    timeArray_month_start = time.strptime(s_month_start, "%Y-%m-%d")
    timeStamp_month_start = int(time.mktime(timeArray_month_start))
    
    s_month_end = month_end.strftime("%Y-%m-%d")
    timeArray_month_end = time.strptime(s_month_end, "%Y-%m-%d")
    timeStamp_month_end = int(time.mktime(timeArray_month_end))
    
    if n == 's':
        return [s_month_start,s_month_end]
    elif n == 'timeArray':
        return [timeArray_month_start,timeArray_month_end]
    elif n == 'timeStamp':
        return [timeStamp_month_start,timeStamp_month_end]
    else:
        print("参数不完整：需要填写{'s':'时间字符串','timeArray':'时间数组','timeStamp':'时间戳'} \n 默认调用 's':'时间字符串'，如有异常，请重新调用 ")
        return [s_month_start,s_month_end]

# last_month(n='timeArray')
 
# 1.16
def last_week(n = 's'):
    import datetime
    # 获取本周日期
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    monday = today - datetime.timedelta(days=today.weekday()) - datetime.timedelta(days=7)
    tuesday = monday + datetime.timedelta(days=1)
    wednesday = monday + datetime.timedelta(days=2)
    thursday = monday + datetime.timedelta(days=3)
    friday = monday + datetime.timedelta(days=4)
    saturday = monday + datetime.timedelta(days=5)
    sunday = monday + datetime.timedelta(days=6)

    s_monday = monday.strftime("%Y-%m-%d")
    s_tuesday = tuesday.strftime("%Y-%m-%d")
    s_wednesday = wednesday.strftime("%Y-%m-%d")
    s_thursday = thursday.strftime("%Y-%m-%d")
    s_friday = friday.strftime("%Y-%m-%d")
    s_saturday = saturday.strftime("%Y-%m-%d")
    s_sunday = sunday.strftime("%Y-%m-%d")
    
    timeArray_monday = time.strptime(s_monday, "%Y-%m-%d")
    timeArray_tuesday = time.strptime(s_tuesday, "%Y-%m-%d")
    timeArray_wednesday = time.strptime(s_wednesday, "%Y-%m-%d")
    timeArray_thursday = time.strptime(s_thursday, "%Y-%m-%d")
    timeArray_friday = time.strptime(s_friday, "%Y-%m-%d")
    timeArray_saturday = time.strptime(s_saturday, "%Y-%m-%d")
    timeArray_sunday = time.strptime(s_sunday, "%Y-%m-%d")
    
    timeStamp_monday = int(time.mktime(timeArray_monday))
    timeStamp_tuesday = int(time.mktime(timeArray_tuesday))
    timeStamp_wednesday = int(time.mktime(timeArray_wednesday))
    timeStamp_thursday = int(time.mktime(timeArray_thursday))
    timeStamp_friday = int(time.mktime(timeArray_friday))
    timeStamp_saturday = int(time.mktime(timeArray_saturday))
    timeStamp_sunday = int(time.mktime(timeArray_sunday))
    week_list = [s_monday,s_tuesday,s_wednesday,s_thursday,s_friday,s_saturday,s_sunday]
    
    if n == 's':
        week_list = [s_monday,s_tuesday,s_wednesday,s_thursday,s_friday,s_saturday,s_sunday]
    elif n == 'timeArray':
        week_list = [timeArray_monday,timeArray_tuesday,timeArray_wednesday,timeArray_thursday,timeArray_friday,timeArray_saturday,timeArray_sunday]
    elif n == 'timeStamp':
        week_list = [timeStamp_monday,timeStamp_tuesday,timeStamp_wednesday,timeStamp_thursday,timeStamp_friday,timeStamp_saturday,timeStamp_sunday]
    else:
        print("参数不完整：需要填写{'s':'时间字符串','timeArray':'时间数组','timeStamp':'时间戳' \n 默认调用 's':'时间字符串'，如有异常，请重新调用 }")
        week_list = [s_monday,s_tuesday,s_wednesday,s_thursday,s_friday,s_saturday,s_sunday]
    return week_list

# 1.17
def this_week(n = 's'):
    # 获取本周日期
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    monday = today - datetime.timedelta(days=today.weekday())
    tuesday = monday + datetime.timedelta(days=1)
    wednesday = monday + datetime.timedelta(days=2)
    thursday = monday + datetime.timedelta(days=3)
    friday = monday + datetime.timedelta(days=4)
    saturday = monday + datetime.timedelta(days=5)
    sunday = monday + datetime.timedelta(days=6)

    s_monday = monday.strftime("%Y-%m-%d")
    s_tuesday = tuesday.strftime("%Y-%m-%d")
    s_wednesday = wednesday.strftime("%Y-%m-%d")
    s_thursday = thursday.strftime("%Y-%m-%d")
    s_friday = friday.strftime("%Y-%m-%d")
    s_saturday = saturday.strftime("%Y-%m-%d")
    s_sunday = sunday.strftime("%Y-%m-%d")
    
    timeArray_monday = time.strptime(s_monday, "%Y-%m-%d")
    timeArray_tuesday = time.strptime(s_tuesday, "%Y-%m-%d")
    timeArray_wednesday = time.strptime(s_wednesday, "%Y-%m-%d")
    timeArray_thursday = time.strptime(s_thursday, "%Y-%m-%d")
    timeArray_friday = time.strptime(s_friday, "%Y-%m-%d")
    timeArray_saturday = time.strptime(s_saturday, "%Y-%m-%d")
    timeArray_sunday = time.strptime(s_sunday, "%Y-%m-%d")
    
    timeStamp_monday = int(time.mktime(timeArray_monday))
    timeStamp_tuesday = int(time.mktime(timeArray_tuesday))
    timeStamp_wednesday = int(time.mktime(timeArray_wednesday))
    timeStamp_thursday = int(time.mktime(timeArray_thursday))
    timeStamp_friday = int(time.mktime(timeArray_friday))
    timeStamp_saturday = int(time.mktime(timeArray_saturday))
    timeStamp_sunday = int(time.mktime(timeArray_sunday))
    week_list = [s_monday,s_tuesday,s_wednesday,s_thursday,s_friday,s_saturday,s_sunday]
    
    if n == 's':
        week_list = [s_monday,s_tuesday,s_wednesday,s_thursday,s_friday,s_saturday,s_sunday]
    elif n == 'timeArray':
        week_list = [timeArray_monday,timeArray_tuesday,timeArray_wednesday,timeArray_thursday,timeArray_friday,timeArray_saturday,timeArray_sunday]
    elif n == 'timeStamp':
        week_list = [timeStamp_monday,timeStamp_tuesday,timeStamp_wednesday,timeStamp_thursday,timeStamp_friday,timeStamp_saturday,timeStamp_sunday]
    else:
        print("参数不完整：需要填写{'s':'时间字符串','timeArray':'时间数组','timeStamp':'时间戳' \n 默认调用 's':'时间字符串'，如有异常，请重新调用 }")
        week_list = [s_monday,s_tuesday,s_wednesday,s_thursday,s_friday,s_saturday,s_sunday]
    return week_list

# 1.18
def Datetime_now(t = 0):
    if t==1:
        return time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
    elif t==2:
        return time.strftime("%Y-%m-%d", time.localtime(time.time()))
    else:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

# 1.19
def Date_now():
    return time.strftime("%Y-%m-%d", time.localtime(time.time()))

# 1.20
def get_days_in_month(year, month):
    import calendar
    # 使用calendar模块的monthrange函数获取该月的第一天是星期几和该月的天数
    first_day_of_month, days_in_month = calendar.monthrange(year, month)
    return days_in_month

# 1.21
def date_check(date):
    date_list = date.split('-')
    if len(date_list)!=3:
        # logger.warning('日期格式不正确，请输入正确的日期')
        raise ValueError('日期格式不正确，请输入正确的日期')
    for i in range(len(date_list)):
        try:
            a = int(date_list[i])
            if i == 0:
                if a>=1900 and a<=2050:
                    year = a
                    pass
                else:
                    raise ValueError('Year is not in the right range: [ 1900,2500 ]')
            elif i==1:
                if a>=1 and a<=12:
                    month = a
                    pass
                else:
                    raise ValueError('Month is not in the right range: [ 1900,2500 ]')
            elif i==2:
                max_days = get_days_in_month(year, month)
                if a>=1 and a<=max_days:
                    pass
                else:
                    raise ValueError('Day is not in the right range: [ 1900,2500 ]')
        except:
            raise ValueError('年月日格式不正确，请输入正确的年月日')
    return True


def get_year(date,dtype = 'str'):
    if date_check(date): 
        date_list = date.split('-')
        if dtype == 'str':
            return date_list[0]
        elif dtype == 'int':
            return int(date_list[0])
        else:
            raise ValueError('参数dtype不正确，请输入 “str” 或 “int” ')

def get_month(date,dtype = 'str'):
    if date_check(date): 
        date_list = date.split('-')
        if dtype == 'str':
            return date_list[1]
        elif dtype == 'int':
            return int(date_list[1])
        else:
            raise ValueError('参数dtype不正确，请输入 “str” 或 “int” ')

def get_day(date,dtype = 'str'):
    if date_check(date): 
        date_list = date.split('-')
        if dtype == 'str':
            return date_list[2]
        elif dtype == 'int':
            return int(date_list[2])
        else:
            raise ValueError('参数dtype不正确，请输入 “str” 或 “int” ')

def month_start(date=today()):
    if date_check(date):             
        return date[:7]+"-01"
    
def month_end(date=today()):
    if date_check(date): 
        year = get_year(date,dtype = 'int')
        month = get_month(date,dtype = 'int')
        day = get_days_in_month(year, month)
        if day>=10:
            return date[:7]+f"-{str(day)}"
        else:
            return date[:7]+f"-0{str(day)}"


def normalize_date(date_str, region='US'):
    """
    将各种格式的日期标准化为 YYYY-MM-DD 格式
    
    参数:
        date_str: 要转换的日期字符串
        region: 地区选项，'US'表示月/日/年，'EU'表示日/月/年

    测试示例：
        print(normalize_date('05/06/2023', 'US'))  # 美国格式: 月/日/年 → 2023-05-06
        print(normalize_date('06/05/2023', 'US'))  # 美国格式: 月/日/年 → 2023-06-05
        print(normalize_date('05/06/2023', 'EU'))  # 欧洲格式: 日/月/年 → 2023-06-05
        print(normalize_date('06/05/2023', 'EU'))  # 欧洲格式: 日/月/年 → 2023-05-06
        print(normalize_date('05/06'))      # 简写格式 → 当前年的5月6日
        print(normalize_date('10月8日'))    # 中文格式 → 当前年的10月8日
        print(normalize_date('2023年5月6日'))  # 中文完整格式 → 2023-05-06
    """
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    try:
        # 处理"昨天"
        if date_str == '昨天':
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 处理中文格式
        if '月' in date_str and '日' in date_str:
            if '年' in date_str:
                year = int(date_str.split('年')[0])
                month = int(date_str.split('年')[1].split('月')[0])
                day = int(date_str.split('月')[1].replace('日', ''))
            else:
                month = int(date_str.split('月')[0])
                day = int(date_str.split('月')[1].replace('日', ''))
                year = today.year
                if datetime(year, month, day).date() > today:
                    year -= 1
            return f"{year}-{month:02d}-{day:02d}"
        
        # 处理带分隔符的格式
        if any(sep in date_str for sep in ('/', '-', '.')):
            parts = [p for p in date_str.replace('-', '/').replace('.', '/').split('/') if p]
            
            # 只有月和日 (05/06)
            if len(parts) == 2:
                month = int(parts[0])
                day = int(parts[1])
                year = today.year
                if datetime(year, month, day).date() > today:
                    year -= 1
                return f"{year}-{month:02d}-{day:02d}"
            
            # 完整日期 (05/06/2023)
            elif len(parts) == 3:
                # 根据地区决定顺序
                if region.upper() == 'US':  # 月/日/年
                    month, day, year = map(int, parts)
                else:  # 日/月/年
                    day, month, year = map(int, parts)
                
                # 处理两位数的年份
                if year < 100:
                    current_century = today.year // 100 * 100
                    year += current_century
                    if year > today.year + 20:  # 如果超过当前年份20年，则认为是上世纪的
                        year -= 100
                
                return f"{year}-{month:02d}-{day:02d}"
        
        # 尝试解析其他常见格式
        for fmt in ('%Y-%m-%d', '%Y%m%d', '%Y.%m.%d'):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return date_str
    
    except Exception:
        return date_str

# # 测试示例
# print(normalize_date('05/06/2023', 'US'))  # 美国格式: 月/日/年 → 2023-05-06
# print(normalize_date('06/05/2023', 'US'))  # 美国格式: 月/日/年 → 2023-06-05
# print(normalize_date('05/06/2023', 'EU'))  # 欧洲格式: 日/月/年 → 2023-06-05
# print(normalize_date('06/05/2023', 'EU'))  # 欧洲格式: 日/月/年 → 2023-05-06
# print(normalize_date('05/06'))      # 简写格式 → 当前年的5月6日
# print(normalize_date('10月8日'))    # 中文格式 → 当前年的10月8日
# print(normalize_date('2023年5月6日'))  # 中文完整格式 → 2023-05-06




# ================================================================================




# Part 2 send_file
# ================================================================================

# 2.1
def df_send_file(df,fname = 'test',key = ''):
    from elias import wechat as w
    df.to_excel(fname+'.xlsx',index=False)
    w.wechat_file(file_path = fname+'.xlsx',key=key)
    
# 2.2
def sql_send_file(sql,hosts,server_type = 'mysql',fname = 'test',key = '',host_record = all_hosts(name = 'records')):
    # from elias import usual as u  
    import os  
    import datetime
    import time
    import pandas as pd
    from elias import wechat as w
    start = time.time()
  
    output_user = os.getlogin()
    output_outer_ip = get_out_ip()
    output_internal_ip = get_ip()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if server_type == 'mysql':
        print(' \n------- mysql --------\n')
        df = mysql_select(sql, hosts)
        h = hosts['host']
        p = hosts['port']
        n = hosts['user']
        c = hosts['code']
        d = hosts['db']
    elif server_type == 'impala':
        print(' \n----- impala sql -----\n')
        df = py_impala(sql, warn=True, num=1, sleeps=3, title='') 
        h,p,n,c,d=None,None,None,None,None
    elif server_type == 'hive':
        print(' \n------ hive sql ------\n')
        df = py_hive(sql, warn=True, num=1, sleeps=3, title='')
        h,p,n,c,d=None,None,None,None,None
    elif server_type == 'clickhouse':
        print(' \n------ clickhouse sql ------\n')
        df = clickhouse_select(sql = sql,hosts = hosts)
        h = hosts['host']
        p = hosts['port']
        n = hosts['user']
        c = hosts['code']
        d = hosts['db']
    time.sleep(2)
    df.to_excel(fname+'.xlsx',index=False)
    end = time.time()
    usetime = round(end-start,2)
    rows=len(df)
    w.wechat_file(file_path = fname+'.xlsx',key=key)
    
    content=[[output_user,output_outer_ip,output_internal_ip,now,server_type,fname,rows,usetime,sql,h,p,n,c,d]]
    df_record = pd.DataFrame(content)
    df_record.columns=['output_user','output_outer_ip','output_internal_ip','output_time','server_type','file_name','rows','usetime','sql','host','port','user','code','db']
    try:
        mysql_write(df_record,'pysql_output_record',update = True,hosts = host_record,wtype='a',index = False)
    except:
        print('pysql_output_record 记录表不存在，已重新创建')
        mysql_write(df_record,'pysql_output_record',update = True,hosts = host_record,wtype='r',index = False)


# ================================================================================

# Part 3 connect database
# ================================================================================

# 写入数据库

# 3.1
def mysql_write(df,name_in_db,update = False,hosts = {},wtype='r',index = False,charset='utf8mb4'):
    from sqlalchemy import create_engine
    from urllib.parse import quote_plus as urlquote
    host = hosts['host']
    port = hosts['port']
    name = hosts['user']
    code = hosts['code']
    db = hosts['db']
    if charset=='':
        # engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(name,code,host,port,db))
        engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(name,urlquote(code),host,port,db))
    else:
        # engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(name,code,host,port,db,charset))
        engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(name,urlquote(code),host,port,db,charset))
    if update == True:
        now = datetime.datetime.now().strftime('%F %T')
        df['updated'] = [now for i in range(len(df))]
    
    if wtype == 'r':
        write_type = 'replace'
    elif wtype == 'a':
        write_type = 'append'
    df.to_sql(name = name_in_db , con = engine,if_exists = write_type,index = index)
    print('\n{}({}) 数据库写入完成\n'.format(host,db))


# 查询数据库

# 3.2
def mysql_select(sql,hosts):
    '''
    Parameters
    ----------
    sql : str        mysql,select语言
    host : dict        {'host': '10.30.5.6', 'port': '3306', 'user': 'slave', 'code': '***', 'db': 'bpm'}

    Returns
    -------
    df_read : DataFrame        返回 sql 查询结果
    '''
    
    # MySQL导入DataFrame
    from sqlalchemy import create_engine
    import pandas as pd
    
    from urllib.parse import quote_plus as urlquote

    host=hosts['host']
    port=hosts['port']
    user=hosts['user']
    password=hosts['code']
    db_name=hosts['db']
    con_info = f'mysql+pymysql://{user}:{urlquote(password)}@{host}:{port}/{db_name}?charset=utf8'
    engine = create_engine(con_info)
    
    # engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(hosts['user'],hosts['code'],hosts['host'],hosts['port'],hosts['db']))
    # engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8".format(hosts['user'],hosts['code'],hosts['host'],hosts['port'],hosts['db']))
    # 填写自己所需的SQL语句，可以是复杂的查询语句
    sql_query = sql
    # 使用pandas的read_sql_query函数执行SQL语句，并存入DataFrame
    df_read = pd.read_sql_query(sql_query, engine)
    return df_read

# 3.3 修改数据库（DDL）
# 如上导入了mysql.connector第三方库，需要安装pip install mysql-connector -i https://pypi.tuna.tsinghua.edu.cn/simple
# 和pip install mysql-connector-python -i https://pypi.tuna.tsinghua.edu.cn/simple
# --allow-external mysql-connector-python
def mysql_ddl(sql,hosts = {},multi=False,division=False):
    import mysql.connector 

    mydb = mysql.connector.connect(
        host = hosts['host'],
        port = hosts['port'],
        user = hosts['user'],
        password = hosts['code'],
        database = hosts['db']
    )
    
    mycursor = mydb.cursor()
    
    # sql = "DELETE FROM cx_bi_report.test a WHERE MonthID=3"
    # sql = "alter table dim_date comment '日期维度表';"
    # hosts = hosts_write
    
    # mycursor.execute(sql,multi=True)
    # print("sql执行成功:\n",sql)
    # mydb.commit()
    if division==False:
        pass
    else:
        mycursor.execute('''SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';''')
        mydb.commit()
        
    
    
    if multi==False:
        if 'delete' in sql.lower():
            mycursor.execute(sql)
            rows = mycursor.rowcount
            print("删除成功:\n",sql)
            mydb.commit()
            result = "{} record(s) deleted".format(mycursor.rowcount)
            print(mycursor.rowcount, "record(s) deleted")
        else:
            mycursor.execute(sql)
            rows = mycursor.rowcount
            print(mycursor.rowcount)
            # print("sql执行成功:\n",sql)
            mydb.commit()
            result = "sql执行成功:\n"+sql
    else :
        mycursor.execute(sql,multi=multi)
        # print("sql执行成功:\n",sql)
        mydb.commit()
        result = "sql执行成功:\n"+sql
    print(result)
    return rows

def mysql_dtype_sql(column,table,hosts,dtype = 'VARCHAR(255)'):
    # alter_sql = '''ALTER TABLE `bi_report`.`om_017_ads_tzl_d_f` MODIFY `申请人` VARCHAR(255);'''
    alter_sql = f'''ALTER TABLE `{hosts['db']}`.`{table}` MODIFY `{column}` {dtype};'''
    return alter_sql

def mysql_index_sql(column,table,hosts):
    # from elias.Scripts import youdao as y
    try:
        index_name = "index_"+get_name(column)
        # index_name = "index_"+y.get_name(column)
    except:
        index_name = "index_"+translate_chinese_to_english(column)
    # alter_sql = '''ALTER TABLE `bi_report`.`om_017_ads_tzl_d_f` ADD INDEX idx_mobile (`申请人`);'''
    alter_sql = f'''ALTER TABLE `{hosts['db']}`.`{table}`  ADD INDEX {index_name} (`{column}`);'''
    return alter_sql

def mysql_add_index(column,table,hosts):
    dtype_sql = mysql_dtype_sql(column,table,hosts,dtype = 'VARCHAR(255)')
    index_sql = mysql_index_sql(column,table,hosts)
    mysql_ddl(dtype_sql,hosts = hosts)
    mysql_ddl(index_sql,hosts = hosts)
    result = f"\ndtype_sql执行成功:\n{dtype_sql}\n\n-------------\nindex_sql执行成功:\n{index_sql}\n"
    print(result)
    return result


def mysql_column_comment(table = 'dim_month',column = 'month_name',comment = '',hosts={},column_type = None):
    
    if column_type == None:
    
        column_type_select = f'''
        SELECT 
        TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,COLUMN_COMMENT
        FROM information_schema.COLUMNS 
        WHERE TABLE_NAME = '{table}'
        AND TABLE_SCHEMA = '{hosts['db']}'
        AND COLUMN_NAME = '{column}'
        '''
        
        df = mysql_select(column_type_select, hosts)
        column_type = df['COLUMN_TYPE'][0]
    else:
        pass
    
    sql = f'''
          alter table `{table}` modify `{column}` {column_type} comment '{comment}';
          '''
    mysql_ddl(sql,hosts=hosts)
    result = f'mysql table:{table} \ncolumn:{column} \ncomment:{comment} \nalter success!'
    return result


# -------------------------------------------------------------------------------------
# from golden

# 3.4
def py_impala(sql, warn=True, num=1, sleeps=3, title='',ssh_host = {},service = {}):

    from myfuncs import ParamikoLib
    import time

    start = time.time()
    n=num
    while True:
        try:
            paramiko = ParamikoLib.ParamikoLib()
            # ssh_host = {"host": "10.35.12.4", "port": 22, "username": "**", "password": "**"}  # 中转主机
            # service = {"host": "prod-worker-x", "port": 21050, "krb_host": "prod-worker-x", "krb_service": "impala", "krb_username":"**", "krb_password":"**"}  # 请求服务
            result = paramiko.exec_command(ssh_host, service, sql)    # 执行查询语句
            end = time.time()
            print('rows:',len(result))
            print('usetime:', round(end-start,2), 'seconds')
            return result
        except Exception as e:
            print('ImpalaError...')
            time.sleep(sleeps)
            n=n-1
            if n==0:
                print('ImpalaError:', e)
                return 'error'

# 3.5
def py_hive(sql, warn=True, num=1, sleeps=3, title='',ssh_host = {},service = {}):

    from myfuncs import ParamikoLib
    import time

    start = time.time()
    n=num
    while True:
        try:
            paramiko = ParamikoLib.ParamikoLib()
            # ssh_host = {"host": "10.35.12.4", "port": 22, "username": "**", "password": "**"}  # 中转主机
            # service = {"host": "prod-hs2-x", "port": 10000, "krb_host": "prod-hs2-x", "krb_service": "hive", "krb_username":"**", "krb_password":"**"}  # 请求服务
            result = paramiko.exec_command(ssh_host, service, sql)    # 执行查询语句
            end = time.time()
            print('rows:',len(result))
            print('usetime:', round(end-start,2), 'seconds')
            return result
        except Exception as e:
            print('ImpalaError...')
            time.sleep(sleeps)
            n=n-1
            if n==0:
                print('ImpalaError:', e)
                return 'error'

#-------------------------------------------------------------------------------
# from blackshark

# 3.6
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple impyla
def bs_impala(sql,hosts):
    from impala.dbapi import connect
    import pandas as pd
    import time

    start = time.time()
    
    config = hosts
    
    try:
        conn = connect(**config)
        print('OK')
    except Exception as e:
        print('wrong')
        raise e
    
    cur = conn.cursor(dictify=True)
    # cur = conn.cursor()
    # sql = """
    # SELECT d_play_status FROM romdata.kudu_events_171 
    # WHERE event_id ='1710014'
    # LIMIT 10
    # """
    cur.execute(sql)
    result = cur.fetchall()
    # print(result)
    
    # 习惯要好，查询完毕关闭连接
    cur.close()
    conn.close()
    
    df = pd.DataFrame(result)
    end = time.time()
    usetime = round(end-start,2)
    end = time.time()
    print('rows:',len(result))
    print('usetime:', usetime, 'seconds')
    return df


#-------------------------------------------------------------------------------
# sqlserver

# 3.7 
def sqlserver_select(hosts,sql,charset='utf8',as_dict=True):
    '''
    执行给定的SQL语句
    '''
    import pandas as pd
    import pymssql #引入pymssql模块 
    config_dict = hosts
    if charset=='':
        connect=pymssql.connect(**config_dict)
    else:
        connect=pymssql.connect(**config_dict,charset=charset,as_dict=as_dict)
    cursor=connect.cursor() 
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
    connect.close()
    return df

# 3.8
def sqlserver_select_table(hosts,table,charset='utf8',as_dict=True):
    '''
    执行给定的SQL语句
    '''
    import pandas as pd
    import pymssql #引入pymssql模块 
    config_dict = hosts
    if charset=='':
        connect=pymssql.connect(**config_dict)
    else:
        connect=pymssql.connect(**config_dict,charset=charset,as_dict=as_dict)
    cursor=connect.cursor() 
    sql = f'SELECT * FROM {table}'
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
    connect.close()
    return df


# 3.9
def sqlserver_select_columns(hosts,table,charset='utf8',as_dict=True):
    '''
    执行给定的SQL语句
    '''
    import pandas as pd
    import pymssql #引入pymssql模块 
    config_dict = hosts
    if charset=='':
        connect=pymssql.connect(**config_dict)
    else:
        connect=pymssql.connect(**config_dict,charset=charset,as_dict=as_dict)
    cursor=connect.cursor() 
    sql = f"SELECT * FROM syscolumns WHERE id = OBJECT_ID('{table}')"
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
    connect.close()
    s = ",".join(list(df['name']))
    return s

# 3.10
def sqlserver_select_table_fixed(hosts ,table,charset='utf8',as_dict=True):
    '''
    执行给定的SQL语句
    解决中文乱码的问题
    '''
    df = sqlserver_select(sql = f'sp_columns {table} ',hosts = hosts,charset=charset,as_dict=as_dict)
    df = df[['COLUMN_NAME','TYPE_NAME','LENGTH']]
    s_list = []
    for i in range(len(df)):
        if df['TYPE_NAME'][i] == 'varchar':
            s = f'''CONVERT(nvarchar({df['LENGTH'][i]}), [{df['COLUMN_NAME'][i]}])[{df['COLUMN_NAME'][i]}]'''
            # print(s)
        else:
            s = f'''[{df['COLUMN_NAME'][i]}]'''
            # print(s)
        s_list.append(s)
    ss = ','.join(s_list)
    sql = f''' select {ss} from {table}'''
    df = sqlserver_select(sql=sql,hosts = hosts,charset=charset,as_dict=as_dict)
    return df
    

# 3.11 clickhouse_ddl
# def clickhouse_select(sql = 'SHOW TABLES',hosts = all_hosts(name = 'ch_bi_report')): # 能良om正式环境
#     from clickhouse_sqlalchemy import make_session
#     from sqlalchemy import create_engine
#     import pandas as pd
    
#     # conf = {
#     #     "user": "nl2020",
#     #     "password": "nengliang2020!",
#     #     "server_host": "cc-uf651o30oz76wz9p9.public.clickhouse.ads.aliyuncs.com",
#     #     "port": "8123",
#     #     "db": "default"
#     # }
    
    
#     conf = {
#         "user": hosts['user'],
#         "password": hosts['code'],
#         "server_host": hosts['host'],
#         "port": hosts['port'],
#         "db": hosts['db']
#     }
    
#     connection = 'clickhouse://{user}:{password}@{server_host}:{port}/{db}'.format(**conf)
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


# 3.11 clickhouse_ddl
def clickhouse_ddl(sql,hosts): # 能良om正式环境
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
    client.disconnect()
    return df



# 3.12 clickhouse_ddl
def clickhouse_select(sql,hosts): # 能良om正式环境
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
    df = client.query_dataframe(sql)
    return df




def mc_ddl(sql,hosts):
    from odps import ODPS
    access_id = hosts['access_id']
    access_key = hosts['access_key']
    project_name = hosts['project_name']
    endpoint = hosts['end_point']
    connection = ODPS(access_id, access_key, project_name, endpoint)
    connection.execute_sql(sql)
    return 'success'


def mc_select(sql,hosts):
    from odps import ODPS
    # 配置MaxCompute连接信息
    access_id = hosts['access_id']
    access_key = hosts['access_key']
    project_name = hosts['project_name']
    end_point = hosts['end_point']
    
    # 创建MaxCompute连接
    odps = ODPS(access_id, access_key, project_name, endpoint=end_point)
    
    # 执行查询并将结果转换为DataFrame
    # sql = 'SELECT * FROM dim_department_d_f LIMIT 10'  # 根据您的需求修改查询语句
    with odps.execute_sql(sql).open_reader() as reader:
        # 获取查询结果的字段信息
        columns = reader._schema.columns
        columns_list = []
        for i in range(len(columns)):
            column_str = str(columns[i])
            
            # 使用字符串处理方法提取目标部分
            start_index = column_str.index(" ") + 1
            end_index = column_str.index(",")
            column_name = column_str[start_index:end_index]
            # print(column_name)
            columns_list.append(column_name)
        
        # 将查询结果逐行添加到DataFrame
        data = []
        for record in reader:
            data.append(record.values)
        
        import pandas as pd
    
        # 创建DataFrame对象
        df = pd.DataFrame(data)
    
        # 设置列名
        df.columns = columns_list
    
    return df



# Part 4 send Email
# ================================================================================

    
# 发送邮件(acc:抄送人)

# 4.1
def Email_send(username, password, subject='', contents='', receivers=[], accs=[], links={}, file_pathname=None, smtp='exmail'):

    import smtplib,re
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # 设置smtplib所需的参数:
    if smtp =='exmail':
        smtpserver = 'smtp.exmail.qq.com'    # foxmail-设置-账号-服务器
    elif smtp =='qq':
        smtpserver = 'smtp.qq.com'
    else:
        print('Error: smtp argument exmail or qq')
    sender = username
    fromname = sender.split('@')[0] + ' <{}>'.format(sender)      # 'Henry.sun <Hexxx.sun@wetax.com.cn>'
    receiver = receivers + accs    #接收人

    # 邮件页面设置-只是显示：（主题，发件人/收件人-允许为空-代码可以注释掉）
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = fromname
    msg['To'] = ";".join(receivers)
    msg['Cc'] = ";".join(accs)

    # 以下设置：正文内容、邮件签名、传入参数(<br/>换行作用)
    message = '''
        <html>
        <body>
        <font size="4">Dear,</font><br/>
        <font size="1">&nbsp</font><br/>
        <font size="4">&nbsp&nbsp&nbsp&nbsp content</font><br/>
        <font size="5">&nbsp&nbsp&nbsp&nbsp</font><a href="link">linkname</a><br/>
        <p>&nbsp</p>
        </body>
        </html>'''

    msgs = message.split('\n')
    lsq5 = msgs[:5]
    lsh3 = msgs[-3:]
    mstr = msgs[5]
    lstr = msgs[6]

    type_c = isinstance(contents, str)   # 类型为str 则返回True,否则返回False
    if type_c ==True:
        conts = [contents]
    else:
        conts = contents
    mstrs = []
    for i in conts:
        i = str(i).replace('\\','/')           # 消除转义字符\ 以免下面报错！(特殊字符会报错-此处修复)
        s = re.sub('content', str(i), mstr)    # i中若有\x会报错!
        mstrs.append(s)

    link_hs = []
    for key,value in links.items():
        link_key = str(key).replace('\\','/')
        link_value = str(value).strip()
        link_h = lstr.replace('linkname',link_key).replace('link',link_value)
        link_hs.append(link_h)

    ls_msg = lsq5 + mstrs + link_hs + lsh3
    message = '\n'.join(ls_msg)

    # 邮件对象: （三个参数：文本内容、plain 设置文本格式、utf-8 设置编码）
    msg.attach(MIMEText(message, 'html', 'utf-8'))

    # 添加附件-名称支持英文/数字/符号：（中文名称在foxmail的pc端、QQ邮箱的pc与手机端都正常，但在foxmail手机端名称显示为UrlDdecode编码）
    if file_pathname != None:
        type_f = isinstance(file_pathname, str)   # 类型为str 则返回True,否则返回False
        if type_f ==True:
            files = [file_pathname]
        else:
            files = file_pathname
        for f in files:
            fname = f.split('\\')[-1]     # 支持路径的两种斜杠/\形式！
            fname = fname.split('/')[-1]
            att = MIMEText(open(r'{}'.format(f), 'rb').read(), 'base64', 'utf-8')  # 编码参数不可省略！
            att["Content-Type"] = 'application/octet-stream'
            att.add_header('Content-Disposition', 'attachment', filename=fname)   # fname-附件的文件名称(test.png)
            msg.attach(att)

    # 发送邮件：
    try:
        # smtp = smtplib.SMTP()   # 未加密发送
        smtp = smtplib.SMTP_SSL(smtpserver, 465)   # 加密发送（页面上无区别）
        smtp.connect(smtpserver)
        smtp.login(username, password)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()
        return '发送成功！'
    except Exception as e:
        print('Error:', str(e))

# Email_send('noreply-dmp@goldentec.com', 'Gaopeng@123', subject='测试', contents=['超链接测试'], receivers=['yiting.liu@goldentec.com'], accs=[], links={'地址>>':'http://www.baidu.com'}, file_pathname=[r'C:\Users\ahui\Desktop\11.txt'], smtp='exmail')

# 4.2
def Email_warn(title='测试', contents=['超链接测试'], receivers=[], accs=[], links={}, file_pathname=None):
    from elias import wechat as w
    try:
        Email_send('noreply-dmp@goldentec.com', 'Gaopeng@123', 
               subject=title,
               contents=contents, 
               receivers=receivers, 
               accs=accs,
               links=links, 
               file_pathname=file_pathname,
               smtp='exmail')
        l = 'success ! '
    except Exception as e:
        l = 'fail ! \n'+str(e)
    text = f'邮件：{title}\n发送{l}'
    w.run_warning(title = "Email发送通知",text = text, user='yiting.liu')







# Part 5 spyder
# ================================================================================

    
# 发送邮件(acc:抄送人)

# 5.1  
def weather():
    # 爬取天气
    import requests
    from bs4 import BeautifulSoup
    r = requests.get('http://www.weather.com.cn/weather/101020100.shtml').content.decode('utf-8')
    soup = BeautifulSoup(r)
    result = soup.find('li', class_='sky skyid lv3 on')
    p = result.find_all('p')
    h = result.find('h1').text
    wea = p[0].text
    tem = p[1].text.replace('\n','')
    win1 = result.find('em').find_all('span')[0]['title']
    try:
        win2 = result.find('em').find_all('span')[1]['title']
    except:
        win2 =""
    if "风" in win2:
        win = win1+"转"+win2
    else:
        win = win1
    w =p[2].text.replace('\n','')
    c = soup.find('div', class_="crumbs fl").find_all('a')[1].text
    d = soup.find('div', class_="crumbs fl").find_all('span')[2].text
    tq = '''{}-{}-{}\n{},{}\n{}\n{}'''.format(c,d,h,tem,wea,win,w)
    return tq 
    
    
    
# 5.2  
def video_get(url,name='hello_world',path = '',v_type='mp4'):
    import os
    if path == '':
        os.getcwd()
        path = os.path.join(os.path.expanduser('~'),"Desktop")
    filepath = os.path.join(path,f'{name}.{v_type}')
    import requests
    res = requests.get(url)
    con = res.content
    doc = open(filepath,'wb')
    doc.write(con)
    doc.close
    print(filepath,'获取成功')


# 5.3
def url_request(url):
    import requests
    res = requests.get(url)
    con = res.content
    return con

    

# 5.4 截取浏览器全屏
def fullscreenshot(url='https://www.baidu.com/',size = (0,0),width_new = 1920,timesleep = 10,file='webpage.png'):
    from selenium import webdriver
    from PIL import Image
    import time

    print('打开浏览器')
    url=url
    option=webdriver.ChromeOptions()
    option.add_argument('headless')
    driver=webdriver.Chrome(options=option)

    print('访问网址')
    driver.get(url)


    print('修改浏览器窗口大小')
    if size == (0,0) or type(size) is not tuple:
        width = driver.execute_script("return document.documentElement.scrollWidth")
        height = driver.execute_script("return document.documentElement.scrollHeight")
    else:
        width = size[0]
        height = size[1]

    width_new = width_new
    rate = width_new/width
    height_new = height*rate

    driver.set_window_size(width_new,height_new) #修改浏览器窗口大小

    print(f'等待{timesleep}秒加载')
    time.sleep(timesleep)
    print('获取整个网页截图')
    #获取整个网页截图
    driver.get_screenshot_as_file(file)
    print("整个网页尺寸:height={},width={}".format(height_new,width_new))
    im=Image.open(file)
    print("截图尺寸:height={},width={}".format(im.size[1],im.size[0]))
    
    # 关闭浏览器
    driver.quit()
    return im
    

# Part 6 decode & encode
# ================================================================================

# 6.1
def url_encode(s='hello world!'):# url编码
    import urllib
    ss = urllib.parse.quote(s)
    return ss

# 6.2
def url_decode(s='%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90%E5%B8%88'):
    import urllib
    ss = urllib.parse.unquote(s)
    return ss

# 6.3
def decode(s):
    return s.encode('raw_unicode_escape').decode()



    

# Part 7 system environment
# ================================================================================

# 7.1
def all_files(path, sep_count=1):
    import os
    #去列出来当前目录下，所有的文件和文件夹
    # 一个一个去判定:
         #如果是文件： 直接去打印
         #如果是目录:  先去打印再继续访问
              #去列出目录下所有的文件和文件夹
              #一个一个判定，
                    # 如果是文件： 直接去打印
                    # 如果是目录:  先去打印再继续访问
    for sub_path in os.listdir(path):
        if os.path.isfile(os.path.join(path, sub_path)): #绝对路径
           print("--" * sep_count, sub_path, sep="")
        if os.path.isdir(os.path.join(path, sub_path)):
           print("--" * sep_count, sub_path, sep="")
           all_files(os.path.join(path, sub_path), sep_count=sep_count + 1)

def list_file(path):
    import os
    files = []
    for sub_path in os.listdir(path):
        if os.path.isfile(os.path.join(path, sub_path)): #绝对路径
            files.append(sub_path)
    return files

def list_folder(path):
    import os
    folders = []
    for sub_path in os.listdir(path):
        if os.path.isdir(os.path.join(path, sub_path)): #绝对路径
            folders.append(sub_path)
    return folders            

# 7.2
def to_txt(name = 'hello world', content='hello python!\nhello world!\n'):
    import os
    os.getcwd()
    path = os.path.join(os.path.expanduser('~'),"Desktop")
    filepath = os.path.join(path,f'{name}.txt')
    f1 = open(filepath,'w')
    f1.write(content)
    f1.close()
    print('txt输出成功')           

# 7.3
def file_get(path=''):
    file = path.split("\\")[-1]
    return file

# 7.4
def filename_get(path=''):
    # filename = path.split("\\")[-1].split(".")[0]
    plist = path.split("\\")[-1].split(".")
    del plist[-1]
    filename = '.'.join(plist)
    return filename

# 7.5
def zip_path(dirpath, outFullName):#手动输入源路径和目标路径&文件名，无输出return
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    import os
    import zipfile
    from loguru import logger
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')
 
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()
    logger.info("文件夹\"{0}\"已压缩为\"{1}\".".format(dirpath, outFullName))

# 7.6
def zip_file(start_dir):#自动在上级目录创建文件，输出压缩文件路径
    # PS: 若递归扫描所有文件夹过程中有文件夹里不存在文件, 该文件夹将被忽略
    import os
    import zipfile
    start_dir = start_dir  # 要压缩的文件夹路径
    file_news = start_dir + '.zip'  # 压缩后文件夹的名字

    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(start_dir):
        f_path = dir_path.replace(start_dir, '')  # 这一句很重要，不replace的话，就从根目录开始复制
        f_path = f_path and f_path + os.sep or ''  # 实现当前文件夹以及包含的所有文件的压缩
        for filename in file_names:
            z.write(os.path.join(dir_path, filename), f_path + filename)
    z.close()
    return file_news

# 7.7
def desktop_path():
    import os
    user = os.getlogin()
    path = r"C:\Users\%s\Desktop"%user
    return path

# 7.8
def change_language(lang="EN"):
    import win32api
    import win32gui
    from win32con import WM_INPUTLANGCHANGEREQUEST
    """
    切换语言
    :param lang: EN––English; ZH––Chinese
    :return: bool
    """
    LANG = {
        "ZH": 0x0804,
        "EN": 0x0409
    }
    hwnd = win32gui.GetForegroundWindow()
    language = LANG[lang]
    result = win32api.SendMessage(
        hwnd,
        WM_INPUTLANGCHANGEREQUEST,
        0,
        language
    )
    if not result:
        return True

# 7.9
def name_to_html(file_name = 'website_1.exe'):
    print('初始文件名：'+file_name)
    if '.' in file_name:
        if '.html' in file_name:
            print('初始文件类型正确，为html')
            file_name = file_name
        else:
            file_list = file_name.split('.')
            print(f'初始文件类型为{file_list[1]}，已自动修正为html')
            file_name = file_list[0]+'.html'
            
    else:
        print('初始文件后缀缺失，文件类型无法识别')
        file_name = file_name+'.html'
    print('……\n确认文件名：'+file_name)
    return file_name

# 7.10
def file_exists_rename(file_name):
    import os
    n = 1
    while os.path.exists(file_name) == True:
        print('\n文件已存在，自动修正文件名')
        if f'_{n-1}.html' in file_name:
            file_name = file_name.replace(f'_{n-1}.html',f'_{n}.html')
        else:
            f_list = file_name.split('.')
            file_name = f_list[0]+f'_{n}.'+f_list[1]
        n=n+1
        print('修正后：'+file_name)
        print('\n----------------')
    print('\n文件确认，可直接使用')
    print('确认文件：'+file_name)
    return file_name

# 7.11
def file_path_fill(file_name,file_path = r'C:\Users\fbi\Desktop\elias\kk_scripts\save_page'):
    import os
    # file_path = r'C:\Users\fbi\Desktop\elias\kk_scripts\save_page'
    
    if file_name == None:
        print('文件名缺失，补全为 new_website.html')
        file_name = os.path.join(file_path, 'new_website.html')
    else:
        if '\\' in file_name:
            print('文件名为路径，无需修改')
            file_name = file_name
        else:
            print('已补全路径')
            file_name = os.path.join(file_path, file_name)
    print(file_name)
    return file_name

# 7.12
# 读取剪贴板的数据
def get_clipboard():
    import win32con
    from win32clipboard import GetClipboardData, OpenClipboard, CloseClipboard
    
    OpenClipboard()
    d = GetClipboardData(win32con.CF_TEXT)
    CloseClipboard()
    print(d.decode("GBK"))
    return d.decode('GBK')
    # return d

# 7.13
# 写入剪贴板数据
def set_clipboard(astr):
    import win32con,time
    from win32clipboard import OpenClipboard, CloseClipboard, EmptyClipboard,SetClipboardData

    OpenClipboard()
    EmptyClipboard()
    #可以sleep一下，防止操作过快报错
    time.sleep(1)
    SetClipboardData(win32con.CF_UNICODETEXT, astr)
    CloseClipboard()

# 7.14 系统控制浏览器打开网页，并保存到相应文件
def save_html(url,file_name=None):
    
    # 确定文件名
    
    # 补全文件名路径
    file_name = file_path_fill(file_name)
    
    # 检查html文件类型
    file_name = name_to_html(file_name)
    
    # 检查文件是否重复
    file_name = file_exists_rename(file_name)
    
    
    import webbrowser
    import time
    import os

    webbrowser.open(url)
    time.sleep(5)
    
    # title = '滑动验证页面.html'
        
    import pyautogui
    
    # 组合键
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)

    # 组合键-复制默认文件名
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
        
    # 读取剪贴板
    title = get_clipboard()
    
    if '滑动验证页面' in title:
        
        # 按键
        pyautogui.press('tab')# 文件类型
        time.sleep(0.5)
        pyautogui.press('tab')# 隐藏文件夹
        time.sleep(0.5)
        pyautogui.press('tab')# 保存
        time.sleep(0.5)
        pyautogui.press('tab')# 取消
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        from elias import wechat as w
        result = title_verify_slide(title)
        w.run_warning(text = title+'\n'+result,key = w.robots('bs_pbi_details'))
        print(title,result)
        
        time.sleep(5)
        
    else:
        pass
        
    
    
    # 组合键
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)

    
    # file_name写入剪贴板
    set_clipboard(file_name)
        
    # 组合键-粘贴
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)

    # # 切换输入法
    # change_language(lang = 'EN')
    
    # # 自动输入
    # pyautogui.typewrite(file_name)
    # time.sleep(1)
    
    # 按键
    pyautogui.press('enter')
    
    time.sleep(5)
    
    t=0
    start = time.time()
    while os.path.exists(file_name)!=True:
        end = time.time()
        print('下载中……', round(end-start, 2), 'seconds')
        time.sleep(1)
        t=t+1
    print('html下载完成')
    # os.system('taskkill /F /IM chrome.exe')
    
    return file_name

# 7.15 遍历windows下 所有句柄及窗口名称
def windows_items_find():
    import win32gui
    hwnd_title = dict()
    def get_all_hwnd(hwnd,mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            hwnd_title.update({hwnd:win32gui.GetWindowText(hwnd)})
    win32gui.EnumWindows(get_all_hwnd, 0)
    
    for h,t in hwnd_title.items():
        if t != "":
            print('--------------------')
            print(h, t)

# 7.16 根据title进行滑动验证判断
def title_verify_slide(title):

    if '滑动验证页面' in title:
        result = '页面异常，需要验证'
        
        import win32con
        import win32gui
        # import time
        
        # 查找窗口句柄
        hwnd = win32gui.FindWindow("Chrome_WidgetWin_1",u"滑动验证页面 - Google Chrome")
        print(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
        win32gui.SetForegroundWindow(hwnd)  # 设置前置窗口
        
        import pyautogui
        pyautogui.moveTo(1080, 375)
        pyautogui.dragRel((1350-1080),0, duration=1)
    else:
        result = '页面正常，无需验证'
    # print(result)
    return result

# 7.17 获取本机局域网ip
def get_ip():
    import socket
    # 函数 gethostname() 返回当前正在执行 Python 的系统主机名
    res = socket.gethostbyname(socket.gethostname())
    print(res)
    return res

# 7.18 获取本机公网ip
def get_out_ip():
    import requests
    import re
     
    ip = ''    
    try:
        res = requests.get('https://myip.ipip.net', timeout=5).text
        ip = re.findall(r'(\d+\.\d+\.\d+\.\d+)', res)
        ip = ip[0] if ip else ''
    except:
        pass
    print(ip)
    return ip


# # 7.19 获取本机elias代码仓库路径
# def get_elias_path(path = ''):
#     import os,sys
#     os.getcwd()
#     list_path = sys.path
#     l = 999
#     for i in range(len(list_path)):
#         if ":\\anaconda3\\lib" in list_path[i].lower():
#             if len(list_path[i])<l:
#                 l=i
#                 a = list_path[i]
#     elias = os.path.join(a, "elias")
#     # print('\n------------------\nelias 路径：\n\n',os.path.join(elias, path),'\n------------------\n')
#     return os.path.join(elias, path)


# # 7.20 获取本机elias代码仓库中，missions中所有mission_run脚本路径
# def get_mission_list(elias_path = get_elias_path(path = 'missions')):
#     import os
#     # elias_path = get_elias_path(path = 'missions')
#     mission_list = os.listdir(elias_path)
#     # print(mission_list)
#     run_list = []
#     for i in range(len(mission_list)):
#         mission = mission_list[i]
#         # print(mission)
#         mission_path = os.path.join(elias_path, mission)
#         run_path = os.path.join(mission_path, 'mission_run.py')
#         print(f'\n------------------\n{mission} 路径：\n\n',run_path,'\n------------------\n')
#         run_list.append(run_path)
#     return run_list


# # 7.21 执行7.20获取的所有脚本（本机elias代码仓库中，missions中所有mission_run脚本路径）
# def all_mission_doing(run_list):
#     import os
#     # run_list= get_mission_list()
#     mission_name = 'All Missions Run'
#     success_list = ''
#     fail_list = ''
#     s=0
#     f=0
#     n=0
#     for run_path in run_list:
#         # print(run_path)
        
#         # ----------------------------------- ok
#         # mission 
#         success = ''
#         fail = ''
#         n=n+1
#         e = None
#         try:
#             os.system(run_path)
#             success = f'【{n}】 {file_get(run_path)} success\n'
#             success_list = success_list + success
#             s = s+1
#         except Exception as e:
#             fail = f'【{n}】 {file_get(run_path)} fail\n' + str(e) + '\n'
#             fail_list = fail_list + fail
#             f = f+1
        
#     if success_list =='':
#         success_list = '无\n'
#     if fail_list =='':
#         fail_list = '无\n'
#     all = s+f
    
#     result = f'''</font>Total <font color=\"warning\">**{all}**</font> missions \n<font color=\"warning\">**{s}**</font> missions success \n<font color=\"warning\">**{f}**</font> missions fail\n
#     ---------------------\n**success missions:**\n{success_list}\n
#     ---------------------\n**fail missions:**\n{fail_list}\n
#     <font color=\"comment\">-end-'''
#     return mission_name,result

# 7.22 python中执行终端命令
def run_cmd(cmd_command = "ipconfig", shell=True, capture_output=True, text=True):
    import subprocess
    
    # 要执行的cmd命令
    # cmd_command = "ipconfig"  # 这里以查看网络配置信息为例
    
    # 使用subprocess模块执行cmd命令
    try:
        result = subprocess.run(cmd_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            # 输出cmd命令执行结果
            print("命令执行成功：")
            print(result.stdout)
        else:
            # 输出cmd命令执行错误信息
            print("命令执行失败：")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print("命令执行出错：", e)    

def run_cmd_os(cmd_command = "ipconfig"):
    import os
    
    # 要执行的cmd命令
    # cmd_command = "ipconfig"  # 这里以查看网络配置信息为例
    
    # 使用os.system()执行cmd命令
    try:
        return_code = os.system(cmd_command)
        if return_code == 0:
            print("命令执行成功")
        else:
            print("命令执行失败")
    except Exception as e:
        print("命令执行出错：", e)


def translate_chinese_to_english(chinese_text):
    from googletrans import Translator
    translator = Translator()
    translated_text = translator.translate(chinese_text, src='zh-cn', dest='en').text
    return translated_text



def create_folder_if_not_exists(folder_path):
    import os
    from loguru import logger
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.warning(f"\n完成创建，Folder created at {folder_path}")
    else:
        logger.info(f"\n文件夹已存在，Folder already exists at {folder_path}")



# Part 8 DataFrame dealing
# ================================================================================

# 8.1
def py_mission_records(mission_name,m_id,m_name,r,ee,usetime,rows,hosts = all_hosts(name = 'records'),sql=''):
    import pandas as pd
    try:
        rows = int(rows)
    except:
        rows = 0
    dic_r = {
            'date': Date_now(),
            'origin_system': mission_name,
            'mission_id': m_id,
            'mission_name': m_name,
            'usetime':usetime,
            'rows':rows,
            'result': r,
            'sql':sql,
            'fail_exception': ee,
            'datetime':Datetime_now(),
            'run_ip':get_out_ip()
        }
    df_r = pd.DataFrame([dic_r])
    mysql_write(df_r,'py_mission_records',update = True,hosts = hosts,wtype='a')
    return df_r

def py_mission_robot_message(mission,start,end,all_c,fail_c,success_c):
    usetime = str(round(end-start, 2))+ ' seconds'
    result = '\n===========%s - 任务执行日报========\n任务开始：%s\n任务结束：%s\n执行时长：%s\n\n总任务数：%s\n异常任务数：%s\n成功任务数：%s\n================ end =================\n'%(mission,Stamp_to_Datetime(start),Stamp_to_Datetime(end),usetime,all_c,fail_c,success_c)
    return result




# Part 9 DataFrame dealing
# ================================================================================

# 9.1 从字符串中提取中文字符
def find_chinese(str):
    import re #re是正则表达式模块
    chinese = re.findall('[\u4e00-\u9fa5]', str)  # 汉字的范围为"\u4e00-\u9fa5"
    str_result = ''
    for ch in chinese:
        str_result = str_result + ch
    print( '\n源文本:',str)
    print('\n提取中文:',str_result)
    return str_result



# 9.2 26个字母对应数字
def letter_num(letter = 'A'):
    dic = {
    'A':1,
    'B':2,
    'C':3,
    'D':4,
    'E':5,
    'F':6,
    'G':7,
    'H':8,
    'I':9,
    'J':10,
    'K':11,
    'L':12,
    'M':13,
    'N':14,
    'O':15,
    'P':16,
    'Q':17,
    'R':18,
    'S':19,
    'T':20,
    'U':21,
    'V':22,
    'W':23,
    'X':24,
    'Y':25,
    'Z':26
    }
    return dic[letter]


# 9.3 增量刷新：比对新老数据的差异，把新数据的新增部分补充到老数据。
def Incremental_update(df_old,df_final):
    '''
    增量刷新
    Parameters
    ----------
    df_old : DataFrame
        老的数据，可以没有updated.
    df_final : DataFrame
        新的数据，用当前时间刷新updated.

    Returns
    -------
    df_new_f : DataFrame
        比对新老数据的差异，把新数据的新增部分补充到老数据。
        新数据删除的部分老数据不会删除，会以当时更新的时间保留，用updated字段识别。

    '''
        
    # 添加update
    import datetime
    now = datetime.datetime.now().strftime('%F %T')
    df_final['updated'] = [now for i in range(len(df_final))]
    
    import pandas as pd
    # list(df_1.columns)
    try:
        print(df_old['updated'])
    except:
        df_old['updated'] = None
    
    
    clist = list(df_final.columns)
    clist.remove('updated')
    # 拼接 新老 数据
    df_new = pd.concat([df_old,df_final],axis=0)
    # 排序 - 降序['工号','日期','updated']
    df_new = df_new.sort_values(by = list(df_final.columns),axis = 0,ascending = False)
    # 去重 - 保留第一条
    df_new_f = df_new.drop_duplicates(subset=clist,keep='first',inplace=False)
    # 重置索引
    df_new_f.reset_index(inplace=True,drop=True)
    
    # # 覆盖老数据
    # mysql_write(df_new_f,table_name,hosts = all_hosts(name = 'kk_temp'))
    # print(len(df_new_f),len(df_old))
    
    incremental = len(df_new_f)-len(df_old)
    print(f"新增{incremental}条数据")
    
    return df_new_f



# 9.3 解析sql，提取表名
def extract_table_name_from_sql(sql):
    
    import re

    # remove the /* */ comments
    q = re.sub(r"/\*[^*]*\*+(?:[^*/][^*]*\*+)*/", "", sql)

    # remove whole line -- and # comments
    lines = [line for line in q.splitlines() if not re.match("^\s*(--|#)", line)]

    # remove trailing -- and # comments
    q = " ".join([re.split("--|#", line)[0] for line in lines])

    # split on blanks, parens and semicolons
    tokens = re.split(r"[\s)(;]+", q)

    # scan the tokens. if we see a FROM or JOIN, we set the get_next
    # flag, and grab the next one (unless it's SELECT).
    
    # result = []
    # remove_list =[]
    # last_token = ''
    # get_next = False
    # for token in tokens:
    #     # print(token.lower())
    #     if get_next:
    #         if token.lower() not in ["", "select"]:
    #             result.append(token)
    #         get_next = False
    #     get_next = token.lower() in ["from", "join"]
        
        
    result = []
    remove_list =[] 
    last_token = ''
    for token in tokens:
        if last_token in (',','with') or ',' in token:
            remove_list.append(token)
        elif last_token in ["from", "join"]:
            result.append(token)
        last_token = token.lower()
    
    for remove_token in remove_list:
        if remove_token in result:
            result.remove(remove_token)
        else:
            pass
        
        if remove_token.replace(',','') in result:
            result.remove(remove_token.replace(',',''))
        else:
            pass
        
    return result

# 获取数据库名称
def get_name(col):
    # 检测关键字是否存在中文，并将中文翻译成英文
    # from elias.Scripts import name_in_db as n
    from elias.Scripts import youdao as yd
    if yd.is_chinese(col)==True:
        col_tr = yd.translate(col)
    else:
        col_tr = col
        
    col_tr = col_tr.replace(',','').replace('(','').replace(')','').replace('+','').replace('-','').replace('[','').replace(']','').replace('{','').replace('}','').replace('?','')
    col_tr = col_tr.replace('!','').replace('@','').replace('#','').replace('$','').replace('%','').replace('^','').replace('&','').replace('*','').replace('<','').replace('>','')
    col_tr = col_tr.replace('`','').replace('~','').replace(':','').replace(';','').replace("'",'').replace('"','').replace('|','').replace('\\','').replace('\/','').replace('.','')
    col_tr = col_tr.replace('·','').replace('！','').replace('￥','').replace('…','').replace("（",'').replace('）','').replace('—','').replace('《','').replace('》','').replace('？','')
    col_tr = col_tr.replace('：','').replace('“','').replace('”','').replace('’','').replace("‘",'').replace('；','').replace('，','').replace('。','').replace('\t','').replace('\n','')
    
    
    # 输出Mysql中表名
    name_in_db = col_tr.lower().lower().replace(" ","_")
    
    if name_in_db[-1] == '_':
        name_in_db = name_in_db[:-1]
    if name_in_db[0] == '_':
        name_in_db = name_in_db[1:]
    # print(name_in_db)
    return name_in_db

# Part 10 logging
# ================================================================================

# 10.1 logger 日志记录器
# def logger(file=''):
#     '''
    

#     Returns
#     -------
#     logger : logger 日志记录器.

#     '''
    
#     import logging
#     # import 
#     # from loguru import logger
    
#     if file==None:

#         # 配置日志输出格式
        
#         logger = logging.getLogger('my_logger')
#         logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
        
#     else:
        
        
#         if file=='':
#             file = log_path()
#         else:
#             pass
#         # import logging
        
        
#         # 创建日志记录器
#         logger = logging.getLogger('my_logger')
#         logger.setLevel(logging.DEBUG)
        
#         # 创建日志输出格式
#         formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
#         # # 检查日志记录器是否已经有处理器
#         if not logger.hasHandlers():
         
#             # 创建控制台日志处理器
#             console_handler = logging.StreamHandler()
#             console_handler.setLevel(logging.DEBUG)
#             console_handler.setFormatter(formatter)
        
#             # 创建文件日志处理器
#             file_handler = logging.FileHandler(file)
#             file_handler.setLevel(logging.DEBUG)
#             file_handler.setFormatter(formatter)
        
#             # 将处理器添加到日志记录器
#             logger.addHandler(console_handler)
#             logger.addHandler(file_handler)
    
#     return logger



def logger(file=''):
    from loguru import logger
    if file==None:
        return logger
        
    else:
        
        if file=='':
            file = log_path()
        else:
            pass
        
        
        logger.add(file, rotation="500 MB", retention="10 days", level="DEBUG")
        return logger


# 将JSON数据写入到指定的JSON文件中。
def write_json_to_file(data, file_path):
    """
    将JSON数据写入到指定的JSON文件中。

    参数：
    data: dict
        要写入文件的JSON数据，必须是一个字典。
    file_path: str
        JSON文件的路径。
    
    返回：
    JSON文件的路径。
    -------------------------------------------
    # 示例用法
    data = {
        "name": "John",
        "age": 30,
        "city": "New York"
    }

    file_path = "data.json"
    write_json_to_file(data, file_path)
    
    """
    
    import json
    
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)  # 设置indent参数为4，表示使用4个空格缩进

    print("JSON数据已写入文件：", file_path)
   
    return file_path


# 将html转化成markdown
def convert_html_to_markdown(html_content):
    
    import html2text
    import re
    # 在转换前预处理HTML，例如插入额外的空行
    html_content = re.sub(r'</p>', r'</p>\n\n', html_content)  # 在每个段落后增加额外的空行

    h = html2text.HTML2Text()
    h.body_width = 0  # 设置为0以防止自动换行
    h.ignore_emphasis = False
    h.ignore_links = False

    markdown_content = h.handle(html_content)

    # 在转换后处理Markdown，例如确保加粗不会在中间断开
    markdown_content = re.sub(r'\*\*(.*?)\*\*', lambda match: '**' + match.group(1).replace('\n', ' ') + '**', markdown_content)
    
    return markdown_content


# 将两个列表均匀插入到一个列表
def interleave_lists(list1, list2):
    '''
    两个列表均匀插入到一个列表

    Parameters
    ----------
    list1 : list
        DESCRIPTION.
    list2 : list
        DESCRIPTION.

    Returns
    -------
    result : list
    
        # 示例1
        list1 = [1, 2, 3, 4, 5, 6, 7, 8]
        list2 = ['a', 'b', 'c']
        print(interleave_lists(list1, list2)) # [1, 2, 'a', 3, 4, 'b', 5, 6, 'c', 7, 8]

        # 示例2
        list1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        list2 = ['a', 'b', 'c']
        print(interleave_lists(list1, list2)) # [1, 2, 3, 'a', 4, 5, 6, 'b', 7, 8, 9, 'c', 10]

        # 示例3
        list1 = [1, 2, 3]
        list2 = ['a', 'b', 'c', 'd', 'e', 'f']
        print(interleave_lists(list1, list2)) # ['a', 'b', 1, 'c', 'd', 2, 'e', 'f', 3]

    '''
    
    if len(list1)<len(list2):
        list0 = list1
        list1 = list2
        list2 = list0
        
    # 计算每隔多少元素插入一个 list2 的值
    step = len(list1) // (len(list2))
    
    # 结果列表
    result = []
    
    # 当前list1中的位置
    index = 0
    
    # 遍历list2，插入到list1中
    for element in list2:
        # 在list1的相应位置之前添加step个元素
        result.extend(list1[index:index + step])
        # 插入list2中的元素
        result.append(element)
        # 更新index
        index += step
    
    # 添加剩余的list1元素
    result.extend(list1[index:])
    
    return result


# 创建文件夹，如果存在就不创建
def create_dir_if_not_exists(dir_path):
    import os
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        return True
    return False

# 下载文件
def download_file(url, save_path):
    """
    Download a file from the given URL and save it to the specified path.
    
    # Example usage:
    image_url = "https://example.com/image.jpg"
    video_url = "https://example.com/video.mp4"
    image_save_path = "image.jpg"
    video_save_path = "video.mp4"
    
    # Download image
    download_file(image_url, image_save_path)
    
    # Download video
    download_file(video_url, video_save_path)
    
    Args:
        url (str): The URL of the file to download.
        save_path (str): The path where the downloaded file will be saved.
    """
    
    import requests
    try:
        # Send a GET request to the URL to fetch the file
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Write the content to a local file
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"File downloaded successfully to: {save_path}")
    except requests.exceptions.RequestException as e:
        # Handle exceptions related to network or request errors
        print(f"Error downloading file from {url}: {e}")
    except IOError as e:
        # Handle exceptions related to file I/O errors
        print(f"Error saving file to {save_path}: {e}")

# 格式化打印json（方便阅读）
def print_json(data):
    """
    打印参数。如果参数是有结构的（如字典或列表），则以格式化的 JSON 形式打印；
    否则，直接打印该值。
    """
    import json
    if hasattr(data, 'model_dump_json'):
        data = json.loads(data.model_dump_json())

    if isinstance(data, (list)):
        for item in data:
            print_json(item)
    elif (isinstance(data, (dict))):
        print(json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ))
    else:
        print(data)
