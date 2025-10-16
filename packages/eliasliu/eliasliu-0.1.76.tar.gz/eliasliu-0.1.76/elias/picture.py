# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 19:21:49 2024

@author: Isabel.Xu
"""

from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np


def new_pic_name(pic_origin):
    from elias import usual as u
    
    pic_name = u.file_get(path=pic_origin)
    pic_name_new = "repaired_"+pic_name
    
    import os 
    pic_dir = os.path.dirname(pic_origin)
    pic_target = os.path.join(pic_dir,pic_name_new)
    return pic_target

def adjust_temperature(image, temp):
    """
    调整图片的色温。
    :param image: OpenCV图像对象
    :param temp: 色温调整量，负值为冷色调，正值为暖色调
    """
    # 根据图像大小创建一个全1的数组
    warmer = np.ones(image.shape, dtype=np.uint8) * abs(int(temp * 255 / 100))
    # 根据色温是增加还是减少来调整蓝色或红色通道
    if temp < 0:
        image[:, :, 0] = cv2.add(image[:, :, 0], warmer[:, :, 0])
    else:
        image[:, :, 2] = cv2.add(image[:, :, 2], warmer[:, :, 2])
    return image

def enhance_highlights_shadows(image, alpha_highlights, beta_shadows):
    """
    增强图片中的高光和阴影。
    :param image: OpenCV图像对象
    :param alpha_highlights: 高光增强系数
    :param beta_shadows: 阴影增强系数
    """
    # 将图像转换为HSV颜色空间
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # 创建高光区域的掩膜
    mask = cv2.inRange(hsv, (0, 0, 255*0.8), (180, 255, 255))
    inv_mask = cv2.bitwise_not(mask)
    # 调整高光区域
    image_highlights = cv2.addWeighted(image, alpha_highlights, image, 0, 0)
    image = np.where(mask[:,:,None] == 255, image_highlights, image)
    # 调整阴影区域
    image_shadows = cv2.addWeighted(image, beta_shadows, image, 0, 0)
    image = np.where(inv_mask[:,:,None] == 255, image_shadows, image)
    return image

# def adjust_image(image_path, output_path):
#     """
#     调整图片的亮度、对比度、饱和度、高光、色温、阴影和锐化。
#     :param image_path: 输入图片的路径
#     :param output_path: 输出图片的路径
#     """
#     # 使用Pillow打开图片
#     img = Image.open(image_path)

#     # 调整亮度（增加15%）
#     img = ImageEnhance.Brightness(img).enhance(1.10)
#     # 调整对比度（增加10%）
#     img = ImageEnhance.Contrast(img).enhance(1.10)
#     # 调整饱和度（增加25%）
#     img = ImageEnhance.Color(img).enhance(1.25)
#     # 调整锐化（增加76%）
#     img = ImageEnhance.Sharpness(img).enhance(1.76)

#     # 将Pillow图像转换为OpenCV格式
#     img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

#     # 调整高光（增强系数1.2）和阴影（增强系数1.2）
#     # img_cv = enhance_highlights_shadows(img_cv, 1.2, 1.2)

#     # 调整色温（降低10单位）
#     img_cv = adjust_temperature(img_cv, -5)

#     # 将OpenCV图像转换回Pillow格式
#     img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

#     # 保存调整后的图片
#     img_pil.save(output_path)


# def ins_adjust_image(image_path, output_path):
#     # 使用Pillow打开图片
#     img = Image.open(image_path)

#     # 调整亮度（增加10%）
#     img = ImageEnhance.Brightness(img).enhance(1.10)
#     # 调整对比度（增加30%）
#     img = ImageEnhance.Contrast(img).enhance(1.20)
#     # 调整饱和度（增加20%）
#     img = ImageEnhance.Color(img).enhance(1.20)
#     # 调整锐化（增加50%）
#     img = ImageEnhance.Sharpness(img).enhance(1.50)

#     # 将Pillow图像转换为OpenCV格式
#     img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

