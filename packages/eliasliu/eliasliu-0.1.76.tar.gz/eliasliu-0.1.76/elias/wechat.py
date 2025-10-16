# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 11:58:44 2022

@author: elias.liu
"""


#-------------------------------------------------------------------------------



# from elias import config_env_variable as ev
# config_path = ev.environ_get()
# config = ev.elias_config()

from elias import config_env_variable as ev
from loguru import logger
try:
    config_path = ev.environ_get()
    config = ev.elias_config()
    print('elias_config配置导入成功')
except:
    logger.warning('elias_config环境变量导入失败！请检查elias_config是否配置，如果已经配置完成。请重启后再试。')


def robots(name='all'):
    all_robots = config.robots
    if name == 'all':
        robots = list(all_robots)
    else:
        robots = all_robots[name]
    return robots

#-------------------------------------------------------------------------------

import datetime
import time
def Stamp_to_Datetime(timeStamp = int(time.time())):
    import time
    timeArray = time.localtime(timeStamp)
    DateTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    # print(DateTime)
    return DateTime

def Stamp_to_Date(timeStamp = int(time.time())):
    import time
    timeArray = time.localtime(timeStamp)
    DateTime = time.strftime("%Y-%m-%d", timeArray)
    # print(DateTime)
    return DateTime

def Stamp_to_Hour(timeStamp = int(time.time())):
    import time
    timeArray = time.localtime(timeStamp)
    DateTime = time.strftime("%H:%M:%S", timeArray)
    # print(DateTime)
    return DateTime

def to_hour(n=0):
    result = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    a = result + datetime.timedelta(seconds=n)
    return a.strftime("%H:%M:%S")

#-------------------------------------------------------------------------------

# 机器人
def wechat_markdown(title, content, user, key):
    '''
    

    Parameters
    ----------
    title : Str        标题.
    content : Str        正文.
    user : Str        @某人.
    key : Str        企业微信机器人key.

    Returns
    -------
    None.

    '''
    import requests
    import json

    mark = {'msgtype': 'markdown',
            'markdown': {'content':'''# {}\n\n{}\n<@{}>'''.format(title,content,user)}}

    headers = {'Content-Type': 'application/json'}
    response = requests.post(url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=' + key,
                             headers=headers,
                             data=json.dumps(mark))
    print(response.text)

def run_warning(title = "警报",text = "test", user='',key = ''):
    # 1.先导入库：
    # import datetime
    from datetime import datetime

    #设置模板
    content = '''   ><font color=\"warning\">{}</font>\n
                    >当前时间：\n<font color=\"comment\">{}</font>\n
            '''.format(text,datetime.now().strftime('%Y-%m-%d %H:%M:%S'))# strftime()，功能：将时间格式化！！！，或者说格式化一个时间字符串
    #发送消息
    wechat_markdown(title=title, content=content, user = user,key = key)
    print('Warning success！')



def run_report(title = "XX任务 - 执行日报",text = "test",fail_count=0,success_count=0,all_count=0, user='yiting.liu',key = ''):
    from datetime import datetime
    content = '''   >**异常任务数：**<font color=\"warning\">{}</font>\n
                    >成功任务数：<font color=\"comment\">{}</font>\n
                    >总任务数：<font color=\"comment\">{}</font>\n
                    >任务明细：\n<font color=\"comment\">{}</font>\n
                    >执行时间：\n<font color=\"comment\">{}</font>\n
            '''.format(fail_count,success_count,all_count,text,datetime.now().strftime('%Y-%m-%d %H:%M:%S'))# strftime()，功能：将时间格式化！！！，或者说格式化一个时间字符串
    #发送消息
    wechat_markdown(title=title, content=content, user=user ,key = key)
    print('Warning success！')

def warning_mission(mission='mission_test',plan='test',e='',key = ''):
    warn = 'Mission：{}\nPlan：{}\n \n执行失败！\n \n{}'.format(mission,plan,e)
    run_warning(title = f"{mission} - 异常报警",text = warn,key = key)




#-------------------------------------------------------------------------------
    
def wechat_file(file_path = 'hello world.txt', key = ''):
    '''
    所有文件size必须大于5个字节
    ----------
    图片（image）：10MB，支持JPG,PNG格式
    语音（voice） ：2MB，播放长度不超过60s，仅支持AMR格式
    视频（video） ：10MB，支持MP4格式
    普通文件（file）：20MB

    Parameters
    ----------
    file_path : TYPE, optional
        DESCRIPTION. The default is 'hello world.txt'.
    key : TYPE, optional
        DESCRIPTION. The default is personal.
    i : 0 - output(导表专用)；1 - personal
    Returns
    -------
    None.

    '''

    import os 
    if file_path == 'hello world.txt':
        f = 'hello python!\nhello world!\n'
        f1 = open('hello world.txt','w')
        f1.write('hello python!\nhello world!\n')
        f1.close()
        path = os.getcwd()
        file_path = os.path.join(path,file_path)
        # file_path = path+'\\'+file_path
    else:
        if '\\' in file_path or '/' in file_path:
            file_path = file_path
        else:
            path = os.getcwd()
            file_path = os.path.join(path,file_path)
            # file_path = path+'\\'+file_path            
        
    from copy import copy
    import json
    from urllib3 import encode_multipart_formdata
    import requests
    wx_upload_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={}&type=file'.format(key)
    file_name = file_path.split("\\")[-1].split("/")[-1]
    with open(file_path, 'rb') as f:
        length = os.path.getsize(file_path)
        data = f.read()
    headers = {"Content-Type": "application/octet-stream"}
    params = {
        "filename": file_name,
        "filelength": length,
    }
    file_data = copy(params)
    file_data['file'] = (file_path.split("\\")[-1:][0].split("/")[-1], data)
    encode_data = encode_multipart_formdata(file_data)
    file_data = encode_data[0]
    headers['Content-Type'] = encode_data[1]
    r = requests.post(wx_upload_url, data=file_data, headers=headers)
    print(r.text)
    media_id = r.json()['media_id']
    msgtype = r.json()['type']
    

    import requests
    # 要求文件大小在5B~20M之间，媒体文件类型，分别有图片（image）、语音（voice）、视频（video），普通文件（file）
    # headers = {"Content-Type": "text/plain"}
    url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={}'.format(key)

    mark = {
            "msgtype": msgtype,
            "file": {
                     "media_id": media_id
                     }
            }  

    response = requests.post(url=url,
                             headers=headers,
                             data=json.dumps(mark))
    print(response.text)
    print('文件 %s 发送成功'%file_name)
    # os.remove(file_path)
 
#-------------------------------------------------------------------------------

# 企微发送图片
def wechat_image(image_path, user='yiting.liu', key = ''):
    import requests
    import json
    import hashlib
    f = open(image_path, 'br')
    fcont = f.read()
    m2 = hashlib.md5(fcont)
    md5_val = m2.hexdigest()
    
    import base64
    base64_data=str(base64.b64encode(fcont),encoding='utf-8')
    
    url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=' + key
    headers = {'Content-Type': 'application/json'}
    r=requests.post(url,headers=headers,data=json.dumps({"msgtype":"image","image":{"base64":base64_data,"md5":md5_val}}))
    print(r.text)
    
# 机器人
def wechat_news(title='中秋节礼品领取', description='今年中秋节公司有豪礼相送',url = "www.qq.com",pic_url = "http://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png", user='yiting.liu', key=''):
    import requests
    import json

    mark = {
    "msgtype": "news",
    "news": {
       "articles" : [
           {
               "title" : title,
               "description" : description,
               "url" : url,
               "picurl" : pic_url
           }
        ]
    }
}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=' + key,
                             headers=headers,
                             data=json.dumps(mark))
    print(response.text)



# ==================================================================================
import json
import urllib
import requests
import urllib.request

def corp_info(corp_name):
    info = {'kk':{'coreID':'ww7dbfc0a99d9921d2',  #企业ID，在管理后台获取
                  'apisecret':'WVRUmAQCyUUQNoj4uBDX-vQsIckcp8FIig7rt5LJa84'}#客户 - 自建应用的Secret，每个自建应用里都有单独的secret
        }
    return info[corp_name]
# coreID = corp_info('kk')['coreID']
# apisecret = corp_info('kk')['apisecret']


def getToken(coreID, apisecret):
    """功能获取access_token
    corpid:企业ID
    corpsecret:应用密钥
    """
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (coreID, apisecret)
    req = urllib.request.Request(url, headers=headers)
    result = urllib.request.urlopen(req)
    access_token = json.loads(result.read())
    # print(access_token['access_token'])
    return access_token['access_token']
# access_token = getToken(coreID, apisecret)


def get_departmentid(access_token):
    """
    功能:获取部门列表
    """
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
    url = "https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=" + access_token
    req = urllib.request.Request(url, headers=headers)
    result = urllib.request.urlopen(req)
    departments = json.loads(result.read())
    departmentlist = departments['department']
    departmentid_list = []
    for i in departmentlist:
        departmentid_list.append(i['id'])
    return departmentid_list
# get_departmentid(access_token)



def get_department_user_simplelist(access_token,departmentid_list):
    """
    功能:部门成员列表
    """
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
    # userlist_all = []
    for department_id in departmentid_list:
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={}&department_id={}".format(access_token,department_id)
        req = urllib.request.Request(url, headers=headers)
        result = urllib.request.urlopen(req)
        userlist = json.loads(result.read())
    return userlist['userlist']
# get_department_user_simplelist(access_token,departmentid_list = get_departmentid(access_token))

def get_department_userlist(access_token,departmentid_list):
    """
    功能:部门成员详细信息列表
    """
    fetch_child = 1 # 1/0：是否递归获取子部门下面的成员
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
    userlist_all = []
    for department_id in departmentid_list:
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={}&department_id={}&fetch_child={}".format(access_token,department_id,fetch_child)
        req = urllib.request.Request(url, headers=headers)
        result = urllib.request.urlopen(req)
        userlist = json.loads(result.read())

        for i in userlist['userlist']:
            userid = i['userid']
            name = i['name']
            department = str(i['department'])
            position = i['position']
            mobile = i['mobile']
            if i['gender']=='1':
                gender = '男'
            elif i['gender']=='2':
                gender = '女'
            else:
                gender = '未知'
            email = i['email']
            try:
                attrs = i['extattr']['attrs'][0]
                work_num = attrs['value']
            except:
                work_num = ''
            useridlist = []
            useridlist.append([userid,name,department,position,mobile,gender,email,work_num])
            userlist_all = userlist_all+useridlist
    return userlist_all#,tagid['tagname']