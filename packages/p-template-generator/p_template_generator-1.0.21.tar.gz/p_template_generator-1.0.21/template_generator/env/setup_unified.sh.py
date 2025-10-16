#!/bin/bash
echo "=== 统一环境设置脚本 ==="

# 获取脚本所在目录
root_dir=$(cd $(dirname $0);pwd)
echo "脚本目录: $root_dir"

# 检测NVIDIA GPU
has_nvidia=false
nvidia_version=""
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi | grep -q "NVIDIA"; then
        has_nvidia=true
        nvidia_version=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -1)
        echo "检测到NVIDIA GPU，驱动版本: $nvidia_version"
    fi
fi

# 检测显示服务器
has_display=false
if [ -n "$XDG_SESSION_TYPE" ] || [ -n "$DISPLAY" ]; then
    has_display=true
    echo "检测到显示服务器"
fi

# 检测EGL支持
has_egl=false
if [ -f "/usr/lib/x86_64-linux-gnu/libEGL.so" ] || [ -f "/usr/lib/libEGL.so" ]; then
    has_egl=true
    echo "检测到EGL支持"
fi

echo "=== 环境检测结果 ==="
echo "NVIDIA GPU: $has_nvidia"
echo "显示服务器: $has_display"
echo "EGL支持: $has_egl"

# 基础环境设置
echo "=== 设置基础环境 ==="
apt-get update
apt-get install libc++1 -y

# 安装基础OpenGL库（所有环境都需要）
echo "=== 安装基础OpenGL库 ==="
apt-get install libgles2-mesa-dev mesa-utils libgl1-mesa-dev mesa-common-dev libglu1-mesa-dev libosmesa6-dev -y
apt-get install libegl1 libegl1-mesa-dev -y
apt-get install libglvnd-dev libglvnd0 -y

# 安装编解码器
echo "=== 安装编解码器 ==="
apt-get install libx264-dev libbz2-dev -y

# 根据检测结果安装特定组件
if [ "$has_nvidia" = true ]; then

    echo "=== EGL Headless 硬渲染 ==="
    echo "检查现有EGL驱动..."
    ls -la /usr/lib/x86_64-linux-gnu/egl/
    ldconfig -p | grep EGL
    apt-get install -y libegl1-mesa libgl1-mesa-dri libgles2-mesa
    echo "EGL驱动目录..."
    mkdir -p /usr/lib/x86_64-linux-gnu/egl/
    echo "EGL驱动软链接..."
    find /usr/lib/x86_64-linux-gnu -name "libEGL*.so*" -exec ln -sf {} /usr/lib/x86_64-linux-gnu/egl/ \;
    echo "EGL平台配置..."
    mkdir -p /usr/share/glvnd/egl_vendor.d/
    cat > /usr/share/glvnd/egl_vendor.d/50_mesa.json << 'EOF'
    {
        "file_format_version" : "1.0.0",
        "ICD" : {
            "library_path" : "libEGL_mesa.so.0",
            "api_version" : "1.5"
        }
    }
    EOF
    echo "重新配置库..."
    ldconfig
    echo "设置环境变量..."
    unset LIBGL_ALWAYS_SOFTWARE
    export EGL_PLATFORM=device
    echo "export EGL_PLATFORM=device" >> /etc/environment
    
    echo "=== 设置NVIDIA EGL环境变量 ==="
    # 设置NVIDIA EGL环境变量
    echo "export __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json" >> /etc/environment
    echo "export __GL_THREADED_OPTIMIZATIONS=1" >> /etc/environment
    echo "export __GL_SYNC_TO_VBLANK=0" >> /etc/environment
    echo "export CUDA_VISIBLE_DEVICES=0" >> /etc/environment
    
    # 设置NVIDIA性能优化
    echo "export __GL_SHADER_DISK_CACHE=1" >> /etc/environment
    echo "export __GL_SHADER_DISK_CACHE_PATH=/tmp/nvidia_shader_cache" >> /etc/environment
    
    # 创建NVIDIA shader缓存目录
    mkdir -p /tmp/nvidia_shader_cache
    chmod 777 /tmp/nvidia_shader_cache
    
    # 创建NVIDIA EGL配置文件
    mkdir -p /usr/share/glvnd/egl_vendor.d/
    cat > /usr/share/glvnd/egl_vendor.d/10_nvidia.json << 'EOF'
{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "/usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.0"
    }
}
EOF
    # 创建NVIDIA OpenGL配置文件
    cat > /usr/share/glvnd/egl_vendor.d/10_nvidia_gl.json << 'EOF'
{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "/usr/lib/x86_64-linux-gnu/libGL_nvidia.so.0"
    }
}
else
    echo "=== 安装Mesa软件渲染组件 ==="
    # 安装xvfb虚拟显示器支持（软件渲染）
    echo "=== 安装xvfb虚拟显示器支持 ==="
    apt-get install xvfb x11-utils -y
    
    echo "=== 设置Mesa环境变量 ==="
    # 设置Mesa软件渲染环境变量
    echo "export MESA_GL_VERSION_OVERRIDE=3.3" >> /etc/environment
    echo "export MESA_GLSL_VERSION_OVERRIDE=330" >> /etc/environment
    echo "export LIBGL_ALWAYS_SOFTWARE=1" >> /etc/environment
    echo "export GALLIUM_DRIVER=llvmpipe" >> /etc/environment
    echo "export EGL_PLATFORM=x11" >> /etc/environment
    echo "export MESA_GLSL_CACHE_DISABLE=1" >> /etc/environment
    echo "export __GL_THREADED_OPTIMIZATIONS=1" >> /etc/environment
    echo "export LIBGL_ALWAYS_INDIRECT=0" >> /etc/environment
    echo "export MESA_GL_VERSION_OVERRIDE=3.3" >> /etc/environment
    echo "export MESA_GLSL_VERSION_OVERRIDE=330" >> /etc/environment
    
    # 创建Mesa EGL配置文件
    mkdir -p /usr/share/glvnd/egl_vendor.d/
    cat > /usr/share/glvnd/egl_vendor.d/50_mesa.json << 'EOF'
{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "libEGL_mesa.so.0"
    }
}
EOF
    
    # 创建额外的EGL配置文件
    cat > /usr/share/glvnd/egl_vendor.d/10_nvidia.json << 'EOF'
{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "/usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.0"
    }
}
EOF
    
    # 确保EGL库链接正确
    if [ -f "/usr/lib/x86_64-linux-gnu/libEGL_mesa.so.0" ]; then
        ln -sf /usr/lib/x86_64-linux-gnu/libEGL_mesa.so.0 /usr/lib/libEGL.so.1
        echo "创建EGL库链接"
    fi
    
    echo "Mesa软件渲染组件安装完成"