#     # 调整高光（增强系数1.15）和阴影（增强系数1.15）
#     # img_cv = enhance_highlights_shadows(img_cv, 1.15, 1.15)

#     # 调整色温（降低5单位）
#     img_cv = adjust_temperature(img_cv, -5)

#     # 将OpenCV图像转换回Pillow格式
#     img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

#     # 保存调整后的图片
#     img_pil.save(output_path)


def adjust_image_parameters(image_path, output_path, brightness=1, contrast=1, color=1, sharpness=1, alpha_highlights=1, beta_shadows=1, temperature=0):
    """
    调整图片的各项参数。
    :param image_path: 输入图片的路径。
    :param output_path: 输出图片的路径。
    :param brightness: 亮度调整比例。
    :param contrast: 对比度调整比例。
    :param color: 饱和度调整比例。
    :param sharpness: 锐化调整比例。
    :param alpha_highlights: 高光增强系数。
    :param beta_shadows: 阴影增强系数。
    :param temperature: 色温调整值。
    """
    # 使用Pillow打开图片并调整
    img = Image.open(image_path)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(color)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)

    # 将Pillow图像转换为OpenCV格式
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 调整高光和阴影
    img_cv = enhance_highlights_shadows(img_cv, alpha_highlights, beta_shadows)

    # 调整色温
    img_cv = adjust_temperature(img_cv, temperature)

    # 将OpenCV图像转换回Pillow格式
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    # 保存调整后的图片
    img_pil.save(output_path)

def apply_ins_style(image_path, output_path):
    """
    将图片调整为INS风格。
    :param image_path: 输入图片的路径。
    :param output_path: 输出图片的路径。
    """
    adjust_image_parameters(image_path, output_path, 
                            brightness=1.10,  # 亮度调整比例
                            contrast=1.20,  # 对比度调整比例
                            color=1.20,  # 饱和度调整比例
                            sharpness=1.50,  # 锐化调整比例
                            # alpha_highlights=1.15,  # 高光增强系数
                            # beta_shadows=1.15,  # 阴影增强系数
                            temperature=-5 # 色温调整值
                            )


def adjust_image(image_path,output_path,style = "ins"):
    if output_path == None:
        output_path = new_pic_name(image_path)
    else:
        pass
    
    if style == "ins":
        apply_ins_style(image_path,output_path)
    else:
        pass
    
    
def adjust_image_folder(pic_origin_folder,pic_target_folder):
    from elias import usual as u
    import os,time
    from loguru import logger
    
    start = time.time()
    
    folder_num = 0
    pic_num = 0
    old_pic_num = 0
    new_pic_num = 0
    old_folder_num = 0
    new_folder_num = 0
    
    # 列出所有文件夹
    folder_list = u.list_folder(pic_origin_folder)
    folder_num = len(folder_list)
    logger.info(f'\n路径：{pic_origin_folder} \n内部共有{len(folder_list)}个文件夹 ')
    
    for i in range(len(folder_list)):
        logger.info(f'\n\n=================={i+1}=================\n')
        folder = folder_list[i]
        logger.info(f'\n开始识别第{i+1}个文件夹 ; 文件夹：{folder} ')
        folder_path = os.path.join(pic_target_folder,folder+'_repaired')
        
        pic_target_daily_folder = folder_path
        if not os.path.exists(pic_target_daily_folder):
            new_folder_num =new_folder_num + 1
            os.makedirs(pic_target_daily_folder)
            logger.warning(f"\n完成创建，Folder created at {pic_target_daily_folder}")
        else:
            old_folder_num = old_folder_num + 1
            logger.info(f"\n文件夹已存在，Folder already exists at {pic_target_daily_folder}")
            
            
        # 列出所有文件
        pic_origin_daily_folder = os.path.join(pic_origin_folder,folder)
        # u.create_folder_if_not_exists(pic_target_daily_folder)
        pics = u.list_file(pic_origin_daily_folder)
        pic_num = pic_num + len(pics)
        
        
        logger.info(f'\n路径：{pic_origin_daily_folder} \n内部共有{len(pics)}张图片 ')
        logger.info('\n开始进行“图片调整” ...')
        for j in range(len(pics)):
            pic_name = pics[j]
            image_path = os.path.join(pic_origin_daily_folder,pic_name)
            # pic_name = u.file_get(path=image_path)
            pic_name_new = "repaired_"+pic_name
            output_path = os.path.join(pic_target_daily_folder,pic_name_new)
            
            if os.path.exists(output_path):
                old_pic_num = old_pic_num + 1
                logger.info(f'\n图片{j+1}：{pic_name}，结果：{pic_name_new}已存在，直接跳过。')
                pass
            else:
                new_pic_num = new_pic_num + 1
                logger.warning(f'\n图片{j+1}：{pic_name}，结果：{pic_name_new}不存在，开始创建。。。')
                adjust_image(image_path,output_path,style = "ins")
                logger.info(f'\n图片{j+1}，输出图片：{output_path} ，已完成创建。')
    
    end = time.time()
    usetime = str(round(end-start, 2))+ ' seconds'
    if new_pic_num == 0:
        avg_usetime = '0.00 seconds'
    else:
        avg_usetime = str(round((end-start)/new_pic_num, 2))+ ' seconds'
    logger.info(f"\n共计{folder_num}个文件夹，{pic_num}张图片\n\n新文件夹：{new_folder_num} ；老文件夹：{old_folder_num}\n新图片数：{new_pic_num} ；老图片数：{old_pic_num}\n\n总共用时：{usetime} ； 平均每图：{avg_usetime}")




