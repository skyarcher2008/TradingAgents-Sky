FROM python:3.10-slim-bookworm

# 环境变量配置
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_TIMEOUT=300 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/ \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 替换为清华大学镜像源（更稳定）
# 直接创建阿里云镜像源配置
RUN echo 'deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free' > /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian/ bookworm main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian-security/ bookworm-security main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian-security/ bookworm-security main contrib non-free' >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    wkhtmltopdf \
    xvfb \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-liberation \
    pandoc \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制 requirements.txt 并安装依赖
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 验证关键模块安装
RUN python -c "import streamlit; print(f'Streamlit {streamlit.__version__} installed')"

# 创建必要目录
RUN mkdir -p /app/data /app/logs

# 复制项目文件（按重要性顺序）
COPY tradingagents/ ./tradingagents/
COPY web/ ./web/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY .env* ./

# 验证文件结构
RUN ls -la /app/ && \
    ls -la /app/web/ && \
    ls -la /app/tradingagents/

# 创建启动脚本
RUN echo '#!/bin/bash\n\
rm -f /tmp/.X99-lock\n\
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX &\n\
export DISPLAY=:99\n\
sleep 2\n\
echo "Starting application..."\n\
cd /app\n\
exec "$@"' > /usr/local/bin/start-xvfb.sh && \
    chmod +x /usr/local/bin/start-xvfb.sh

EXPOSE 8501

CMD ["/usr/local/bin/start-xvfb.sh", "python", "-m", "streamlit", "run", "web/app.py", "--server.address=0.0.0.0", "--server.port=8501"]