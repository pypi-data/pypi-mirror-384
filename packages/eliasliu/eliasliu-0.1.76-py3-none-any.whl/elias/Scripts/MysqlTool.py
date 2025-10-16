# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 16:54:08 2023

@author: Administrator
"""

import pymysql
from elias import usual as u



class MysqlTool(object):

    def __init__(self,kwargs):
        # MYSQL_HOST = hosts['host']
        # MYSQL_PORT = hosts['port']
        # MYSQL_DBNAME = hosts['db']
        # MYSQL_USER = hosts['name']
        # MYSQL_PASSWD = hosts['code']
        
        self.connect = pymysql.connect(
            host = kwargs.get('host'),
            port = int(kwargs.get('port')),
            db = kwargs.get('db'),
            user = kwargs.get('name'),
            passwd = kwargs.get('code'),
            charset = 'utf8',
            use_unicode = True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connect.close()

    def insert(self, sql):
        cursor = self.connect.cursor()
        cursor.execute(sql)
        self.connect.commit()
        cursor.close()

    def select(self, sql):
        cursor = self.connect.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        data = list(data)
        if len(data) > 0:
            data = [list(da) for da in data]
        return data

    def select_one(self, sql):
        cursor = self.connect.cursor()
        cursor.execute(sql)
        data = cursor.fetchone()
        cursor.close()
        return data

    def select2dict(self, sql):
        cursor = self.connect.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        index_dict = dict()
        index = 0
        for desc in cursor.description:
            index_dict[desc[0]] = index
            index = index + 1
        res = []
        for da in data:
            resi = dict()
            for ix in index_dict:
                resi[ix] = da[index_dict[ix]]
            res.append(resi)
        cursor.close()
        return res

    def select_df(self, sql):
        cursor = self.connect.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        data = list(data)
        if len(data) > 0:
            data = [list(da) for da in data]
        import pandas as pd
        df = pd.DataFrame(data)
        return df

    def create_table(self,keys,table_name):
        sql = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)
        for key in keys:
            sql += "{} varchar(255),".format(key)
        sql = sql[:-1] + ")"
        self.insert(sql)
        
    def ddl(self, sql):
       cursor = self.connect.cursor()
       cursor.execute(sql)
       self.connect.commit()
       cursor.close()   
       
MysqlTool1 = MysqlTool(u.all_hosts('om'))

df = MysqlTool1.select_df('show tables')
