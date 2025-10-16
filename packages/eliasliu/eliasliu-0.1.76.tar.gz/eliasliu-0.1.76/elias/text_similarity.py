# -*- coding: utf-8 -*-
"""
Created on Thu May 23 10:46:04 2024

@author: Administrator
"""

import re
import math
import jieba

def preprocess_text(text):
    """
    预处理文本：保留各种语言的字符
    """
    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)  # 保留字母、数字、标点和空格
    return text

def chinese_word_segmentation(text):
    """
    对中文文本进行分词
    """
    seg_list = jieba.cut(text)
    return " ".join(seg_list)

def compute_cosine_similarity(text1, text2):
    """
    计算两个文本的余弦相似度
    """
    # 预处理文本
    # text1 = preprocess_text(text1)
    # text2 = preprocess_text(text2)
    
    # 中文分词
    text1 = chinese_word_segmentation(text1)
    text2 = chinese_word_segmentation(text2)
    
    # 将文本转换为字符列表
    chars1 = text1.split()
    chars2 = text2.split()
    
    # 创建字符频率字典
    char_freq1 = {char: chars1.count(char) for char in set(chars1)}
    char_freq2 = {char: chars2.count(char) for char in set(chars2)}
    
    # 计算字符频率向量的长度
    vector_length1 = math.sqrt(sum(freq**2 for freq in char_freq1.values()))
    vector_length2 = math.sqrt(sum(freq**2 for freq in char_freq2.values()))
    
    # 计算点积
    dot_product = sum(char_freq1[char] * char_freq2[char] for char in set(chars1) if char in set(chars2))
    
    # 计算余弦相似度
    cosine_similarity = dot_product / (vector_length1 * vector_length2 + 1e-10)  # 避免除零错误
    
    return cosine_similarity


if __name__ == '__main__':
    # 示例用法
    text1 = "我爱Python编程!"
    text2 = "我喜欢编程！"
    similarity = compute_cosine_similarity(text1, text2)
    print("text1:", text1)
    print("text2:", text2)
    print("Similarity:", similarity)




