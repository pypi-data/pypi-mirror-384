# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 11:05:20 2023

@author: Administrator
"""



def environ_get(env_variable_name = "elias_config"):
    import os
    # 读取单个环境变量
    env_value = os.environ.get(env_variable_name)
    return env_value

def file_import(file_path,module_name):
    import importlib.util
    
    # 指定文件路径
    # file_path = os.path.join(env_value,'config.py')
    
    # 指定模块名
    # module_name = "my_module"
    
    # 创建一个模块规范
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    
    # 根据规范创建一个模块对象
    my_module = importlib.util.module_from_spec(spec)
    
    # 将模块添加到sys.modules中
    spec.loader.exec_module(my_module)
    
    # 调用模块中的函数
    # result = my_module.hosts
    # print(result)
    return my_module

def elias_config():
    # import importlib.util
    import os
    
    env_value = environ_get(env_variable_name = "elias_config")
    
    # 指定文件路径
    file_path = os.path.join(env_value,'config.py')
    
    elias_config = file_import(file_path,'elias_config')
    
    # 调用模块中的函数
    # result = my_module.hosts
    # print(result)
    return elias_config


# elias_config = elias_config()
# elias_config.hosts
