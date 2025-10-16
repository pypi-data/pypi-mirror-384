import requests, json, time, threading, os, shutil, tempfile, random, glob, traceback
from functools import wraps
from typing import Any, Dict, List, Optional
from template_generator.utils import deviceInfo

class StatsReporter:
    def __init__(self):
        self.primary_domain = "api.dalipen.com"
        self.backup_domain = "aigc.zjtemplate.com"
        self.endpoint = "aigc/task/templateGeneratorStatus"
        self.timeout = 3
        self.max_sample_size = 5
        
        if os.name == 'nt':
            self._stats_dir = os.path.join(os.environ.get('TEMP', ''), 'template_generator_stats')
        else:
            self._stats_dir = os.path.join(tempfile.gettempdir(), 'template_generator_stats')
        os.makedirs(self._stats_dir, exist_ok=True)
    
    def _write_to_file(self, data: Dict[str, Any]):
        try:
            file_index = random.randint(0, 100)
            filename = f"stats_{file_index:02d}.jsonl"
            stats_file = os.path.join(self._stats_dir, filename)
            with open(stats_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
                f.flush()
        except Exception as e:
            pass
    
    def _read_all_files(self):
        try:
            pattern = os.path.join(self._stats_dir, "stats_*.jsonl")
            files = glob.glob(pattern)
            
            all_events = []
            for file_path in files:
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in lines:
                                try:
                                    event = json.loads(line.strip())
                                    all_events.append(event)
                                except Exception as e:
                                    continue
                except Exception as e:
                    continue
            
            return all_events
        except Exception as e:
            return []
    
    def _clear_all_files(self):
        try:
            shutil.rmtree(self._stats_dir)
            os.makedirs(self._stats_dir, exist_ok=True)
        except Exception as e:
            pass
    
    def _aggregate_events(self, events: List[Dict[str, Any]]):
        try:
            function_stats = {}
            
            for event in events:
                function_name = event.get('function_name', 'unknown')
                
                if function_name not in function_stats:
                    function_stats[function_name] = {
                        'count': 0,
                        'success_count': 0,
                        'error_count': 0,
                        'samples': []
                    }
                
                stats = function_stats[function_name]
                stats['count'] += 1
                
                if event.get('success', True):
                    stats['success_count'] += 1
                else:
                    stats['error_count'] += 1
                
                if len(stats['samples']) < self.max_sample_size:
                    sample = {
                        'timestamp': event.get('timestamp'),
                        'args': event.get('args', []),
                        'kwargs': event.get('kwargs', {}),
                        'success': event.get('success', True),
                        'error_message': event.get('error_message')
                    }
                    stats['samples'].append(sample)
                elif random.random() < self.max_sample_size / stats['count']:
                    sample = {
                        'timestamp': event.get('timestamp'),
                        'args': event.get('args', []),
                        'kwargs': event.get('kwargs', {}),
                        'success': event.get('success', True),
                        'error_message': event.get('error_message')
                    }
                    stats['samples'][random.randint(0, self.max_sample_size - 1)] = sample
            
            return function_stats
        except Exception as e:
            return {}
    
    def _send_report(self, function_stats: Dict[str, Any]):
        try:
            for domain in [self.primary_domain, self.backup_domain]:
                try:
                    requests.adapters.DEFAULT_RETRIES = 2
                    s = requests.session()
                    s.keep_alive = False
                    s.headers.update({'Connection':'close'})
                    res = s.post(f"https://{domain}/{self.endpoint}",
                                 data={
                                    "device_info": json.dumps(deviceInfo()),
                                    "function_stats": json.dumps(function_stats)
                                }, 
                                 verify=False,
                                 timeout=3)
                    if res.status_code == 200:
                        return
                except Exception as e:
                    continue
        except Exception as e:
            pass
    
    def report_function_call(self, function_name: str, args: tuple, kwargs: dict, result: Any = None, error: Exception = None):
        try:
            report_data = {
                "function_name": function_name,
                "timestamp": int(time.time() * 1000),
                "args": self._serialize_args(args),
                "kwargs": self._serialize_kwargs(kwargs),
                "success": error is None,
                "error_message": str(error)[:500] if error else None
            }
            self._write_to_file(report_data)
            
            if random.random() < 0.05:
                events = self._read_all_files()
                if events:
                    function_stats = self._aggregate_events(events)
                    if function_stats:
                        self._send_report(function_stats)
                        self._clear_all_files()
        except Exception as e:
            pass
    
    def _serialize_args(self, args: tuple) -> List[Any]:
        serialized = []
        for arg in args:
            try:
                if isinstance(arg, (str, int, float, bool, type(None))):
                    serialized.append(arg)
                elif isinstance(arg, (list, dict)):
                    serialized.append(str(arg)[:500])
                else:
                    serialized.append(str(type(arg).__name__))
            except Exception as e:
                serialized.append("unserializable")
        return serialized
    
    def _serialize_kwargs(self, kwargs: dict) -> Dict[str, Any]:
        serialized = {}
        for key, value in kwargs.items():
            try:
                if isinstance(value, (str, int, float, bool, type(None))):
                    serialized[key] = value
                elif isinstance(value, (list, dict)):
                    serialized[key] = str(value)[:500]
                else:
                    serialized[key] = str(type(value).__name__)
            except Exception as e:
                serialized[key] = "unserializable"
        return serialized

_stats_reporter = StatsReporter()

def report_function_stats(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        error = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error = e
            raise
        finally:
            try:
                _stats_reporter.report_function_call(
                    func.__name__,
                    args,
                    kwargs,
                    result,
                    error
                )
            except Exception as e:
                pass
    
    return wrapper
