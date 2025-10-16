import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Tuple, Dict, Optional

class HardwareDetector:
    def __init__(self):
        self.platform = sys.platform
        self.is_linux = self.platform == "linux"
        self.is_windows = self.platform == "win32"
        self.is_macos = self.platform == "darwin"
        
    def get_command_result(self, cmd: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                shell=True, 
                timeout=timeout,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return ""
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Command failed: {cmd}, error: {e}")
            return ""
    
    def detect_nvidia_gpu(self) -> bool:
        if not self.is_linux:
            return False
            
        if self.get_command_result("which nvidia-smi"):
            result = self.get_command_result("nvidia-smi")
            return "NVIDIA" in result and "Driver Version" in result
        return False
    
    def detect_display_server(self) -> Dict[str, bool]:
        result = {
            'has_display': False,      # 有传统显示服务器（X11/Wayland）
            'egl_headless': False,     # 支持EGL headless渲染
            'needs_virtual_display': False  # 需要虚拟显示服务器
        }
        
        if not self.is_linux:
            result['has_display'] = True
            return result
            
        # 1. 检测EGL headless支持（最高优先级）
        hardware_info = self.detect_hardware_acceleration()
        if hardware_info['egl_support']:
            result['egl_headless'] = True
            return result
            
        # 2. 检测传统显示服务器
        display = self.get_command_result("echo $DISPLAY")
        if display and display.strip():
            # 测试DISPLAY是否可用
            test_cmd = f"xdpyinfo -display {display.strip()} > /dev/null 2>&1"
            test_result = subprocess.run(test_cmd, shell=True)
            if test_result.returncode == 0:
                result['has_display'] = True
                return result
        
        # 3. 检测Wayland
        session_type = self.get_command_result("echo $XDG_SESSION_TYPE")
        if session_type and 'wayland' in session_type.lower():
            result['has_display'] = True
            return result
            
        # 4. 都没有，需要虚拟显示服务器
        result['needs_virtual_display'] = True
        return result
    
    def detect_hardware_acceleration(self) -> Dict[str, bool]:
        result = {
            'nvidia_encode': False,
            'nvidia_decode': False,
            'mesa_software': False,
            'egl_support': False
        }
        
        if not self.is_linux:
            return result
            
        # 检测NVIDIA编码/解码支持
        has_nvidia = self.detect_nvidia_gpu()
        if has_nvidia:
            result['nvidia_encode'] = True
            result['nvidia_decode'] = True
        
        # 检测Mesa软件渲染
        mesa_libs = [
            "/usr/lib/x86_64-linux-gnu/libGL.so",
            "/usr/lib/x86_64-linux-gnu/libGLESv2.so"
        ]
        result['mesa_software'] = any(os.path.exists(lib) for lib in mesa_libs)
        
        # 检测EGL支持
        egl_libs = [
            "/usr/lib/x86_64-linux-gnu/libEGL.so",
            "/usr/lib/libEGL.so"
        ]
        result['egl_support'] = any(os.path.exists(lib) for lib in egl_libs)
        
        return result

class EnvironmentSetup:
    def __init__(self, search_path: str = ""):
        self.search_path = search_path
        self.detector = HardwareDetector()
        self.platform = sys.platform
        
    def get_setup_script_path(self, script_name: str) -> str:
        if self.platform == "linux":
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, script_name)
            py_script_path = script_path + ".py"
            
            if os.path.exists(py_script_path):
                self._convert_py_to_sh(py_script_path, script_path)
            
            return script_path if os.path.exists(script_path) else ""
        return ""
    
    def _convert_py_to_sh(self, py_path: str, sh_path: str) -> bool:
        try:
            with open(py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(sh_path, 'w', encoding='utf-8') as f:
                f.write(content)
            os.chmod(sh_path, 0o755)
            os.remove(py_path)#remove .sh.py
            return True
            
        except Exception:
            return False
    
    def should_use_mesa(self, use_hardware_encode: bool = True, use_hardware_decode: bool = True) -> bool:
        if not self.detector.is_linux or not use_hardware_encode:
            return not use_hardware_encode
            
        display_info = self.detector.detect_display_server()
        
        # EGL headless > 传统显示 > 虚拟显示 > Mesa软件渲染
        if display_info['egl_headless']:
            return False  # 使用EGL硬件渲染
        elif display_info['has_display']:
            return False  # 使用传统显示服务器
        elif display_info['needs_virtual_display']:
            return False  # 使用虚拟显示服务器
        else:
            return True   # 回退到Mesa软件渲染
    
    def should_use_software_encoding(self, use_hardware_encode: bool = True, use_hardware_decode: bool = True) -> bool:
        if not self.detector.is_linux:
            return not use_hardware_encode            
        if not use_hardware_encode or not use_hardware_decode:
            return True
        hardware_info = self.detector.detect_hardware_acceleration()
        if not hardware_info['nvidia_encode'] and not hardware_info['nvidia_decode']:
            return True
        return False
    
    def setup_environment(self, use_hardware_encode: bool = True) -> bool:
        if not self.detector.is_linux:
            return True
            
        libskycore_path = "/usr/lib/libskycore.so"
        if os.path.exists(libskycore_path):
            if os.path.islink(libskycore_path):
                target_path = os.readlink(libskycore_path)
                if os.path.exists(target_path):
                    return True
                else:
                    # 符号链接的目标文件不存在，删除无效链接
                    os.unlink(libskycore_path)
            else:
                return True
            
        # 使用统一的设置脚本
        setup_script = self.get_setup_script_path('setup_unified.sh')
            
        if not setup_script or not os.path.exists(setup_script):
            print(f"setup_script: {setup_script}")
            return False
            
        # 执行设置脚本
        try:
            result = subprocess.run(
                f"sh {setup_script}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                return True
            else:
                # 尝试使用sudo版本
                print(f"result: {result}")
                print("setup_script执行失败，尝试使用sudo版本")
                sudo_script = self.get_setup_script_path("sudo_setup.sh")
                if sudo_script and os.path.exists(sudo_script):
                    result = subprocess.run(
                        f"sh {sudo_script}",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    return result.returncode == 0
                        
        except Exception as ex:
            print(f"setup_script执行失败: {ex}")
            pass
            
        return False
    
    def setup_egl_headless(self) -> bool:
        if not self.detector.is_linux:
            return True
            
        hardware_info = self.detector.detect_hardware_acceleration()
        if not hardware_info['egl_support']:
            print("EGL不支持，无法设置headless环境")
            return False
            
        has_nvidia = self.detector.detect_nvidia_gpu()
        
        if has_nvidia:
            self._setup_nvidia_egl_environment()
        else:
            self._setup_mesa_egl_environment()
            
        # 设置EGL headless环境变量
        os.environ['EGL_PLATFORM'] = 'device'
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '0'  # 禁用软件渲染
        return True
    
    def setup_display(self) -> bool:
        if not self.detector.is_linux:
            return True
        
        display_info = self.detector.detect_display_server()
        
        # 按优先级选择渲染方式
        if display_info['egl_headless']:
            return self.setup_egl_headless()
        elif display_info['has_display']:
            return True
        elif display_info['needs_virtual_display']:
            return self._setup_virtual_display()
        else:
            print("✗ 无法设置显示环境")
            return False
    
    def _setup_virtual_display(self) -> bool:
        self.cleanup_display_processes()
        print("  使用Xvfb虚拟显示器（软件渲染）")
        return self._setup_xvfb_display()
    
    
    def _setup_xvfb_display(self) -> bool:
        display_num = ":616"
        
        # 检查Xvfb是否已经在运行
        result = subprocess.run(f"ps -ef | grep 'Xvfb {display_num}' | grep -v grep", shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            # 直接检查DISPLAY是否可用
            test_cmd = f"xdpyinfo -display {display_num} > /dev/null 2>&1"
            test_result = subprocess.run(test_cmd, shell=True)
            if test_result.returncode == 0:
                os.environ['DISPLAY'] = display_num
                self._setup_mesa_software_environment()
                self._ensure_system_wide_display()
                return True
            else:
                print("Xvfb is running but DISPLAY not accessible, cleaning up...")
                # 清理无效的Xvfb进程
                subprocess.run(f"pkill -f 'Xvfb {display_num}'", shell=True)
                subprocess.run("sleep 1", shell=True)
        
        # 检查Xvfb是否安装
        xvfb_check = subprocess.run("which Xvfb", shell=True, capture_output=True, text=True)
        if xvfb_check.returncode != 0:
            print("Installing Xvfb...")
            install_result = subprocess.run(
                "apt-get update && apt-get install -y xvfb x11-utils", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            if install_result.returncode != 0:
                print("Warning: Failed to install Xvfb")
                return False
        
        # 启动Xvfb
        xvfb_cmd = f"nohup Xvfb {display_num} -screen 0 1920x1080x24 -ac -nolisten tcp -dpi 96 > /dev/null 2>&1 &"
        subprocess.run(xvfb_cmd, shell=True)
        subprocess.run("sleep 3", shell=True)
        
        # 验证Xvfb启动
        result = subprocess.run(f"ps -ef | grep 'Xvfb {display_num}' | grep -v grep", shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("Xvfb started successfully")
            
            # 验证DISPLAY是否可用
            test_cmd = f"xdpyinfo -display {display_num} > /dev/null 2>&1"
            test_result = subprocess.run(test_cmd, shell=True)
            if test_result.returncode == 0:
                # 设置当前进程环境变量
                os.environ['DISPLAY'] = display_num
                self._setup_mesa_software_environment()
                
                # 设置系统级环境变量持久化
                self._ensure_system_wide_display()
                
                print("Xvfb DISPLAY setup completed successfully")
                return True
            else:
                print("Warning: Xvfb started but DISPLAY not accessible")
                return False
        else:
            print("Warning: Failed to start Xvfb process")
            return False
        
    
    def _setup_nvidia_egl_environment(self):
        # NVIDIA硬件加速环境变量
        os.environ['__EGL_VENDOR_LIBRARY_FILENAMES'] = '/usr/share/glvnd/egl_vendor.d/10_nvidia.json'
        os.environ['__GL_THREADED_OPTIMIZATIONS'] = '1'
        os.environ['__GL_SYNC_TO_VBLANK'] = '0'
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        
        # NVIDIA性能优化
        os.environ['__GL_SHADER_DISK_CACHE'] = '1'
        os.environ['__GL_SHADER_DISK_CACHE_PATH'] = '/tmp/nvidia_shader_cache'
        
        # EGL headless环境变量
        os.environ['EGL_PLATFORM'] = 'device'
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '0'
        
        # 确保NVIDIA EGL库路径正确
        nvidia_egl_paths = [
            '/usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.0',
            '/usr/lib/x86_64-linux-gnu/libEGL.so.1'
        ]
        
        for path in nvidia_egl_paths:
            if os.path.exists(path):
                os.environ['EGL_DRIVER_PATH'] = os.path.dirname(path)
                break
    
    def _setup_mesa_egl_environment(self):
        # Mesa硬件渲染环境变量
        os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
        os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '0'  # 优先使用硬件渲染
        os.environ['GALLIUM_DRIVER'] = 'auto'  # 自动选择最佳驱动
        
        # EGL headless环境变量
        os.environ['EGL_PLATFORM'] = 'device'
        os.environ['MESA_GLSL_CACHE_DISABLE'] = '0'  # 启用shader缓存
        os.environ['__GL_THREADED_OPTIMIZATIONS'] = '1'
        os.environ['LIBGL_ALWAYS_INDIRECT'] = '0'
        
        # 确保Mesa EGL库路径正确
        mesa_egl_paths = [
            '/usr/lib/x86_64-linux-gnu/libEGL_mesa.so.0',
            '/usr/lib/x86_64-linux-gnu/libEGL.so.1'
        ]
        
        for path in mesa_egl_paths:
            if os.path.exists(path):
                os.environ['EGL_DRIVER_PATH'] = os.path.dirname(path)
                break
    
    def _setup_mesa_software_environment(self):
        # Mesa软件渲染环境变量
        os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
        os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'  # 强制软件渲染
        os.environ['GALLIUM_DRIVER'] = 'llvmpipe'  # 使用软件驱动
        
        # X11环境变量
        os.environ['EGL_PLATFORM'] = 'x11'
        os.environ['MESA_GLSL_CACHE_DISABLE'] = '1'  # 禁用shader缓存
        os.environ['__GL_THREADED_OPTIMIZATIONS'] = '1'
        os.environ['LIBGL_ALWAYS_INDIRECT'] = '0'
    
    def cleanup_display_processes(self):
        display_num = ":616"
        
        # 清理Xvfb进程
        xvfb_result = subprocess.run(f"ps -ef | grep 'Xvfb {display_num}' | grep -v grep", shell=True, capture_output=True, text=True)
        if xvfb_result.returncode == 0 and xvfb_result.stdout.strip():
            print("Cleaning up existing Xvfb process...")
            subprocess.run(f"pkill -f 'Xvfb {display_num}'", shell=True)
            subprocess.run("sleep 1", shell=True)
    
    def _write_to_file_if_not_exists(self, file_path, content):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    existing_content = f.read()
                    if 'Template Generator Environment Variables' in existing_content:
                        # 已经存在，跳过
                        return
            
            # 写入文件
            with open(file_path, 'a') as f:
                f.write(content)
        except Exception as e:
            print(f"Warning: Failed to write to {file_path}: {e}")
    
    def _ensure_system_wide_display(self):
        try:
            display_value = os.environ.get('DISPLAY', ':616')
            
            # 1. 写入到/etc/environment（系统级环境变量）
            self._write_display_to_etc_environment(display_value)
            
            # 2. 写入到用户级配置文件（确保用户shell能加载）
            self._write_display_to_user_configs(display_value)
            
            # 3. 尝试在当前shell中导出环境变量
            self._export_to_current_shell(display_value)
            
            # 4. 创建包装脚本，确保环境变量传递
            self._create_wrapper_script(display_value)
        except Exception as e:
            print(f"Warning: Failed to set system-wide DISPLAY: {e}")
    
    def _write_display_to_etc_environment(self, display_value):
        try:
            env_file = '/etc/environment'
            display_line = f'DISPLAY="{display_value}"\n'
            
            # 读取现有内容
            existing_content = ""
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    existing_content = f.read()
            
            # 检查是否已存在DISPLAY设置
            if f'DISPLAY=' in existing_content:
                # 替换现有的DISPLAY设置
                lines = existing_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('DISPLAY='):
                        new_lines.append(f'DISPLAY="{display_value}"')
                    else:
                        new_lines.append(line)
                new_content = '\n'.join(new_lines)
            else:
                # 添加新的DISPLAY设置
                new_content = existing_content.rstrip() + '\n' + display_line
            
            # 写入文件
            with open(env_file, 'w') as f:
                f.write(new_content)
        except PermissionError:
            print("Warning: Cannot write to /etc/environment (need root permission)")
        except Exception as e:
            print(f"Warning: Failed to write DISPLAY to /etc/environment: {e}")
    
    def _write_display_to_user_configs(self, display_value):
        try:
            display_content = f"""
# Template Generator DISPLAY Configuration
export DISPLAY="{display_value}"
"""
            
            # 只写入最重要的用户配置文件
            user_configs = [
                os.path.expanduser('~/.bashrc'),
                os.path.expanduser('~/.profile')
            ]
            
            for config_file in user_configs:
                self._write_to_file_if_not_exists(config_file, display_content)
                
        except Exception as e:
            print(f"Warning: Failed to write DISPLAY to user configs: {e}")
    
    def _export_to_current_shell(self, display_value):
        try:
            # 尝试通过subprocess在当前shell中设置环境变量
            # 注意：这只能影响子进程，不能影响父shell
            export_cmd = f'export DISPLAY="{display_value}"'
            
            # 创建一个临时的shell脚本来设置环境变量
            temp_script = '/tmp/set_display.sh'
            with open(temp_script, 'w') as f:
                f.write(f'#!/bin/bash\n{export_cmd}\necho "DISPLAY set to: $DISPLAY"\n')
            
            os.chmod(temp_script, 0o755)
            
            result = subprocess.run(['bash', temp_script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Warning: Failed to export DISPLAY: {result.stderr}")
                
        except Exception as e:
            print(f"Warning: Failed to export to current shell: {e}")
    
    def _create_wrapper_script(self, display_value):
        try:
            wrapper_script = '/tmp/set_display_wrapper.sh'
            with open(wrapper_script, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write(f'# Template Generator DISPLAY Wrapper Script\n')
                f.write(f'export DISPLAY="{display_value}"\n')
                f.write(f'echo "DISPLAY环境变量已设置为: $DISPLAY"\n')
                f.write(f'echo "当前shell PID: $$"\n')
                f.write(f'echo "父shell PID: $PPID"\n')
                f.write(f'echo "要在此shell中永久设置DISPLAY，请执行:"\n')
                f.write(f'echo "export DISPLAY=\\"{display_value}\\""\n')
                f.write(f'echo "或者重新启动shell会话"\n')
                f.write(f'echo "验证命令: echo \\$DISPLAY"\n')
            
            os.chmod(wrapper_script, 0o755)
            result = subprocess.run(['bash', wrapper_script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"包装脚本执行失败: {result.stderr}")
                
        except Exception as e:
            print(f"Warning: Failed to create wrapper script: {e}")
    
def maybeSoftWare(useHardwareEncode=True, useHardwareDecode=True):
    setup = EnvironmentSetup()
    return setup.should_use_software_encoding(useHardwareEncode, useHardwareDecode)