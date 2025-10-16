# -*- coding: utf-8 -*-
"""
Created on Tue May 28 17:25:31 2024

@author: Administrator
"""

from PIL import Image

def image_difference(image1, image2):
    """
    检查两张图片的像素差异
    :param image1: 图片1
    :param image2: 图片2
    :return: 差异像素的数量
    """
    diff_count = 0
    width, height = image1.size
    for x in range(width):
        for y in range(height):
            pixel1 = image1.getpixel((x, y))
            pixel2 = image2.getpixel((x, y))
            if pixel1 != pixel2:
                diff_count += 1
    return diff_count

def main(image1, image2):
    # 加载图片A和图片B
    image_a = Image.open(image1)
    image_b = Image.open(image2)

    # 检查图片大小是否一致，如果不一致，调整大小
    if image_a.size != image_b.size:
        image_b = image_b.resize(image_a.size)

    # 检查像素差异
    diff_count = image_difference(image_a, image_b)

    if diff_count == 0:
        print("图片A和图片B相同")
        return 0
    else:
        print("图片A和图片B不同，差异像素数量为:", diff_count)
        return diff_count

if __name__ == "__main__":
    image1 = r"C:\Users\Administrator\Pictures\1.jpg"  # 图片 B 的路径
    image2 = r"C:\Users\Administrator\Pictures\2.jpg" # 合成后的图片路径
    main(image1, image2)