#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AVIF图片压缩工具API服务
提供图片上传和AVIF格式转换的API接口
"""

import os
import shutil
import hashlib
import random
from flask import Flask, request, send_from_directory, jsonify, abort
from PIL import Image
import pillow_heif
from datetime import datetime, timedelta
import re

# 注册HEIF/AVIF编解码器
pillow_heif.register_heif_opener()

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['MYIMG_FOLDER'] = 'myImg'
app.config['ORIGINAL_FOLDER'] = 'myImg_original'

# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MYIMG_FOLDER'], exist_ok=True)
os.makedirs(app.config['ORIGINAL_FOLDER'], exist_ok=True)

# 安全配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # 白名单：只允许这些扩展名
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/pjpeg', 'image/x-png'}  # 白名单：只允许这些MIME类型
API_TOKEN = 'your_secure_token_here'  # API访问令牌，客户端必须提供此令牌

# 简单的速率限制实现
request_counts = {}
RATE_LIMIT = 1000  # 每分钟最大请求数
RATE_LIMIT_WINDOW = timedelta(minutes=1)

# 请求速率限制装饰器
def rate_limit(f):
    def decorated(*args, **kwargs):
        client_ip = request.remote_addr
        now = datetime.now()
        
        # 清理过期的请求记录
        if client_ip in request_counts:
            # 移除窗口外的请求
            request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] 
                                        if now - req_time < RATE_LIMIT_WINDOW]
            # 检查是否超过速率限制
            if len(request_counts[client_ip]) >= RATE_LIMIT:
                abort(429, description="Too many requests")
        else:
            request_counts[client_ip] = []
        
        # 记录当前请求
        request_counts[client_ip].append(now)
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 验证文件名安全性，防止路径遍历攻击
def sanitize_filename(filename):
    # 移除路径分隔符和特殊字符
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)
    # 确保文件名不是空的
    return filename if filename else "unnamed"


def compress_image_to_avif(input_path, output_path, quality=40, resize=None):
    """
    将图片压缩为AVIF格式
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
            
            # 调整尺寸
            if resize:
                img = img.resize(resize, Image.Resampling.LANCZOS)
            
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
        
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/api/upload', methods=['POST'])
@rate_limit  # 添加速率限制
def api_upload():
    """
    API接口：通过POST请求上传图片，返回固定格式的JSON数据
    返回格式：
    {
        "success": true,
        "result": [
            "https://example.com/myImg/20260112120837465.png?avif"
        ]
    }
    """
    try:
        # 1. 验证API令牌
        token = request.headers.get('Authorization') or request.form.get('token')
        # 如果令牌格式是Bearer token，提取token部分
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        # 调试日志
        app.logger.debug(f"Received token: {token}")
        app.logger.debug(f"Expected token: {API_TOKEN}")
        app.logger.debug(f"Token match: {token == API_TOKEN}")
        
        if token != API_TOKEN:
            return jsonify({'success': False, 'error': 'Invalid API token'}), 401
            
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # 1. 验证文件扩展名
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # 2. 验证文件MIME类型（更灵活的检查，允许常见的图片MIME类型）
        actual_mime = file.mimetype
        
        # 如果MIME类型为空，基于文件扩展名推断
        if not actual_mime:
            ext = os.path.splitext(file.filename)[1].lower()
            mime_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif'
            }
            actual_mime = mime_map.get(ext, '')
        
        mime_main_type = actual_mime.split('/')[0] if actual_mime else ''
        # 只检查主类型是否为image，不严格检查子类型
        if mime_main_type != 'image':
            return jsonify({'success': False, 'error': 'File MIME type not allowed'}), 400
        
        # 3. 生成随机md5+时间戳混合文件名，防止文件路径被爆破
        # 获取当前时间
        current_time = datetime.now()
        # 生成时间戳（格式：YYYYMMDDHHMMSSsss）
        timestamp = current_time.strftime("%Y%m%d%H%M%S%f")[:-3]
        
        # 生成随机字符串（长度为8）
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
        
        # 生成md5值（结合随机字符串和时间戳）
        md5_hash = hashlib.md5()
        md5_hash.update(f"{random_str}{timestamp}".encode('utf-8'))
        md5_value = md5_hash.hexdigest()
        
        # 结合md5和时间戳生成最终文件名前缀
        filename_prefix = f"{md5_value[:8]}{timestamp}"
        
        # 获取原始文件扩展名
        _, original_ext = os.path.splitext(file.filename)
        original_ext = original_ext.lower()
        
        # 确保扩展名是允许的
        safe_ext = original_ext if original_ext[1:] in ALLOWED_EXTENSIONS else '.png'
        
        # 4. 使用md5+时间戳作为文件名
        # 构造显示文件名：md5+时间戳 + 安全扩展名
        display_filename = f"{filename_prefix}{safe_ext}"
        
        # 压缩后的AVIF文件名：md5+时间戳 + .avif（与原文件名保持一致的前缀）
        avif_filename = f"{filename_prefix}.avif"
        
        # 5. 安全地构造文件路径
        # 确保路径在预期的文件夹内，防止路径遍历攻击
        # 使用原始扩展名保存临时文件，以便正确验证图片类型
        temp_input = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename_prefix}{safe_ext}")
        temp_input = os.path.normpath(temp_input)
        # 验证路径是否在预期的上传文件夹内
        if not temp_input.startswith(os.path.normpath(app.config['UPLOAD_FOLDER'])):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        
        original_path = os.path.join(app.config['ORIGINAL_FOLDER'], display_filename)
        original_path = os.path.normpath(original_path)
        if not original_path.startswith(os.path.normpath(app.config['ORIGINAL_FOLDER'])):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        
        avif_path = os.path.join(app.config['MYIMG_FOLDER'], avif_filename)
        avif_path = os.path.normpath(avif_path)
        if not avif_path.startswith(os.path.normpath(app.config['MYIMG_FOLDER'])):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        
        # 6. 保存上传的文件
        try:
            file.save(temp_input)
        except Exception as e:
            return jsonify({'success': False, 'error': 'Failed to save file'}), 500
        
        # 7. 验证文件内容是否为真正的图片
        try:
            with Image.open(temp_input) as img:
                # 简化验证：只检查是否能打开图片，不进行严格的完整性验证
                img.load()  # 尝试加载图片数据
        except Exception as e:
            # 删除无效文件
            if os.path.exists(temp_input):
                os.remove(temp_input)
            return jsonify({'success': False, 'error': f'Invalid image file: {str(e)}'}), 400
        
        # 8. 保存原始图片（保持原扩展名）
        shutil.copy2(temp_input, original_path)
        
        # 9. 压缩图片为AVIF格式
        result = compress_image_to_avif(temp_input, avif_path, quality=40)
        
        if not result['success']:
            # 清理文件
            for path in [temp_input, original_path, avif_path]:
                if os.path.exists(path):
                    os.remove(path)
            return jsonify({'success': False, 'error': 'Image compression failed'}), 500
        
        # 10. 清理临时文件
        if os.path.exists(temp_input):
            os.remove(temp_input)
        
        # 11. 生成完整URL
        base_url = request.host_url.rstrip('/')
        # 使用安全的文件名生成URL
        image_url = f"{base_url}/myImg/{display_filename}?avif"
        
        # 12. 返回固定格式的JSON，不泄露敏感信息
        return jsonify({
            "success": True,
            "result": [
                image_url
            ]
        })
    except Exception as e:
        # 只返回通用错误信息，不泄露具体异常细节
        app.logger.error(f"API Upload Error: {str(e)}")  # 记录详细错误到日志
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# 添加静态文件路由，用于访问myImg文件夹中的图片
@app.route('/myImg/<filename>')
@rate_limit  # 添加速率限制
def serve_myimg(filename):
    """
    提供myImg文件夹中的图片访问
    - 如果URL带有?avif参数，返回压缩后的AVIF图片
    - 如果没有参数，返回原始图片
    """
    try:
        # 1. 验证文件名安全性，防止路径遍历攻击
        safe_filename = sanitize_filename(filename)
        if safe_filename != filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        # 2. 检查是否有avif参数
        has_avif_param = 'avif' in request.args
        
        if has_avif_param:
            # 返回压缩后的AVIF图片
            # 将文件名转换为AVIF格式：去掉扩展名，添加.avif
            base_name = os.path.splitext(safe_filename)[0]
            avif_filename = f"{base_name}.avif"
            
            # 3. 安全地构造文件路径
            avif_path = os.path.join(app.config['MYIMG_FOLDER'], avif_filename)
            avif_path = os.path.normpath(avif_path)
            # 验证路径是否在预期的文件夹内
            if not avif_path.startswith(os.path.normpath(app.config['MYIMG_FOLDER'])):
                return jsonify({'success': False, 'error': 'Invalid file path'}), 400
            
            if os.path.exists(avif_path):
                return send_from_directory(app.config['MYIMG_FOLDER'], avif_filename, mimetype='image/avif')
            else:
                return jsonify({'success': False, 'error': 'Image not found'}), 404
        else:
            # 返回原始图片
            # 4. 安全地构造文件路径
            original_path = os.path.join(app.config['ORIGINAL_FOLDER'], safe_filename)
            original_path = os.path.normpath(original_path)
            # 验证路径是否在预期的文件夹内
            if not original_path.startswith(os.path.normpath(app.config['ORIGINAL_FOLDER'])):
                return jsonify({'success': False, 'error': 'Invalid file path'}), 400
            
            if os.path.exists(original_path):
                # 5. 根据文件名扩展名确定MIME类型，只允许安全的图片类型
                ext = os.path.splitext(safe_filename)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif'
                }
                # 只允许白名单中的MIME类型
                mimetype = mime_types.get(ext, None)
                if mimetype:
                    return send_from_directory(app.config['ORIGINAL_FOLDER'], safe_filename, mimetype=mimetype)
                else:
                    return jsonify({'success': False, 'error': 'Invalid image type'}), 400
            else:
                return jsonify({'success': False, 'error': 'Image not found'}), 404
    except Exception as e:
        # 只返回通用错误信息，不泄露具体异常细节
        app.logger.error(f"Serve Image Error: {str(e)}")  # 记录详细错误到日志
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # 生产环境建议使用Gunicorn或uWSGI等WSGI服务器
    # 开发环境使用Flask内置服务器
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)