# A_path = 'E:\\头条发布\\logo.jpg'
# B_path = 'E:\\头条发布\\待发头条\\【学者启智】“央视陈世美”水均益抛妻弃女？因娶小13岁美娇妻背负无数骂名\\origin\\9.jpg'
# output_path = 'E:\\头条发布\\待发头条\\【学者启智】“央视陈世美”水均益抛妻弃女？因娶小13岁美娇妻背负无数骂名\\9.jpg'



def merge_images(A_path, B_path, output_path, num_times=5):
    '''
    # # 示例用法
    # A_path = "A.png"  # 图片 A 的路径
    # B_path = "B.png"  # 图片 B 的路径
    # output_path = "output.png"  # 合成后的图片路径

    # merge_images(A_path, B_path, output_path)

    Parameters
    ----------
    A_path : TYPE
        DESCRIPTION.
    B_path : TYPE
        DESCRIPTION.
    output_path : TYPE
        DESCRIPTION.
    num_times : TYPE, optional
        DESCRIPTION. The default is 5.

    Returns
    -------
    None.

    '''
    
    import random
    from PIL import Image
    
    # 打开图片 A 和 B
    A = Image.open(A_path)
    B = Image.open(B_path)

    # 确保图片 A 的模式为 RGBA
    if A.mode != "RGBA":
        A = A.convert("RGBA")

    # 降低 A 图片的透明度到最低
    A = A.point(lambda p: p * 0.001)


    # 获取 A 图片的宽度和高度
    A_width, A_height = A.size

    # 如果 B 图片的宽度或高度小于 A 图片，则将 B 图片等比例缩小一半，直到比 A 大为止
    while B.width < A_width or B.height < A_height:
        B = B.resize((B.width * 2, B.height * 2))

    # 获取 B 图片的宽度和高度
    B_width, B_height = B.size

    # 在 B 图片上随机添加 A 图片
    for _ in range(num_times):
        # 随机生成 A 图片的位置
        x_offset = random.randint(0, B_width - A.width)
        y_offset = random.randint(0, B_height - A.height)

        # 将 A 图片粘贴到 B 图片上
        B.paste(A, (x_offset, y_offset), A)
    
    try:
        # 保存合成后的图片
        B.save(output_path)
    except:
        # 保存合成后的图片为 PNG 格式
        B.save(output_path, "PNG")

def image_difference_check(image1, image2):
    from elias.Scripts import image_check as ic
    diff_count = ic.main(image1, image2)
    return diff_count
    

