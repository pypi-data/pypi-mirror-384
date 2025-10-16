# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 15:50:35 2023

@author: elias
"""

# 如果终端显示乱码可以打开注释
# import sys
# import locale
# import codecs

# preferred_encoding = locale.getpreferredencoding()
# sys.stdout = codecs.getwriter(preferred_encoding)(sys.stdout.detach())

# ======================================================================

import argparse        
from elias import usual as u 
from elias.datax import auto_create_table as act 
from elias.datax import job 
logger = u.logger()

def run(data):
    split = data.get("split")
    where = data.get("where")
    if split == None:
        split = ''
    else:
        split = str(split)
        
    if  where == None:
        where = ''
    else:
        where = str(where)
    
    
    origin_hosts = u.all_hosts(name = data.get('sourcename'))
    origin_table_name = data.get('sourcetable')
    
    target_hosts = u.all_hosts(name = data.get('targetname'))
    target_table_name = data.get('targettable')
    
    if data.get('channel') == None:
        channel = 6
    else:
        channel = int(data.channel)
    
    if data.get('record') == None:
        record = 0
    else:
        record = int(data.record)
        
    
    if data.get('percentage') == None:
        percentage = 0
    else:    
        percentage = float(data.percentage)
    
    try:
        act.auto_create(origin_table_name,origin_hosts,target_table_name,target_hosts)
        file_path = job.datax_json_config(origin_table_name,origin_hosts,target_table_name,target_hosts,channel,record,percentage,split,where)
        return file_path
    
    except ConnectionError as ce:
        logger.error(str(ce))
    except ValueError as ve:
        logger.error(str(ve))
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

def main(args):
    if args.split == None:
        split = ''
    else:
        split = str(split)
        
    if args.where == None:
        where = ''
    else:
        where = str(where)
    
    origin_hosts = u.all_hosts(name = args.sourcename)
    origin_table_name = args.sourcetable
    
    target_hosts = u.all_hosts(name = args.targetname)
    target_table_name = args.targettable
    
    if args.channel == None:
        channel = 6
    else:
        channel = int(args.channel)
    
    if args.record == None:
        record = 0
    else:
        record = int(args.record)
        
    
    if args.percentage == None:
        percentage = 0
    else:    
        percentage = float(args.percentage)
    
    try:
        act.auto_create(origin_table_name,origin_hosts,target_table_name,target_hosts)
        job.datax_json_config(origin_table_name,origin_hosts,target_table_name,target_hosts,channel,record,percentage,split,where)

    except ConnectionError as ce:
        logger.error(str(ce))
    except ValueError as ve:
        logger.error(str(ve))
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replicate database table structure and create corresponding tables in the target database")
    parser.add_argument('-s', '--sourcename', required=True, help="Source database name")
    parser.add_argument('-st', '--sourcetable', required=True, help="Source table name")
    parser.add_argument('-sp', '--split', required=True, help="Source split cloumn")
    parser.add_argument('-w', '--where', required=True, help="Source table where")
    parser.add_argument('-t', '--targetname', required=True, help="Target database name")
    parser.add_argument('-tt', '--targettable', required=True, help="Target table name")
    parser.add_argument('-c', '--channel', required=False, help="JSON config : channel")
    parser.add_argument('-r', '--record', required=False, help="JSON config : record")
    parser.add_argument('-p', '--percentage', required=False, help="JSON config : percentage")
    args = parser.parse_args()

    main(args)

