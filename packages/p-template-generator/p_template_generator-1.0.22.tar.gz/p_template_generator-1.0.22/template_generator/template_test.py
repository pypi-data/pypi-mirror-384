import sys
import os
import subprocess
import json
import shutil
import zipfile
import time
import platform
from template_generator import template
from template_generator import binary
from template_generator.env.template_env import HardwareDetector, EnvironmentSetup

def updateRes(rootDir):
    for root,dirs,files in os.walk(rootDir):
        for file in files:
            if file.find(".") <= 0:
                continue
            name = file[0:file.index(".")]
            ext = file[file.index("."):]
            if ext == ".zip.py" and os.path.exists(os.path.join(root, name)) == False:
                for dir in dirs:
                    shutil.rmtree(os.path.join(root, dir))
                with zipfile.ZipFile(os.path.join(root, file), "r") as zipf:
                    zipf.extractall(os.path.join(root, name))
                return
        if root != files:
            break

def get_device_status():
    detector = HardwareDetector()
    current_platform = platform.system().lower()
    
    if current_platform == "linux":
        # Linux使用template_env检测
        hardware_info = detector.detect_hardware_acceleration()
        display_info = detector.detect_display_server()
        
        # 检测GPU
        has_nvidia = detector.detect_nvidia_gpu()
        gpu_status = "NVIDIA GPU" if has_nvidia else "无NVIDIA GPU"
        
        # 检测显示服务器
        if display_info['x11']:
            display_status = "X11"
        elif display_info['wayland']:
            display_status = "Wayland"
        elif display_info['headless']:
            display_status = "Headless"
        else:
            display_status = "未知"
        
        # 硬件加速状态
        hw_encode = "✅" if hardware_info['nvidia_encode'] else "❌"
        hw_decode = "✅" if hardware_info['nvidia_decode'] else "❌"
        hw_render = "✅" if hardware_info['egl_support'] else "❌"
        
        return f"🖥️  Linux设备状态: {gpu_status} | 显示: {display_status} | 硬编: {hw_encode} | 硬解: {hw_decode} | 硬件渲染: {hw_render}"
        
    elif current_platform == "windows":
        # Windows固定硬编、硬解、硬件渲染
        return "🖥️  Windows设备状态: 固定配置 | 硬编: ✅ | 硬解: ✅ | 硬件渲染: ✅"
        
    elif current_platform == "darwin":
        # macOS固定软编、软解、硬件渲染
        return "🖥️  macOS设备状态: Apple Silicon | 硬编: ❌ | 硬解: ❌ | 硬件渲染: ✅"
        
    else:
        return f"🖥️  {current_platform}设备状态: 未知平台"

