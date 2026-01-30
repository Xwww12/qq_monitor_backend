# 使用轻量级 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
# 注意：确保你本地执行了 pip freeze > requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# 暴露 FastAPI 默认端口
EXPOSE 9000

# 启动命令
# 使用 uvicorn 运行，注意 main 是你的文件名，app 是 FastAPI 实例名
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]