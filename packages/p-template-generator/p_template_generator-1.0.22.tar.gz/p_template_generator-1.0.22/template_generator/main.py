import os
import sys
import argparse
from pathlib import Path
from PIL import Image
import shutil
import urllib3
import datetime
import platform
import time

from pkg_resources import parse_version
from template_generator import template
from template_generator import template_test
from template_generator import ffmpeg
from template_generator import json_util as json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from license_manager import read_license, write_license
from template_generator.stats import report_function_stats

@report_function_stats
def testTemplate():
    searchPath = findSearchPath(3)
    template_test.test(searchPath)

@report_function_stats
def gen():
    file = sys.argv[1]

    width = 0
    height = 0
    video_bitrate = 5*1000*1000
    audio_bitrate = 128*1000
    fps = 30
    timeout = 240
    openlog = False
    output = None
    idx = 2
    snapshot = -1
    hardware = False
    while idx < len(sys.argv):
        if sys.argv[idx] == "-size":
            size = sys.argv[idx+1].split("x")
            width = int(size[0])
            height = int(size[1])
        if sys.argv[idx] == "-bitrate":
            video_bitrate = int(sys.argv[idx+1])
        if sys.argv[idx] == "-video_bitrate":
            video_bitrate = int(sys.argv[idx+1])
        if sys.argv[idx] == "-audio_bitrate":
            audio_bitrate = int(sys.argv[idx+1])
        if sys.argv[idx] == "-fps":
            fps = float(sys.argv[idx+1])
        if sys.argv[idx] == "-timeout":
            timeout = int(sys.argv[idx+1])
        if sys.argv[idx] == "-output":
            output = sys.argv[idx+1]
        if sys.argv[idx] == "-log":
            openlog = (int(sys.argv[idx+1]) == 1)
        if sys.argv[idx] == "-snapshot":
            snapshot = float(sys.argv[idx+1])
        if sys.argv[idx] == "-hardware":
            hardware = (int(sys.argv[idx+1]) == 1)
        idx+=1
    return template.templateToVideo(file,
                                    width, 
                                    height, 
                                    video_bitrate, 
                                    audio_bitrate, 
                                    fps, 
                                    timeout,
                                    snapshot,
                                    printLog=openlog, 
                                    output_file=output,
                                    useHardwareEncode=hardware, 
                                    useHardwareDecode=hardware)

def checkJsonParam(data):
    if "input" not in data or "template" not in data or "params" not in data or "output" not in data:
        raise Exception("json key missing")
    inputFiles = data["input"]
    template_path = data["template"]
    output_path = data["output"]
    params = data["params"]
    if len(template_path) <= 0 or len(output_path) <= 0:
        raise Exception("template | output_path is empty")
    for it in inputFiles:
        if os.path.exists(it) == False:
            raise Exception(f"file {it} not found!")
    
@report_function_stats
def txt2proj():
    txt = sys.argv[2]
    output = sys.argv[3]

    try:
        searchPath = ""
        if len(sys.argv) > 5 and sys.argv[4] == "-i":
            searchPath = sys.argv[5]

        template.generateTemplate(txt, output, searchPath)
    except Exception as e:
        raise e
    
def findSearchPath(begin):
    idx = begin
    while idx < len(sys.argv):
        if sys.argv[idx] == "-i":
            return sys.argv[idx+1]
        idx+=1
    return ""
    
@report_function_stats
def configTemplate():
    input = sys.argv[2]

    try:
        if os.path.isfile(input):
            with open(input, 'r') as f:
                data = json.load(f)
        elif os.path.isdir(input):
            data = {
                "input":[],
                "template":input,
                "params":{},
                "output": os.path.join(input, "out.mp4")
            }
        if isinstance(data, (dict)):
            checkJsonParam(data)
        elif isinstance(data, (list)):
            for it in data:
                checkJsonParam(it)
        else:
            raise Exception("input file is not [] or {} or template dir")
            
        searchPath = ""
        froceAdaptiveSize = False
        froceAdaptiveDuration = False
        idx = 3
        while idx < len(sys.argv):
            if sys.argv[idx] == "-i":
                searchPath = sys.argv[idx+1]
            if sys.argv[idx] == "-adaptiveSize":
                froceAdaptiveSize = True
            if sys.argv[idx] == "-adaptiveDuration":
                froceAdaptiveDuration = True
            idx+=1
        template.executeTemplate(data, searchPath, froceAdaptiveSize, froceAdaptiveDuration)
    except Exception as e:
        raise e
    
@report_function_stats
def transcoding():
    file = sys.argv[2]
    if os.path.exists(file) == False:
        raise Exception("transcoding file not exist")
    
    searchPath = findSearchPath(3)

    w,h,bitrate,fps,duration = ffmpeg.videoInfo(file, "")
    if w <= 0 or h <= 0 or bitrate <= 0 or fps <= 0:
        raise Exception("file is not video")

    niceBitrate = min(bitrate, (w * h) * (fps / 30.0) / (540.0 * 960.0 / 4000))

    tmpPath = f"{file}.mp4"
    args_moov = ["-movflags", "faststart"]
    args_h264 = ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    args_bitrate = ["-b:v", f"{niceBitrate}k", "-bufsize", f"{niceBitrate}k"]
    command = ["-i", file] + args_moov + args_h264 + args_bitrate + ["-y", tmpPath]
    if ffmpeg.process(command, searchPath):
        os.remove(file)
        os.rename(tmpPath, file)

