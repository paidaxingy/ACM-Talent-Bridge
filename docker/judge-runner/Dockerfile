FROM python:3.11-slim

# Minimal toolchain for MVP: python3 + g++ + coreutils(timeout) + bash
# 使用国内镜像加速 apt（直接写入 sources.list，避免 slim 镜像不存在该文件的问题）
RUN set -eux; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian trixie main contrib non-free" > /etc/apt/sources.list; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian trixie-updates main contrib non-free" >> /etc/apt/sources.list; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main" >> /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        bash \
        g++ \
        coreutils \
        time \
        ca-certificates; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Create non-root user for better isolation
RUN useradd -m runner
USER runner
