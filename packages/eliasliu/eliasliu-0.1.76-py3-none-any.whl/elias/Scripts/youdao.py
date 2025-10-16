# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 20:28:51 2021

@author: Administrator
# """
# import requests
# import json
# def translate(word = "数据分析师"):
#     url='http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'
#     #使用post需要一个链接
#     data={'i': word,
#           'from': 'zh-CHS',# 'AUTO'
#           'to': 'en',# 'AUTO'
#           'smartresult': 'dict',
#           'client': 'fanyideskweb',
#           'doctype': 'json',
#           'version': '2.1',
#           'keyfrom': 'fanyi.web',
#           'action': 'FY_BY_REALTIME',
#           'typoResult': 'false'}
#     #将需要post的内容，以字典的形式记录在data内。
#     r = requests.post(url, data)
#     #post需要输入两个参数，一个是刚才的链接，一个是data，返回的是一个Response对象
#     answer=json.loads(r.text)
#     #你可以自己尝试print一下r.text的内容，然后再阅读下面的代码。
#     result = answer['translateResult'][0][0]['tgt']
#     return result

#from langdetect import detect
#from langdetect import detect_langs
#from langdetect import DetectorFactory
#DetectorFactory.seed = 0
#detect(result)
#detect_langs(result)
#import langid
#langid.classify(result)

from hashlib import md5
 
import requests
 
 
def get_form_data(text, le):
    """
    构建表单参数
    :param :text:翻译内容
    :param :le:目标语言
    """
    # 固定值
    w = 'Mk6hqtUp33DGGtoS63tTJbMUYjRrG1Lu'
    v = 'webdict'
    _ = 'web'
 
    r = text + v
    time = len(r) % 10
    o = md5(r.encode('utf-8')).hexdigest()
    n = _ + text + str(time) + w + o
    f = md5(n.encode('utf-8')).hexdigest()
 
    form_data = {
        'q': text,
        'le': le,
        't': time,
        'client': _,
        'sign': f,
        'keyfrom': v,
    }
    return form_data
 
 
def translate(query, to_lan = 'en'):
    """
    启动翻译
    :param query: 翻译内容
    :param to_lan: 目标语言
    # 有道词典语言选项
    lang = {
        '自动检测语言': '',
        '中英': 'en',
        '中法': 'fr',
        '中韩': 'ko',
        '中日': 'ja',
    }
    :return:
    """
    # 有道词典网页请求参数
    url = 'https://dict.youdao.com/jsonapi_s?doctype=json&jsonversion=4'
    form_data = get_form_data(query, to_lan)
 
    try:
        res = requests.post(url, data=form_data).json()
        # result = res['fanyi']['tran']
        # 取第一个网络释义
        try:
            result = res['fanyi']['tran']
        except:
            result = res['web_trans']['web-translation'][0]['trans'][0]['value']
        return result
    except Exception as e:
        print('翻译失败：', e)
        return '翻译失败：' + query
 


def is_chinese(s = '数据分析师'):
    r=0
    try:
        for i in s:
            if u'\u4e00' <= i <= u'\u9fff':
                r=r+1
        if r>0:
            return True
        else:
            return False
    except:
        return False


def get_name(s = '数据分析师'):
    # 检测关键字是否存在中文，并将中文翻译成英文
    # import youdao as yd
    if is_chinese(s)==True:
        rs = translate(s)
    else:
        rs = s
    name = rs.replace(" ","_")
    return name