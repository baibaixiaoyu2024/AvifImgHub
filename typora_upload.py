#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Typora图片上传工具
基于项目的api_upload接口上传图片
用法：python typora_upload.py "demo1.jpg" "demo2.jpg" ...
作者：白小羽
描述：创作不易，没有收任何费用，还请保留源作者信息，感谢您的关注
"""

import sys
import requests
import os
import json

# API配置
API_URL = "http://154.64.250.117:5000/api/upload"  # 使用远程服务器
API_TOKEN = "your_secure_token_here"  # 与服务端配置的token保持一致
REQUEST_TIMEOUT = 30  # 请求超时时间，单位：秒

def upload_image(file_path):
    """
    上传单张图片到api_upload接口
    :param file_path: 图片文件路径
    :return: 上传成功返回图片URL，失败返回None
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误：文件 {file_path} 不存在", file=sys.stderr)
            return None

        # 检查文件是否为图片（只支持png, jpg, jpeg, gif格式，与API保持一致）
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in image_extensions:
            print(f"错误：文件 {file_path} 不是支持的图片格式（仅支持png, jpg, jpeg, gif）", file=sys.stderr)
            return None

        # 准备请求数据，使用with语句确保文件正确关闭
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {
                'Authorization': f'Bearer {API_TOKEN}'
            }

            # 发送POST请求，添加超时设置防止永久挂起
            response = requests.post(API_URL, files=files, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # 检查请求是否成功

            # 解析响应
            result = response.json()
            if result.get('success'):
                # 返回第一张图片的URL
                return result.get('result', [None])[0]
            else:
                print(f"错误：上传失败 - {result.get('error', '未知错误')}", file=sys.stderr)
                return None
    except requests.ConnectionError as e:
        print(f"错误：连接失败，请检查API服务是否运行 - {str(e)}", file=sys.stderr)
        return None
    except requests.Timeout as e:
        print(f"错误：请求超时（{REQUEST_TIMEOUT}秒）- {str(e)}", file=sys.stderr)
        return None
    except requests.HTTPError as e:
        print(f"错误：HTTP错误 {response.status_code if 'response' in locals() else '未知'} - {str(e)}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"错误：响应解析失败，请检查API返回格式 - {str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"错误：{str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)  # 打印完整错误堆栈便于调试
        return None

def main():
    """
    主函数
    - 当作为Typora自定义命令使用时，直接输出图片URL
    - 当作为普通脚本使用时，输出完整的JSON格式
    """
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法：python typora_upload.py \"demo1.jpg\" \"demo2.jpg\" ...", file=sys.stderr)
        sys.exit(1)

    # 获取图片文件路径列表
    image_paths = sys.argv[1:]

    # 上传所有图片
    uploaded_urls = []
    for path in image_paths:
        url = upload_image(path)
        if url:
            uploaded_urls.append(url)

    # Typora模式：无论上传多少张图片，都直接输出URL，每个URL占一行
    # 这是Typora自定义上传命令期望的输出格式
    for url in uploaded_urls:
        print(url)

if __name__ == "__main__":
    main()