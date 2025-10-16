# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 13:06:43 2023

@author: Elias.Liu
"""


# from elias import config
from elias import usual as u
from elias.datax import reader as dr
from elias.datax import writer as dw

logger = u.logger()

from elias import config_env_variable as ev
config_path = ev.environ_get()
config = ev.elias_config()

def datax_inner_path(path):
    import os 
    datax_path = config.datax_path
    final_path = os.path.join(datax_path,f"{path}")
    return final_path


def job_dic(origin_table_name,origin_hosts,target_table_name,target_hosts,channel=6,record=0,percentage=0.02,split="",where=""):
    job = {
        "job": {
            "setting": {
                "speed": {
                    "channel": channel
                },
                "errorLimit": {
                    "record": record,
                    "percentage": percentage
                }
            },
            "content": [{
                "reader": dr.reader(origin_table_name,origin_hosts,split,where)["reader"],
                "writer": dw.writer(target_table_name,target_hosts)["writer"]
            }]
        }
    }
    return job


def get_filename(target_table_name,target_hosts):
    if target_hosts['dbtype'] == 'maxcompute':
        filename = f"【{target_hosts['dbtype']}】{target_hosts['project_name']}.{target_table_name}.json"
        
    else:
        filename = f"【{target_hosts['dbtype']}】{target_hosts['db']}.{target_table_name}.json"
    logger.info(f"已生成文件名：{filename}" )
    return filename

def get_file(job_dic,filename='test.json',output_path=datax_inner_path('job')):
    
    import os
    import json
    
    # Generate JSON string from the datax_config dictionary
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    file_path = os.path.join(output_path,f"{filename}")
    
    try:
        u.write_json_to_file(job_dic, file_path)
        logger.info(f"{filename}.json\n\n{json.dumps(job_dic, indent=4)}\n\n" )
        logger.info(f"JSON数据已写入文件：{file_path}" )
    except Exception as e:
        logger.error(f"Failed to generate DataX JSON configuration file: {str(e)}")
        raise e
    return file_path


def datax_json_config(origin_table_name,origin_hosts,target_table_name,target_hosts,channel=6,record=0,percentage=0.02,split="",where=""):
    try:
        logger.info("开始生成json文件内容……" )
        job = job_dic(origin_table_name,origin_hosts,target_table_name,target_hosts,channel,record,percentage,split,where)
        logger.error(f"json文件内容生成成功: {job}\n")
    except Exception as e:
        logger.error(f"json文件内容生成失败: {str(e)}\n")
        raise e
    
    
    try:
        logger.info("正在生成json文件名……" )
        filename = get_filename(target_table_name,target_hosts)
        logger.info(f"文件名生成完成：{filename}\n" )
    except Exception as e:
        logger.info(f"文件名生成失败：{str(e)}\n" )
        raise e
        
        
    try:
        logger.info(f"开始将 JSON数据 写入文件：{filename}" )
        file_path = get_file(job,filename)
        logger.info(f"JSON文件写入完成：{file_path}\n" )
    except Exception as e:
        logger.info(f"JSON文件写入失败：{str(e)}\n" )
        raise e

    return file_path




        



