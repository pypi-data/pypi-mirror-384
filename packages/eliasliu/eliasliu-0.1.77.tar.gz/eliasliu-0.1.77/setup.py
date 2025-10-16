# -*- coding: utf-8 -*-
"""
Created on Sun Aug  6 16:31:31 2023

@author: Elias.Liu
"""


from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='eliasliu',  # 包名
    version='0.1.77',  # 版本号
    description='A very easy tool to deal your data',  # 包的简要描述
    long_description = long_description,
    # long_description='Data Engineer & Analyst will use',  # 包的详细描述，通常从README文件中读取
    long_description_content_type='text/markdown',  # 详细描述的格式，这里是Markdown
    author='Elias Liu 刘益廷',  # 作者名称
    author_email='liuyiting120@126.com',  # 作者邮箱
    url='https://github.com/tenbj/elias',  # 项目的URL
    packages=find_packages(),  # 包含的包列表，使用find_packages()可以自动查找包含的包
    install_requires=[  # 依赖的其他包（如果有）
        'pymysql',
        # 'pymssql==2.2.5',
        'pandas',
        'sqlalchemy',
        'mysql-connector',
        'requests',
        'mysql-connector-python',
        'impyla',
        # 'clickhouse_sqlalchemy',
        # 'clickhouse_driver',
        # 'odps',
        'bs4',
        'selenium',
        'loguru',
        # 'googletrans',
        'ollama',
        'pillow',
        'opencv-python',
        'jieba',
        'openai',
	'elias_ollama'
    ],
    classifiers=[  # 包的分类标签
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
