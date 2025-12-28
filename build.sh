#!/bin/bash
# 自动构建脚本 - 在 WSL 中运行

echo "================================"
echo "NFC 文件传输应用 - 构建脚本"
echo "================================"

# 检查是否在 WSL 环境
if ! grep -qi microsoft /proc/version; then
    echo "警告：此脚本应在 WSL 环境中运行"
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3，请先安装"
    exit 1
fi

# 检查 buildozer
if ! command -v buildozer &> /dev/null; then
    echo "未找到 buildozer，正在安装..."
    pip3 install --upgrade buildozer cython
fi

# 安装系统依赖
echo "检查系统依赖..."
sudo apt update
sudo apt install -y \
    build-essential \
    git \
    zip \
    unzip \
    openjdk-17-jdk \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev

# 清理之前的构建（可选）
read -p "是否清理之前的构建？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理构建缓存..."
    buildozer android clean
fi

# 开始构建
echo "开始构建 APK..."
buildozer android debug

# 检查构建结果
if [ -f "bin/nfcfiletransfer-1.0-debug.apk" ]; then
    echo "================================"
    echo "✅ 构建成功！"
    echo "APK 位置: bin/nfcfiletransfer-1.0-debug.apk"
    echo "================================"
    
    # 询问是否安装到手机
    read -p "是否立即安装到手机？(需要连接 USB 并启用调试) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v adb &> /dev/null; then
            echo "正在安装到手机..."
            adb install -r bin/nfcfiletransfer-1.0-debug.apk
        else
            echo "错误：未找到 adb 工具"
            echo "请手动安装：adb install bin/nfcfiletransfer-1.0-debug.apk"
        fi
    fi
else
    echo "================================"
    echo "❌ 构建失败"
    echo "请查看上方错误信息"
    echo "================================"
    exit 1
fi
