import sys
import os
import subprocess
import random
import shutil
from pathlib import Path

from template_generator import binary
from template_generator import aigc_input
from template_generator import convertor
from template_generator import license_manager
from template_generator.license_manager import require_valid_license
from template_generator.env import template_env
from template_generator import json_util as json
from template_generator.stats import report_function_stats

def getCommandResult(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=300)
        if result.returncode == 0:
            return result.stdout.decode(encoding="utf8", errors="ignore").replace("\n","").strip()
        else:
            return ""
    except subprocess.CalledProcessError as e:
        print(f"getCommandResult fail {e}")
        return ""
    
def getBinary(searchPath, useHardwareEncode=True):
    binaryPath = ""
    if sys.platform == "win32":
        binaryPath = os.path.join(binary.skymediaPath(searchPath), "TemplateProcess.exe")
    elif sys.platform == "linux":
        env_setup = template_env.EnvironmentSetup(binary.skymediaPath(searchPath))
        should_use_mesa = env_setup.should_use_mesa(useHardwareEncode, True)
        if should_use_mesa:
            binaryPath = os.path.join(binary.skymediaPath(searchPath), "TemplateProcess_osmesa")
        else:
            binaryPath = os.path.join(binary.skymediaPath(searchPath), "TemplateProcess_egl")
        if os.path.exists(binaryPath):
            cmd = subprocess.Popen(f"chmod 755 {binaryPath}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            while cmd.poll() is None:
                print(cmd.stdout.readline().rstrip().decode('utf-8'))
        
        #check env
        if not env_setup.setup_environment(useHardwareEncode):
            raise Exception("linux environment setup failed")
        #check display
        if not env_setup.setup_display():
            print("Warning: Display setup failed, attempting EGL fix...")
    elif sys.platform == "darwin":
        binaryPath = os.path.join(binary.skymediaPath(searchPath), "TemplateProcess")
        if os.path.exists(binaryPath):
            cmd = subprocess.Popen(f"chmod 755 {binaryPath}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            while cmd.poll() is None:
                print(cmd.stdout.readline().rstrip().decode('utf-8'))
            
    if os.path.exists(binaryPath):
        return os.path.dirname(binaryPath), os.path.basename(binaryPath)
    else:
        return "", ""
    
# def transcode(f):
#     try:
#         file_name = Path(f).name
#         ext = file_name[file_name.index("."):].lower()
#         if ext in [".webp"]:
#             image = Image.open(f, "r")
#             format = image.format
#             if format.lower() == "webp":
#                 newFile = f"{f}.png"
#                 image.save(newFile, "png")
#                 image.close()
#                 return True, newFile
#     except:
#         return False, f
#     return False, f
    
# def resetInput(data, tmp_file_cache):
#     newInput = []
#     for s in data["input"]:
#         needDeleteSrc, newSrc = transcode(s)
#         if needDeleteSrc:
#             tmp_file_cache.append(newSrc)
#         newInput.append(newSrc)
#     data["input"] = newInput
    
def checkTemplateIs30(tid_dir):
    finded = False
    projFile = os.path.join(tid_dir, "template.proj")
    if os.path.exists(projFile) == True:
        for root,dirs,files in os.walk(tid_dir):
            for file in files:
                name, ext = os.path.splitext(file)
                if ext == ".sky":
                    finded = True
                    break
            if root != files:
                break
    return finded

def mediaType(path):
    file_name = Path(path).name
    ext = file_name[file_name.index("."):].lower()
    if ext in [".jpg", ".png", ".jpeg", ".bmp", ".webp", ".gif"]:
        return "image"
    elif ext in [".mp4",".mov",".avi",".wmv",".mpg",".mpeg",".rm",".ram",".flv",".swf",".ts"]:
        return "video"
    elif ext in [".mp3",".aac",".wav",".wma",".cda",".flac",".m4a",".mid",".mka",".mp2",".mpa",".mpc",".ape",".ofr",".ogg",".ra",".wv",".tta",".ac3",".dts"]:
        return "music"
    else:
        return "image"
    
def resByType(inputs, type, begin_idx=0):
    for p in inputs[begin_idx:]:
        if mediaType(p) == type:
            begin_idx+=1
            return p
        begin_idx+=1

def copyInputFile(src, dst):
    file_type = mediaType(dst)
    if file_type == "image":
        image1 = Image.open(src)
        image2 = Image.open(dst)
        width1, height1 = image1.size
        width2, height2 = image2.size
        scale_ratio = min(width2/width1, height2/height1)
        new_width = int(width1 * scale_ratio)
        new_height = int(height1 * scale_ratio)
        resized_image1 = image1.resize((new_width, new_height))
        left = (new_width - width2) // 2
        top = (new_height - height2) // 2
        right = left + width2
        bottom = top + height2
        cropped_image1 = resized_image1.crop((left, top, right, bottom))
        image1.close()
        image2.close()
        cropped_image1.save(dst)
        cropped_image1.close()
    elif file_type == "video":
        return 
    elif file_type == "music":
        return 
    else:
        return 
    
def findInputList(dir, name=None):
    if name:
        input_list_path0 = os.path.join(dir, name)
        if os.path.exists(input_list_path0):
            with open(input_list_path0, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
    input_list_path = os.path.join(dir, "inputList.conf")
    if os.path.exists(input_list_path):
        with open(input_list_path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())
    input_list_path1 = os.path.join(dir, "skyinput0.conf")
    if os.path.exists(input_list_path1):
        with open(input_list_path1, 'r', encoding='utf-8') as f:
            return json.loads(f.read())
    return None

def resetTemplate(data, searchPath):
    templateNameToPath(data, searchPath)
    tpDir = data["template"]
    #fix not found template.proj
    if not os.path.exists(os.path.join(tpDir, "template.proj")):
        #查询tpDir目录下，第一个sky结尾的文件，作为template.proj的skyFile
        skyFile = "timeline.sky"
        for file in os.listdir(tpDir):
            if file.endswith(".sky"):
                skyFile = file
                break
        with open(os.path.join(tpDir, "template.proj"), "w") as f:
            json.dump({"skyFile": skyFile, "type": "Timeline"}, f)
        #fix not found output.conf
        if not os.path.exists(os.path.join(tpDir, "output.conf")):
            height = 1920
            width = 1080
            frameRate = 30.0
            videoBitRate = 5*1000*1000
            audioBitRate = 128*1000
            timeline_sky_path = os.path.join(tpDir, skyFile)
            if os.path.exists(timeline_sky_path):
                try:
                    with open(timeline_sky_path, "r", encoding="utf-8") as f:
                        timeline_data = json.load(f)
                        if "timeline" in timeline_data and "videoParams" in timeline_data["timeline"]:
                            video_params = timeline_data["timeline"]["videoParams"]
                            height = video_params.get("height", 1920)
                            width = video_params.get("width", 1080)
                            frameRate = video_params.get("frameRate", 30.0)
                            videoBitRate = video_params.get("videoBitRate", 0)
                            audioBitRate = video_params.get("audioBitRate", 0)
                            if videoBitRate > 0:
                                videoBitRate = (width * height * frameRate * 0.1)
                            with open(os.path.join(tpDir, "output.conf"), "w") as f:
                                json.dump([{"height": height, "frameRate": frameRate, "type": "Video", "width": width, "videoBitRate": int(videoBitRate), "audioBitRate": int(audioBitRate)}], f)
                except Exception as e:
                    pass
    
    if checkTemplateIs30(data["template"]) == False and len(data["input"])>0 and data.get("input_param",None):
        #create 3.0 template with 2.0 template
        new_template = convertor.template2To3(data["template"], data["input_param"], data["video_input"])
        data["template"] = new_template
        input_config = findInputList(new_template, "")
        for item in input_config:
            if item.get("need_face", False) == True or item["type"] not in ["image","music"] or item.get("need_segment_mask", False) == True:
                raise Exception("cannot process vnn input")
            real_path = item["path"]
            if real_path[0:1] == "/":
                real_path = real_path[1:]
            dst_file = os.path.join(new_template, real_path)
            src_file = resByType(data["input"], item["type"])
            if src_file:
                copyInputFile(src_file, dst_file)
        data["input"] = []

def templateNameToPath(data, searchPath):
    template_path = data["template"]
    if os.path.exists(template_path):
        return
    #template info with server
    try:
        from template_res import template as template_res_search
        server_templates = template_res_search.listTemplate(searchPath, template_path)
        if len(server_templates) > 0:
            data["template"] = server_templates[0]["path"]
            data.update(server_templates[0])
            return
    except Exception as e:
        pass
    raise Exception(f"template {template_path} not found")
    
def isAdaptiveSize(data):
    template_path = data["template"]
    templateName = os.path.basename(template_path)
    if "template" in templateName or templateName == "AIGC_1":
        return True
    return False

def isAdaptiveDuration(data):
    template_path = data["template"]
    templateName = os.path.basename(template_path)
    if "template" in templateName or templateName == "AIGC_1":
        return True
    return False

def maybeSoftWare(useHardwareEncode=True, useHardwareDecode=True):
    return template_env.maybeSoftWare(useHardwareEncode, useHardwareDecode)
    
def realCommand(cmd):
    if len(cmd) > 0 and '--license' not in cmd:
        license_key = license_manager.read_license()
        if license_key:
            new_cmd = [cmd[0], "--license", license_key] + cmd[1:]
            cmd = new_cmd
    
    if sys.platform == "linux":
        return "./" + " ".join(cmd)
    if sys.platform == "darwin":
        return "./" + " ".join(cmd)
    else:
        return cmd

def prepare_subprocess_env(binary_file=""):
    env = os.environ.copy()
    
    if sys.platform == "linux":
        if "osmesa" in binary_file.lower():
            env['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            env['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            env['LIBGL_ALWAYS_SOFTWARE'] = '1'
            env['GALLIUM_DRIVER'] = 'llvmpipe'
            env['EGL_PLATFORM'] = 'x11'
            env['MESA_GLSL_CACHE_DISABLE'] = '1'
            env['__GL_THREADED_OPTIMIZATIONS'] = '1'
            env['LIBGL_ALWAYS_INDIRECT'] = '0'

            if 'DISPLAY' not in env or not env['DISPLAY']:
                env['DISPLAY'] = ':616'
        elif "egl" in binary_file.lower():
            env['EGL_PLATFORM'] = 'device'
            env['LIBGL_ALWAYS_SOFTWARE'] = '0'
            env['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            env['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            env['MESA_GLSL_CACHE_DISABLE'] = '0'
            env['__GL_THREADED_OPTIMIZATIONS'] = '1'
            env['LIBGL_ALWAYS_INDIRECT'] = '0'

            if 'DISPLAY' in env:
                del env['DISPLAY']
        else:

            env['DISPLAY'] = ':616'
            env['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            env['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            env['LIBGL_ALWAYS_SOFTWARE'] = '1'
            env['GALLIUM_DRIVER'] = 'llvmpipe'
            env['EGL_PLATFORM'] = 'x11'
            env['MESA_GLSL_CACHE_DISABLE'] = '1'
    
    return env
    
@require_valid_license
@report_function_stats
def executeTemplate(data, searchPath="", useAdaptiveSize=False, useAdaptiveDuration=False, printLog=False, oneVideoTimeout=240, useHardwareEncode=True, useHardwareDecode=True):
    binary_dir, binary_file = getBinary(searchPath, useHardwareEncode)
    if len(binary_dir) <= 0:
        raise Exception("binary not found")

    tmp_file_cache = []
    tmp_dir_cache = []
    output_path = ""
    output_cnt = 1
    if isinstance(data, (dict)):
        output_path = data["output"]
        # resetInput(data, tmp_file_cache)
        resetTemplate(data, searchPath)
        useAdaptiveSize = useAdaptiveSize or isAdaptiveSize(data)
        useAdaptiveDuration = useAdaptiveDuration or isAdaptiveDuration(data)
        aigc_input.preProcessAIGC(data,tmp_file_cache,tmp_dir_cache)
    elif isinstance(data, (list)):
        for it in data:
            output_path = it["output"]
            # resetInput(it, tmp_file_cache)
            resetTemplate(it, searchPath)
            useAdaptiveSize = useAdaptiveSize or isAdaptiveSize(it)
            useAdaptiveDuration = useAdaptiveDuration or isAdaptiveDuration(it)
            aigc_input.preProcessAIGC(it,tmp_file_cache,tmp_dir_cache)
            output_cnt+=1

    tempDir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(tempDir) == False:
        os.makedirs(tempDir)
    inputArgs = os.path.join(tempDir, f"{random.randint(100,99999999)}.in")
    tmp_file_cache.append(inputArgs)
    if os.path.exists(inputArgs):
        os.remove(inputArgs)
    with open(inputArgs, 'w') as f:
        json.dump(data, f)

    extArgs = []
    #--adaptiveSize
    if useAdaptiveSize:
        extArgs += ["--adaptiveSize", "true"]
    #--adaptiveDuration
    if useAdaptiveDuration:
        extArgs += ["--adaptiveDuration", "true"]
    #--fontDir
    fontPath = binary.fontPath(searchPath)
    if os.path.exists(fontPath):
        extArgs += ["--fontDir", fontPath]
    #--subEffectDir
    subPath = binary.subEffectPath(searchPath)
    if os.path.exists(subPath):
        extArgs += ["--subEffectDir", subPath]
    if sys.platform == "linux":
        if maybeSoftWare(useHardwareEncode, useHardwareDecode):
            extArgs += ["--call_software_encoder"]
            extArgs += ["--call_software_decoder"]
    else:
        if useHardwareEncode == False:
            extArgs += ["--call_software_encoder"]
        if useHardwareDecode == False:
            extArgs += ["--call_software_decoder"]

    command = [binary_file, "--config", inputArgs] + extArgs
    command = realCommand(command)
    if printLog:
        print(f"=== executeTemplate => {command}")

    # 准备环境变量
    env = prepare_subprocess_env(binary_file)
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=binary_dir, timeout=oneVideoTimeout*output_cnt, env=env)
    if result.returncode == 0:
        for t in tmp_file_cache:
            os.remove(t)
        for t in tmp_dir_cache:
            shutil.rmtree(t)
        if printLog:
            print(result.stdout.decode(encoding="utf8", errors="ignore"))
        #check one output
        if os.path.exists(output_path) == False:
            print(f"output file not found")
            raise Exception("output file not found")
    else:
        err_msg = result.stdout.decode(encoding="utf8", errors="ignore")
        print(f"executeTemplate err {err_msg}")
        
        # 检查是否是硬编失败且日志中包含[Could not open video codec]
        should_retry_with_software = (
            useHardwareEncode and  # 开启了硬编
            ("[Could not open video codec]" in err_msg or "encoder.open fail" in err_msg) and  # 错误日志包含codec错误
            not any("--call_software_encoder" in arg for arg in command)  # 当前不是软编模式
        )
        
        if should_retry_with_software and sys.platform == "linux": 
            print("Hardware encoding failed with codec error, retrying with software encoding...")
            if printLog:
                print("Hardware encoding failed, retrying with software encoding...")
            
            # 清理临时文件
            for t in tmp_file_cache:
                os.remove(t)
            for t in tmp_dir_cache:
                shutil.rmtree(t)
            
            retry_command = command.copy()
            retry_command.append("--call_software_encoder")
            retry_command.append("--call_software_decoder")
            if printLog:
                print(f"=== retry with software encoding => {retry_command}")
            
            # 重新创建临时文件
            tmp_file_cache = []
            tmp_dir_cache = []
            tempDir = os.path.dirname(os.path.abspath(__file__))
            inputArgs = os.path.join(tempDir, f"{random.randint(100,99999999)}.in")
            tmp_file_cache.append(inputArgs)
            if os.path.exists(inputArgs):
                os.remove(inputArgs)
            with open(inputArgs, 'w') as f:
                json.dump(data, f)
            
            # 执行软编重试（使用OSMesa环境变量）
            retry_env = prepare_subprocess_env("TemplateProcess_osmesa")
            retry_result = subprocess.run(retry_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=binary_dir, timeout=oneVideoTimeout*output_cnt, env=retry_env)
            
            if retry_result.returncode == 0:
                for t in tmp_file_cache:
                    os.remove(t)
                for t in tmp_dir_cache:
                    shutil.rmtree(t)
                if printLog:
                    print("Software encoding retry successful!")
                    print(retry_result.stdout.decode(encoding="utf8", errors="ignore"))
                # 检查输出文件
                if os.path.exists(output_path) == False:
                    print(f"output file not found after software retry")
                    raise Exception("output file not found")
            else:
                # 软编重试也失败了
                for t in tmp_file_cache:
                    os.remove(t)
                for t in tmp_dir_cache:
                    shutil.rmtree(t)
                retry_err_msg = retry_result.stdout.decode(encoding="utf8", errors="ignore")
                print(f"executeTemplate software retry err {retry_err_msg}")
                if printLog:
                    print(f"Software encoding retry also failed: {retry_err_msg}")
                raise Exception(f"template process exception (both hardware and software failed): {retry_err_msg}")
        else:
            # 不是硬编codec错误，直接抛出异常
            for t in tmp_file_cache:
                os.remove(t)
            for t in tmp_dir_cache:
                shutil.rmtree(t)
            if printLog:
                print(err_msg)
            raise Exception(f"template process exception: {err_msg}")
    
@require_valid_license
@report_function_stats
def generateTemplate(config, output, searchPath, printLog=True, useHardwareEncode=True, useHardwareDecode=True): 
    binary_dir, binary_file = getBinary(searchPath, useHardwareEncode)
    if len(binary_dir) <= 0:
        raise Exception("binary not found")
    
    if os.path.exists(config) == False:
        raise Exception("input config not exist")

    if os.path.exists(output) == False:
        os.makedirs(output)

    command = [binary_file, "--project", config ,"-y", output]
    command = realCommand(command)
    if printLog:
        print(f"=== generateTemplate => {command}")
    
    # 准备环境变量
    env = prepare_subprocess_env(binary_file)
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=binary_dir, timeout=120, env=env)
    if result.returncode != 0:
        err_msg = result.stdout.decode(encoding="utf8", errors="ignore")
        print(f"generateTemplate err {err_msg}")
        if printLog:
            print(err_msg)
        raise Exception(f"generate template exception!")
    else:
        if printLog:
            print(result.stdout.decode(encoding="utf8", errors="ignore"))
  
@require_valid_license
def templateToVideo(path, width, height, video_bitrate, audio_bitrate, fps, timeout, snapshot=-1, printLog=False, output_file=None, useHardwareEncode=True, useHardwareDecode=True):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(current_dir, ".temp")
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        if os.path.isdir(path):
            template_dir = path
        else:
            import zipfile
            if not os.path.exists(path):
                raise Exception(f"Template file not found: {path}")
            
            extract_dir = os.path.join(temp_dir, "extracted_template")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            # 解压zip文件
            with zipfile.ZipFile(path, "r") as zipf:
                zipf.extractall(extract_dir)
            
            template_dir = extract_dir
        
        with open(os.path.join(template_dir, "output.conf"), "w") as f:
            if snapshot >= 0:
                json.dump([{
                    "pts": snapshot,
                    "type": "Image"
                }], f)
            else:
                json.dump([{
                    "height":height,
                    "frameRate":fps,
                    "type":"Video",
                    "width":width,
                    "videoBitRate":video_bitrate,
                    "audioBitRate":audio_bitrate
                }], f)
    
        if not output_file:
            if snapshot >= 0:
                output_file = os.path.join(current_dir, "output.png")
            else:
                output_file = os.path.join(current_dir, "output.mp4")
            if os.path.exists(output_file):
                os.remove(output_file)
        if os.path.exists(output_file):
            raise Exception(f"output file already exists: {output_file}")
        executeTemplate( {
            "input":[ ],
            "template":template_dir,
            "params":{},
            "output":output_file,
            }, searchPath="",
                        useAdaptiveSize=False,
                        useAdaptiveDuration=False,
                        printLog=printLog, 
                        oneVideoTimeout=timeout,
                        useHardwareEncode=useHardwareEncode, 
                        useHardwareDecode=useHardwareDecode)
        return output_file
    except Exception as e:
        raise e
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)