@report_function_stats
def getcover():
    path = sys.argv[2]
    outpath = path.replace(".mp4", ".mp4.jpg")
    if len(sys.argv) > 3:
        outpath = sys.argv[3]
    searchPath = findSearchPath(3)
    ffmpeg.process(["-i", path, "-ss", "00:00:00.02", "-frames:v", "1", "-y", outpath], searchPath)
    if os.path.exists(outpath):
        print(outpath)
        exit(0)
    exit(-1)

@report_function_stats
def size():
    path = sys.argv[2]
    file_name = Path(path).name
    ext = file_name[file_name.index("."):].lower()
    width = 0
    height = 0
    if ext in [".jpg", ".png", ".jpeg", ".bmp"]:
        img = Image.open(path)
        imgSize = img.size
        width = img.width
        height = img.height
    else:
        searchPath = findSearchPath(3)
        width,height,bitrate,fps = ffmpeg.videoInfo(path,searchPath)
    print(f"{int(width)}, {int(height)}")
    exit(0)
 
@report_function_stats   
def doFfmpeg():
    cmd = sys.argv[2]
    if len(cmd) <= 0:
        raise Exception("please set command")
    
    searchPath = findSearchPath(3)

    if ffmpeg.process(cmd.split(" "), searchPath):
        print("=== success")
    else:
        print("=== fail")

@report_function_stats
def licenseCommand():
    if len(sys.argv) == 2:
        license_key = read_license()
        if license_key:
            print(license_key)
        else:
            print("no license")
    elif len(sys.argv) == 3:
        new_license = sys.argv[2]
        if write_license(new_license):
            print(f"✅ already set license: {new_license}")
        else:
            print("❌ set license failed")

def log():
    logFilePath = f"{os.path.dirname(os.path.abspath(__file__))}/log.log"
    if os.path.exists(logFilePath):
        with open(logFilePath, "r") as f:
            all_lines = f.readlines()
            if len(all_lines) > 300:
                print("⚠️ last 300 lines of log, more log in file")
                print(logFilePath)
            lines = all_lines[-300:]
            for line in lines:
                print(line.strip())
    else:
        print("empty")
    
module_func = {
    "-test": testTemplate,
    "-txt2proj": txt2proj,
    "-input": configTemplate,
    "-transcoding": transcoding,
    "-ffmpeg": doFfmpeg,
    "-size": size,
    "-cover": getcover,
    "-gen": gen,
    "-license": licenseCommand,
    "-log": log
}

# def _funnyLogo():
#     print('''
#                           ==++=+
#                         +--::::--+
#                         :-::--::--=
#                         =::-**-::-+
#                          +***=++-+
#                         =:*#=*+++
#                     *#....=***+ =
#                  -...@... ..-. :.%:
#                 :....=+.. .   .-.% ..-
#                ...   .#...:... . #...  -
#              ::..... .*  .. ... -*. . .  -
#            -  . ... .==.....  . *..  . ..  -
#          -  .. . .. .* .....  . *   : ..  ......  .-
#        :.... .       *  .... . +        -. .:=**+-*==
#      -....     .. ..-# .. ..  -            =***#**=+*
#     ....        ..  #..    ..-            =+++**++++*
#    :          ...:..: .   :.:-            -=+-+=+++++
#   :..          --::-::-:::-:--:           +=--===-=-=
#  +*            --=------------:            =----=--=
#  **#*          :---:::-=--=--=-               ===
#  =#*           =+===-=-----=====
#                +=++===::::-=====-
#                +=+++==- :-:----===
#                ++++++==   ::-=--==-
#                 =++++==    :---=====
#                 =++++==      :---====
#                 =++++==       :---===
#                 -====--        ::---=-
#                 ===---         ------=
#                 ===---         :-----
#                 ==----         ---:--
#                  =---         =-----
#                  ----         ----:-
#                  ---:         ----:
#                  -=--         ==-:
#                  ...         ..--
#                  ...        .:...:
#                 -:::        ....:::
#                 .:::         ....:...
# ''')

def main():
    if len(sys.argv) < 2:
        #输出版本号
        print("Template Generator 1.0.22")
        print(" ")
        print("Supported commands:")
        print("  -test: test environment")
        print("  [zip/dir] : generate video from template zip file or template dir")
        print("  -license: license show/set")
        print(" ")
        print("custome generate video:")
        print("  -txt2proj: generate template cofnig from layer config")
        print("  -input: generate video from template config")
        print("  -transcoding: transcoding video")
        print("  -ffmpeg: execute ffmpeg")
        print("  -size: get video size")
        print("  -cover: get video cover")
        print("  -gen: generate video")
        return
    
    urllib3.disable_warnings()
    logFilePath = f"{os.path.dirname(os.path.abspath(__file__))}/log.log"
    if os.path.exists(logFilePath) and os.stat(logFilePath).st_size > (1024 * 1024 * 5):  # 5m bak file
        d = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        bakFile = logFilePath.replace(".log", f"_{d}.log")
        shutil.copyfile(logFilePath, bakFile)
        os.remove(logFilePath)

    try:
        cnt = len(sys.argv)
        full_command = "template "
        for i in range(cnt):
            full_command += f" {sys.argv[i]}"

        module = sys.argv[1]
        if module in module_func:
            module_func[module]()
            sys.exit(0)
        elif os.path.isdir(module) and (os.path.exists(os.path.join(module, "timeline.sky")) or 
                                      os.path.exists(os.path.join(module, "timeline0.sky"))):
            print(gen())
            sys.exit(0)
        elif os.path.exists(module) and ".zip" in module:
            print(gen())
            sys.exit(0)
        else:
            print("Unknown command:", module)
            sys.exit(-1)
    except Exception as e:
        print(f"uncatch Exception:{e}")
        print(e)
        sys.exit(-1)
        
if __name__ == '__main__':
    main()