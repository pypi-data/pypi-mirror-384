import uuid
import platform
import subprocess
import os
import sys
import psutil
from datetime import datetime, timedelta
import http
import json
from pathlib import Path
import socket

def get_mac_from_nettools():
    try:
        cmd = "ifconfig"
        output = subprocess.check_output(cmd, shell=True)
        output_str = output.decode(encoding='UTF-8')
        mac = output_str[output_str.index('ether') + 6:output_str.index('ether') + 23].replace(':', '')
        return True, mac
    except Exception as e:
        return False, None
    
def get_mac_from_system():
    try:
        root_path = '/sys/class/net/'
        dbtype_list = os.listdir(root_path)
        for dbtype in dbtype_list:
            if os.path.isfile(os.path.join(root_path, dbtype)):
                dbtype_list.remove(dbtype)

        if len(dbtype_list) == 0:
            return False, None
        mac = ''
        for dbtype in dbtype_list:
          cmd = f"cat {root_path}{dbtype}/address"
          output = subprocess.check_output(cmd, shell=True)
          mac += output.decode(encoding='UTF-8')
        return True, mac
    except Exception as e:
        return False, None

mac_value = ""
def get_mac_address():
    global mac_value
    if mac_value and len(mac_value) > 0:
        return mac_value
    
    if platform.system() == 'Windows':
        cmd = "ipconfig /all"
        output = subprocess.check_output(cmd, shell=True)
        output_str = output.decode('gbk')
        pos = output_str.find('Physical Address')
        if pos == -1:
            pos = output_str.find('物理地址')
        mac_value = (output_str[pos:pos+100].split(':')[1]).strip().replace('-', '')
    elif platform.system() == 'Linux' or platform.system() == 'Darwin':
        ok, mac_value = get_mac_from_nettools()
        if ok:
            return mac_value
        ok, mac_value = get_mac_from_system()
        if ok:
            return mac_value
        return None
    else:
        mac_value = None
    return mac_value

cpu_serial = ""
def get_cpu_serial():
    global cpu_serial
    if cpu_serial and len(cpu_serial) > 0:
        return cpu_serial
    
    if platform.system() == 'Windows':
        cmd = "wmic cpu get ProcessorId"
        output = subprocess.check_output(cmd, shell=True)
        output_str = output.decode('gbk')
        pos = output_str.index("\n")
        cpu_serial = output_str[pos:].strip()
    elif platform.system() == 'Linux':
        with open('/proc/cpuinfo') as f:
            
            for line in f:
                if line[0:6] == 'Serial':
                    return "1"
                if line.strip().startswith('serial'):
                    cpu_serial = line.split(":")[1].strip()
                    break
        if not cpu_serial:
            cpu_serial = None
    elif platform.system() == 'Darwin':
        cmd = "/usr/sbin/system_profiler SPHardwareDataType"
        output = subprocess.check_output(cmd, shell=True)
        output_str = output.decode(encoding='UTF-8')
        cpu_serial = output_str[output_str.index('Hardware UUID:') + 14:output_str.index('Hardware UUID:') + 51].replace('-', '')
    else:
        cpu_serial = None
    return cpu_serial

def get_hostname():
    return socket.gethostname()

def generate_unique_id():
    mac = get_mac_address()
    cpu_serial = get_cpu_serial()
    hostname = get_hostname()
    if mac and cpu_serial:
        unique_id = uuid.uuid5(uuid.NAMESPACE_DNS, mac + cpu_serial + hostname)
        return str(unique_id).replace('-', '')
    if mac :
        unique_id = uuid.uuid5(uuid.NAMESPACE_DNS, mac + hostname)
        return str(unique_id).replace('-', '')

def deviceInfo():
    mac = get_mac_address()
    mac = "" if mac == None else mac
    cpu_serial = get_cpu_serial()
    cpu_serial = "" if cpu_serial == None else cpu_serial
    hostname = get_hostname()
    G=1024*1024*1024
    cpu_freq = "None"
    try:
        cpu_freq = psutil.cpu_freq().max / 1000
    except:
        pass
    
    virtual_mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    data = {
        "cpu": {
            "count" : psutil.cpu_count(logical=False),
            "max_freq" : f"{cpu_freq} GHz",
        },
        "disk": {
            "total": f"{(disk.total / G):.1f} G",
        },
        "memory": {
            "total": f"{(virtual_mem.total / G):.1f} G",
        },
        "device_id": generate_unique_id(),
        "host_name": hostname
    }
    return data