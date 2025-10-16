# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 18:13:45 2024

@author: Administrator
"""


def tools(name,description,parameter):
    tools = [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters":parameter,
            },
        }
    ]
    return tools
    

def parameter(required,*args):
    
    # 检查required参数是否为列表
    if not isinstance(required, list):
        raise TypeError("required参数必须是列表类型")
        
    # 检查参数数量是否为偶数，以确保每个键都有对应的值
    if len(args) % 2 != 0:
        raise ValueError("参数数量必须是偶数，以确保每个键都有对应的值")
    
    # 使用字典推导式生成字典，同时确保所有required的键都被包含
    dict_items = [(key, value) for key, value in zip(args[::2], args[1::2])]
    result_dict = dict(dict_items)
    
    # 检查required列表中的键是否都在字典中
    for key in required:
        if key not in result_dict:
            raise KeyError(f"缺少必需的键: {key}")
            
    parameter = {
        "type": "object",
        "properties": result_dict,
        "required": ["location"],
    }
    return parameter
    
def properties(ptype = 'string',description=None,enum=None):
    properties = {
                    "type": ptype,
                    "description": description,
                }
    if enum!=None or description!=None:
        if enum!=None:
            properties['enum']=enum
        if description!=None:
            properties['description']=description
    else:
        raise ValueError("至少需要提供一个参数：enum 或 description")
    return properties
    
if __name__ == '__main__':
    
    # 配置 properties
    name_1 = 'location'
    properties_1 = properties(ptype = 'string',description='The city and state, e.g. San Francisco, CA',enum=None)
    name_2 = 'unit'
    properties_2 = properties(ptype = 'string',enum=["celsius", "fahrenheit"])
    
    # 配置 parameter
    required = ['location']
    parameter = parameter(required,name_1,properties_1,name_2,properties_2)
    
    # 配置 tools
    name = 'get_current_weather'
    description = 'Get the current weather in a given location'
    tools = tools(name,description,parameter)
