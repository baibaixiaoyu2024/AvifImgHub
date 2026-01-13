# AvifImgHub- 图片上传与压缩工具

公众号：泷羽Sec

作者：白小羽

微信：baibaixiaoyu2024

一个基于Flask的图片上传与压缩工具，集成Typora自定义命令上传，可将图片压缩为AVIF格式并保存。

从下图可以明显的看到图片的压缩情况，压缩后的图片文件大小为17.4KB，压缩前的文件大小为485.08KB，缩小了二十倍多！并且集成了Typora上传图片的功能，不需要高价使用腾讯云/阿里云的对象存储，节省成本

![0e2ab53d20260113121330781](http://154.64.250.117:5000/myImg/1ab3dc5b20260113044623683.png?avif)

就拿我的对象存储来讲，由于我的站longyusec.com复现过程比较多，图片也是非常的多，我每次请求访问一次网站就要消耗不少次数了，更何况一天几百人访问，下面是我买的图片压缩包，要不是年底腾讯云活动打折，不然一年的成本就要500-1000块

![image-20260113124300171](http://154.64.250.117:5000/myImg/9a2ebb0120260113044301420.png?avif)

另外还有流量包，请求次数包，等等

![image-20260113124511930](http://154.64.250.117:5000/myImg/9e71bf6720260113044512869.png?avif)

为此我想到了一个方法，我的服务器是无限流量的，空间也相对来说足够

11

那么有没有什么方法呢，我之前一直使用的是腾讯云的对象存储，还想要把它放在服务器上？并压缩？

![image-20260113122813841](http://154.64.250.117:5000/myImg/82a87ffd20260113042814383.png?avif)

然后还能告别PicGo！使用自定义服务器，还能配合粘贴，并上传到云端中

![image-20260113123705549](http://154.64.250.117:5000/myImg/450316ae20260113043706110.png?avif)

这个时候，AvifImgHub 诞生了

## 功能特性

### 1. Flask API服务

- 接收图片上传并自动压缩为AVIF格式
- 支持文件扩展名白名单验证
- 支持MIME类型检查
- 防止路径遍历攻击
- 支持Token认证
- 支持速率限制
- 使用随机md5+时间戳混合命名文件，防止文件路径被爆破，压缩前后文件名一致

### 2. Typora图片上传脚本

- 与Typora编辑器集成，支持一键上传图片，粘贴/拖动上传图片
- 支持批量上传多张图片
- 自动返回格式化的URL
- 支持Token认证

### 3. 批量上传脚本

- 支持从指定文件夹批量上传所有图片
- 支持自定义上传间隔
- 提供详细的上传进度和结果反馈

### 4. Typora命令生成工具

- 生成Typora自定义命令
- 提供GUI界面，支持一键复制命令
- 支持打包为独立可执行文件

## 目录结构

```
img_tools/
├── app.py                 # Flask API主程序
├── typora_upload.py       # Typora上传脚本
├── upload_all.py          # 批量上传脚本 / 本地迁移脚本，将一个目录中的所有图片批量压缩为avif到本地的另一个目录，适合从腾讯云/阿里云/七牛云等对象存储的内容下载到服务器，批量压缩
├── get_typora_cmd.exe     # Typora命令生成工具
├── requirements.txt       # 项目依赖
├── README.md              # 项目说明文档
├── myImg/                 # 压缩后的AVIF图片
├── myImg_original/        # 原始图片备份
└── uploads/               # 临时上传文件夹
```

## 环境要求

- Python 3.8+
- Flask
- Pillow
- requests

## 安装依赖

服务端和客户端都需要安装依赖

```bash
pip install -r requirements.txt
```

服务端

若出现如下错误

![image-20260113112157621](http://154.64.250.117:5000/myImg/7f37e48520260113044456265.png?avif)

需要在后边添加一个参数即可

```python
pip install -r requirements.txt --break-system-packages
```

![image-20260113111905365](http://154.64.250.117:5000/myImg/025bb24d20260113044453488.png?avif)

客户端

![image-20260113112251633](http://154.64.250.117:5000/myImg/a27d2b7220260113044452092.png?avif)

## 配置说明

### app.py 配置

```python
# 安全配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # 允许的文件扩展名
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/pjpeg', 'image/x-png'}  # 允许的MIME类型
API_TOKEN = 'your_secure_token_here'  # API访问令牌，需与客户端一致

# 速率限制配置
RATE_LIMIT = 100000000  # 每分钟最大请求数
RATE_LIMIT_WINDOW = timedelta(minutes=1)
```

### typora_upload.py 配置

```python
# API配置
API_URL = "http://127.0.0.1:5000/api/upload"  # API服务地址
API_TOKEN = "your_secure_token_here"  # API访问令牌需与服务端一致
REQUEST_TIMEOUT = 30  # 请求超时时间
```

## 使用方法

### 1. 启动Flask API服务

```bash
python app.py
```

服务将在 `http://127.0.0.1:5000` 启动

![image-20260113112428600](http://154.64.250.117:5000/myImg/8c02106c20260113044449224.png?avif)

支持以下API端点：

- `POST /api/upload` - 上传图片并压缩
- `GET /myImg/<filename>` - 访问压缩后的图片

### 2. Typora集成

#### 方法1：使用GUI工具生成命令

1、运行 `get_typora_cmd.exe`

![image-20260113112528961](http://154.64.250.117:5000/myImg/4d4df22d20260113044446275.png?avif)

2、点击"复制命令"

![image-20260113112622881](http://154.64.250.117:5000/myImg/5443b59820260113044444286.png?avif)

3、打开Typora偏好设置 → 图像 → 上传服务设定 → 自定义命令

![image-20260113115849803](http://154.64.250.117:5000/myImg/34e11ddb20260113035850455.png?avif)

4、粘贴命令并点击"验证图片上传选项"

![image-20260113113949786](http://154.64.250.117:5000/myImg/20260113033950.png?avif)

验证成功！

![image-20260113115739342](http://154.64.250.117:5000/myImg/28d97f2920260113035739939.png?avif)

5、尝试拖动/截图/粘贴到typora，也是成功上传到云服务器中

![image-20260113120314662](http://154.64.250.117:5000/myImg/ddf345d120260113040315492.png?avif)

#### 方法2：手动配置

在Typora设置中，将自定义命令设置为python+你这个上传脚本的路径：

```
python "d:\Desktop\img_tools\typora_upload.py"
```

### 3. 批量上传图片

```bash
python upload_all.py
```

默认配置会上传 `C:\Users\xt350\Downloads\myImg_1768198798854` 文件夹中的所有图片，可在脚本中修改 `folder_path` 变量。通常用来本地迁移，比如从腾讯云对象存储中将所有图片，放到服务器中，服务器需要将这些图片批量压缩到某一个文件中可用此脚本，文件名和原始图片名是一致的

### 4、单文件上传

准备好一个图片

![image-20260113113242645](http://154.64.250.117:5000/myImg/7e7e947c20260113044436845.png?avif)

上传一张图片

```python
python typora_upload.py .\test_image.png
```

![image-20260113113450506](http://154.64.250.117:5000/myImg/b562756220260113044433473.png?avif)

上传多张图片

```python
python typora_upload.py .\test_image.png .\test_image.png 
```

![image-20260113113627335](http://154.64.250.117:5000/myImg/2408d37e20260113044431525.png?avif)

## 安全特性

1. **文件扩展名白名单**：只允许上传指定扩展名的图片
2. **MIME类型检查**：验证文件实际类型
3. **路径遍历防护**：使用安全的文件名生成和路径验证
4. **Token认证**：防止未授权访问
5. **速率限制**：防止恶意请求
6. **安全的错误处理**：不泄露敏感信息
7. **随机文件名生成**：使用md5+时间戳混合命名，防止文件路径被爆破

## 部署建议

### 开发环境

```bash
python app.py
```

### 生产环境

建议使用Gunicorn或uWSGI等WSGI服务器部署：

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:app &
```

![image-20260113120757260](http://154.64.250.117:5000/myImg/24d9947920260113040757866.png?avif)

这样之后即使你的会话断开了，也不会导致你的服务停止

## 常见问题

### 1. 上传失败，提示"Invalid API token"

确保 `typora_upload.py` 中的 `API_TOKEN` 与 `app.py` 中的 `API_TOKEN` 一致。

![image-20260113120928389](http://154.64.250.117:5000/myImg/510ab49e20260113040928951.png?avif)

### 2. 上传失败，提示"File type not allowed"

确保上传的文件扩展名在 `ALLOWED_EXTENSIONS` 列表中。

### 3. Typora上传无响应

- 确保Flask服务正在运行
- 检查网络连接
- 检查Token配置
- 检查防火墙配置

ufw放行指定端口

```python
ufw allow 5000/tcp
```

### 4. 压缩后的图片质量不佳

可在 `app.py` 中修改 `quality` 参数调整压缩质量：

```python
result = compress_image_to_avif(temp_input, avif_path, quality=40)  # 调整quality值
```

默认是40，可以参考如下图，压缩后的图片大小为17.4KB，而压缩前是485.08KB，在图片整体观感中是看不出任何变化的！！！

![0e2ab53d20260113121330781](http://154.64.250.117:5000/myImg/1ab3dc5b20260113044623683.png?avif)

## 许可证

MIT License

