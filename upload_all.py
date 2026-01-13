#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量压缩指定文件夹中的所有图片文件并保存到myImg文件夹
"""

import os
import sys
import glob
import time
from PIL import Image


def compress_image_to_avif(input_path, output_path, quality=40):
    """
    将图片压缩为AVIF格式
    :param input_path: 输入图片路径
    :param output_path: 输出AVIF文件路径
    :param quality: 压缩质量（1-100，默认40）
    :return: 成功返回True，失败返回False
    """
    try:
        with Image.open(input_path) as img:
            # 确保图片是RGB模式
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 保存为AVIF格式
            img.save(
                output_path, 
                format='AVIF',
                quality=quality,
                speed=6,
                subsampling='4:4:4',
                chroma_quality=quality,
                overshoot_deringing=True,
                sharpness=0
            )
        return True
    except Exception as e:
        print(f"压缩失败: {str(e)}")
        return False


def process_all_images(folder_path, output_folder):
    """
    批量压缩指定文件夹中的所有图片文件并保存到输出文件夹
    :param folder_path: 输入文件夹路径
    :param output_folder: 输出文件夹路径
    """
    # 支持的图片扩展名
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif']
    
    # 创建输出文件夹（如果不存在）
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有图片文件
    all_files = []
    for ext in image_extensions:
        all_files.extend(glob.glob(os.path.join(folder_path, ext)))
        all_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
    
    total_files = len(all_files)
    print(f"找到 {total_files} 个图片文件")
    
    # 测试模式：只处理前10个文件
    test_mode = False
    max_test_files = 10
    
    # 支持的图片扩展名列表（用于验证）
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    
    processed_count = 0
    failed_count = 0
    
    for i, file_path in enumerate(all_files[:max_test_files] if test_mode else all_files, 1):
        filename = os.path.basename(file_path)
        print(f"\n[{i}/{total_files}] 正在处理: {filename}")
        
        # 获取文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            print(f"跳过: 不支持的文件类型 {ext}")
            continue
        
        # 构造输出文件名
        base_name = os.path.splitext(filename)[0]
        avif_filename = f"{base_name}.avif"
        output_path = os.path.join(output_folder, avif_filename)
        
        # 压缩图片
        try:
            if compress_image_to_avif(file_path, output_path):
                print(f"压缩成功: {avif_filename} 已保存到 {output_folder}")
                processed_count += 1
            else:
                print(f"压缩失败: {filename}")
                failed_count += 1
        except Exception as e:
            print(f"处理异常: {filename} - {str(e)}")
            failed_count += 1
        
        # 每0.5秒处理一次
        time.sleep(0.5)
    
    if test_mode:
        print(f"\n测试模式: 已处理 {processed_count} 个文件，失败 {failed_count} 个，剩余 {max(0, total_files - max_test_files)} 个文件未处理")
    else:
        print(f"\n处理完成! 共处理 {total_files} 个文件，成功 {processed_count} 个，失败 {failed_count} 个")


if __name__ == "__main__":
    # 配置
    folder_path = r"C:\Users\xt350\Downloads\myImg_1768198798854"
    output_folder = r"d:\Desktop\img_tools\myImg"  # 当前目录下的myImg文件夹
    
    process_all_images(folder_path, output_folder)