def test(searchPath):
    is_hardware=True
    rootDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
    updateRes(rootDir)
    while True:
        try:
            for s in ["res", "tp", "tp_20231121", "tp_2023112101"]:
                if os.path.exists(os.path.join(rootDir, s)):
                    shutil.rmtree(os.path.join(rootDir, s))
            test_template_dir = os.path.join(rootDir, "tp_2023112102")
            img_output = os.path.join(test_template_dir, "out.png")
            video_output = os.path.join(test_template_dir, "out.mp4")
            tp_dir = os.path.join(test_template_dir, "gen_template")
            tp_output = os.path.join(test_template_dir, "tp_out.mp4")
            noizz_output = os.path.join(test_template_dir, "noizz_out.mp4")
            tmp_file = []
            tmp_file.append(img_output)
            tmp_file.append(video_output)
            tmp_file.append(tp_output)
            tmp_file.append(noizz_output)
            #1024 picture
            img_start_pts = time.time()
            config = {
                "input":[
                    os.path.join(test_template_dir, "1.png"),
                    os.path.join(test_template_dir, "2.png"),
                    os.path.join(test_template_dir, "3.png"),
                    os.path.join(test_template_dir, "4.png"),
                    ],
                "template":os.path.join(test_template_dir, "gen_img"),
                "params":{},
                "output":img_output
                }
            template.executeTemplate(config, searchPath, useAdaptiveDuration=False, useAdaptiveSize=False, printLog=False, useHardwareEncode=is_hardware, useHardwareDecode=is_hardware)
            img_success = False
            if os.path.exists(img_output):
                img_success = True
            img_end_pts = time.time()
            #1024 video
            config["template"] = os.path.join(test_template_dir, "gen_video")
            config["output"] = video_output
            template.executeTemplate(config, searchPath, useAdaptiveDuration=False, useAdaptiveSize=False, printLog=False, useHardwareEncode=is_hardware, useHardwareDecode=is_hardware)
            video_end_pts = time.time()
            video_success = False
            if os.path.exists(video_output):
                video_success = True
            #txt to video
            tp_config = {
                "width": 1024,
                "height": 1024,
                "layer": [ [ ],[ ],[ ] ]
            }
            clip_duration = 3
            for i in range(1, 4):
                tp_config["layer"][0].append({
                        "res": f"hello every one, i'm template-generator with pj {i}",
                        "type": "text",
                        "startTime":clip_duration*(i-1),
                        "duration":clip_duration,
                        "positionType": "relative",
                        "positionX": 0,
                        "positionY": 0.8,
                        "params": {
                            "animation": 0,
                            "enterAnimationDuration": 0.3,
                            "exitAnimationDuration": 0.3,
                            "textColor": "#ffffffff",
                            "stroke": 1,
                            "alignment": 2,
                            "fontSize": 3
                        }
                    })
                tp_config["layer"][1].append({
                        "res":os.path.join(test_template_dir, f"{i}.png"),
                        "type":"video",
                        "startTime":clip_duration*(i-1),
                        "duration":clip_duration,
                        "positionType":"relative",
                        "positionX":0,
                        "positionY":0,
                        "params": {
                            "trimStartTime":0,
                            "width": 1024,
                            "height": 1024,
                            "animation":0
                        }
                    })
                tp_config["layer"][2].append({
                        "res":os.path.join(test_template_dir, f"{i}.mp3"),
                        "type":"audio",
                        "startTime":clip_duration*(i-1),
                        "duration":clip_duration,
                        "params": {  
                            "volume": 1
                        }
                    })    
            with open(os.path.join(test_template_dir, "param.config"), 'w') as f:
                json.dump(tp_config, f)
            template.generateTemplate(os.path.join(test_template_dir, "param.config"), tp_dir, searchPath, printLog=False, useHardwareEncode=is_hardware, useHardwareDecode=is_hardware)
            config["template"] = tp_dir
            config["output"] = tp_output
            template.executeTemplate(config, searchPath, useAdaptiveDuration=False, useAdaptiveSize=False, printLog=False, useHardwareEncode=is_hardware, useHardwareDecode=is_hardware)
            tp_end_pts = time.time()
            tp_success = False
            if os.path.exists(tp_output):
                tp_success = True
            #noizz video
            config["template"] = os.path.join(test_template_dir, "noizz_tp")
            config["output"] = noizz_output
            template.executeTemplate(config, searchPath, useAdaptiveDuration=False, useAdaptiveSize=False, printLog=False, useHardwareEncode=is_hardware, useHardwareDecode=is_hardware)
            noizz_end_pts = time.time()
            noizz_success = False
            if os.path.exists(noizz_output):
                noizz_success = True

            if video_success and img_success and tp_success and noizz_success:
                print(get_device_status())
                print("=" * 40 +" " + ("Support Hardware" if is_hardware else "SupportSoftware") + " " + "=" * 40)    
                print(f"[1024x1024                      Picture] Generate time is {round(img_end_pts-img_start_pts,2)}s")
                print(f"[1024x1024, 16.7s, 30 fps         Video] Generate time is {round(video_end_pts-img_end_pts,2)}s")
                print(f"[1024x1024, 9s             TXT to Video] Generate time is {round(tp_end_pts-video_end_pts,2)}s")
                print(f"[544 x 960, 14.93s       Template Video] Generate time is {round(noizz_end_pts-tp_end_pts,2)}s")
                if (noizz_end_pts-tp_end_pts) < 5:
                    print(f"🟢 your device is greate!")
                elif (noizz_end_pts-tp_end_pts) < 15:
                    print(f"🟡 your device is ordinary")
                else:
                    print(f"🔴 your device performance is very low")
            else:
                print(f"test fail")
            for s in tmp_file:
                os.remove(s)
            shutil.rmtree(tp_dir)
            return
        except:
            if is_hardware == False:
                return
            is_hardware = False
            pass

if __name__ == '__main__':
    test("")