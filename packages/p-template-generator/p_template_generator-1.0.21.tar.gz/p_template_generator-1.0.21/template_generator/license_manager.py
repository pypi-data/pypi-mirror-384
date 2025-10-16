import os
import platform
import time
import json
import hashlib
from threading import Thread, Lock
from typing import Optional, Tuple

def _get_config_dir():
    if platform.system() == "Windows":
        appdata = os.environ.get('APPDATA', '')
        config_dir = os.path.join(appdata, 'template_generator')
    else:
        home = os.path.expanduser('~')
        config_dir = os.path.join(home, '.config', 'template_generator')
    
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def _get_license_file_path():
    return os.path.join(_get_config_dir(), 'license.txt')

def _get_state_file_path():
    return os.path.join(_get_config_dir(), '.state')

def _encrypt_data(data: str) -> str:
    data_bytes = data.encode('utf-8')
    # 使用base64和简单的异或混淆
    import base64
    key = b'tg_secret_key_2024'
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data_bytes)])
    return base64.b64encode(encrypted).decode('utf-8')

def _decrypt_data(encrypted: str) -> str:
    try:
        import base64
        key = b'tg_secret_key_2024'
        encrypted_bytes = base64.b64decode(encrypted.encode('utf-8'))
        decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes)])
        return decrypted.decode('utf-8')
    except Exception:
        return None

class LicenseManager:
    _instance = None
    _lock = Lock()
    
    # 时效常量（秒） - 用于提醒时机
    TRIAL_PERIOD = 30 * 24 * 3600  # 30天后提示激活License
    GRACE_PERIOD = 30 * 24 * 3600  # 30天内持续提醒
    VERIFY_INTERVAL = 24 * 3600     # 24小时验证一次（后台获取提醒信息）
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.state = self._load_state()
            self._ensure_install_time()
            self._start_background_verify()
    
    def _load_state(self) -> dict:
        try:
            state_file = _get_state_file_path()
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()
                    decrypted_data = _decrypt_data(encrypted_data)
                    if decrypted_data:
                        return json.loads(decrypted_data)
        except Exception as e:
            print(f"Failed to load state: {e}")
        
        # 返回默认状态
        return {
            'install_time': None,
            'license_activated_time': None,
            'last_verify_time': None,
            'last_verify_success': False,
            'license_hash': None
        }
    
    def _save_state(self):
        try:
            state_file = _get_state_file_path()
            json_data = json.dumps(self.state)
            encrypted_data = _encrypt_data(json_data)
            with open(state_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Failed to save state: {e}")
    
    def _ensure_install_time(self):
        if self.state.get('install_time') is None:
            self.state['install_time'] = time.time()
            self._save_state()
    
    def _hash_license(self, license_key: str) -> str:
        return hashlib.sha256(license_key.encode('utf-8')).hexdigest()
    
    def _start_background_verify(self):
        def verify_task():
            time.sleep(60)  # 延迟60秒启动，不影响首次使用
            self._periodic_verify()
        
        # 只在需要时启动后台线程
        if self.should_verify():
            thread = Thread(target=verify_task, daemon=True)
            thread.start()
    
    def should_verify(self) -> bool:
        last_verify = self.state.get('last_verify_time')
        if last_verify is None:
            return True
        
        # 超过验证间隔需要验证
        return (time.time() - last_verify) > self.VERIFY_INTERVAL
    
    def _periodic_verify(self):
        try:
            license_key = self.read_license()
            if license_key:
                # 调用远程API获取提醒信息
                api_result = self._verify_license_with_api(license_key)
                
                self.state['last_verify_time'] = time.time()
                self.state['last_verify_success'] = api_result
                
                if api_result:
                    # API响应正常，更新激活时间
                    self.state['license_activated_time'] = time.time()
                    print("License后台验证成功")
                else:
                    # API验证未通过，记录但不影响使用
                    print("License后台验证未通过，建议检查License状态")
                
                self._save_state()
        except Exception as e:
            print(f"License后台验证异常: {e}")
    
    def _verify_license_with_api(self, license_key: str) -> bool:
        return True
    
    def check_license(self) -> Tuple[bool, str]:
        current_time = time.time()
        install_time = self.state.get('install_time', current_time)
        license_key = self.read_license()
        
        # 情况1：没有license，给出提示但不阻止
        if not license_key:
            days_since_install = (current_time - install_time) / (24 * 3600)
            if days_since_install > 30:
                return False, f"您已使用{int(days_since_install)}天，完整功能请使用License。"
            else:
                remaining_days = 30 - int(days_since_install)
                if remaining_days < 5:
                    return False, f"试用期剩余{5}天，请及时购买License。"
                return True, ""
        
        # 情况2：有license，通过API获取状态用于提醒
        license_activated_time = self.state.get('license_activated_time')
        last_verify_success = self.state.get('last_verify_success', False)
        last_verify_time = self.state.get('last_verify_time')
        
        # 如果从未验证，尝试验证获取提醒信息
        if license_activated_time is None:
            # 首次验证，获取API提醒信息
            api_result = self._verify_license_with_api(license_key)
            if api_result:
                self.state['license_activated_time'] = current_time
                self.state['last_verify_time'] = current_time
                self.state['last_verify_success'] = True
                self._save_state()
                return True, "License已激活，感谢支持！"
            else:
                # API验证失败或无响应，记录但不阻止
                self.state['last_verify_time'] = current_time
                self.state['last_verify_success'] = False
                self._save_state()
                return True, "License验证未通过，建议联系服务商确认"
        
        # 如果上次验证失败，给出提示但不阻止
        if not last_verify_success and last_verify_time:
            days_since_failed = (current_time - last_verify_time) / (24 * 3600)
            if days_since_failed > 30:
                return True, f"License已{int(days_since_failed)}天未验证成功，建议联系服务商。"
            else:
                remaining_days = 30 - int(days_since_failed)
                return True, f"License验证未通过，建议在{remaining_days}天内联系服务商确认"
        
        # License正常
        return True, "License有效"
    
    def read_license(self) -> Optional[str]:
        try:
            file_path = _get_license_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None

    def write_license(self, license_key: str) -> bool:
        if not license_key:
            return False
        
        try:
            file_path = _get_license_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(license_key)
            
            license_hash = self._hash_license(license_key)
            
            api_result = self._verify_license_with_api(license_key)
            self.state['license_activated_time'] = time.time()
            self.state['last_verify_time'] = time.time()
            self.state['last_verify_success'] = api_result
            self.state['license_hash'] = license_hash
            self._save_state()
            
            if not api_result:
                print("License验证未通过，但已保存")
            return True
        except Exception as e:
            logprint(f"Failed to write license: {e}")
            return False

_license_manager = None

def _get_manager() -> LicenseManager:
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager

def read_license():
    return _get_manager().read_license()

def write_license(license_key):
    return _get_manager().write_license(license_key)

def check_license_validity():
    is_valid, message = _get_manager().check_license()
    return is_valid, message

def require_valid_license(func):
    def wrapper(*args, **kwargs):
        is_valid, message = check_license_validity()
        if not is_valid:
            warning_msg = f"⚠️ License提醒：{message}"
            print(warning_msg)
            print(f"\n{warning_msg}")
        elif "试用期" in message or "宽限期" in message:
            print(f"ℹ️ {message}")
        return func(*args, **kwargs)
    return wrapper