fi

# 通用设置
echo "=== 通用设置 ==="

# 链接libskycore.so
rm -rf /usr/lib/libskycore.so
ln -s $root_dir/../bin/skymedia/libskycore.so /usr/lib/libskycore.so

# 创建硬件加速检测脚本
cat > /usr/local/bin/check_acceleration << 'EOF'
#!/bin/bash
echo "=== 硬件加速检测 ==="

# 检查nvidia-smi
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA驱动: 已安装"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
else
    echo "NVIDIA驱动: 未安装"
fi

# 检查EGL支持
if [ -f "/usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.0" ]; then
    echo "NVIDIA EGL: 支持"
elif [ -f "/usr/lib/x86_64-linux-gnu/libEGL_mesa.so.0" ]; then
    echo "Mesa EGL: 支持"
else
    echo "EGL: 不支持"
fi

# 检查Mesa支持
if [ -f "/usr/lib/x86_64-linux-gnu/libGL.so" ]; then
    echo "Mesa GL: 支持"
else
    echo "Mesa GL: 不支持"
fi

# 检查虚拟显示器支持
if command -v Xorg &> /dev/null && [ -f "/usr/lib/x86_64-linux-gnu/xorg/modules/drivers/dummy_drv.so" ]; then
    echo "Xorg虚拟显示器: 支持（硬件渲染）"
elif command -v Xvfb &> /dev/null; then
    echo "Xvfb虚拟显示器: 支持（软件渲染）"
else
    echo "虚拟显示器: 不支持"
fi

echo "=== 检测完成 ==="
EOF

chmod +x /usr/local/bin/check_acceleration

echo "=== 验证安装 ==="
# 检查EGL库文件
if [ -f "/usr/lib/x86_64-linux-gnu/libEGL_mesa.so.0" ]; then
    echo "✓ Mesa EGL库已安装"
else
    echo "✗ Mesa EGL库未找到"
fi

if [ -f "/usr/lib/libEGL.so.1" ]; then
    echo "✓ EGL库链接已创建"
else
    echo "✗ EGL库链接未创建"
fi

if [ -f "/usr/lib/libskycore.so" ]; then
    echo "✓ libskycore.so链接已创建"
else
    echo "✗ libskycore.so链接未创建"
fi

echo "=== 统一环境设置完成 ==="
echo "可以使用 'check_acceleration' 命令检测硬件加速状态"

# 运行硬件加速检测
echo "=== 运行硬件加速检测 ==="
/usr/local/bin/check_acceleration

exit 0
