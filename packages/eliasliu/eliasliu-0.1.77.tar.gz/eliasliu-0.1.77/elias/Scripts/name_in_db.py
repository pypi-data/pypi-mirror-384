# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 13:12:47 2021

@author: Administrator
"""

# def name_get(city = "上海",job = "数据分析师"):
    
#     # 确认搜索关键字
#     city_chose = city
   
#     # 选择城市
#     import city_choose as cc
#     city_num = cc.city_choose(city_chose)
    
    
#     # 检测关键字是否存在中文，并将中文翻译成英文
#     import youdao as yd
#     if yd.is_chinese(city_chose)==True:
#         city_tr = yd.translate(city_chose)
#     else:
#         city_tr = city_chose
        
#     if yd.is_chinese(job)==True:
#         job_tr = yd.translate(job)
#     else:
#         job_tr = job
        
#     # 输出Mysql中表名
#     name_in_db = ('{}_{}').format(city_tr.replace(" ","_"),job_tr.replace(" ","_"))
#     print(name_in_db)
#     return name_in_db

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
    print(name_in_db)
    return name_in_db