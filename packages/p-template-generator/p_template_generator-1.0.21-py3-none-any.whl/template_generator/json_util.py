import sys

try:
    import orjson
    _USE_ORJSON = True
except ImportError:
    import json as orjson
    _USE_ORJSON = False


def loads(data, **kwargs):
    if _USE_ORJSON:
        if isinstance(data, str):
            data = data.encode('utf-8')
        return orjson.loads(data)
    else:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return orjson.loads(data, **kwargs)


def dumps(obj, **kwargs):
    if _USE_ORJSON:
        option = 0
        
        if kwargs.get('indent'):
            option |= orjson.OPT_INDENT_2
        
        if kwargs.get('sort_keys'):
            option |= orjson.OPT_SORT_KEYS
        
        result = orjson.dumps(obj, option=option)
        return result.decode('utf-8')
    else:
        if 'ensure_ascii' not in kwargs:
            kwargs['ensure_ascii'] = False
        return orjson.dumps(obj, **kwargs)


def load(fp, **kwargs):
    data = fp.read()
    return loads(data, **kwargs)


def dump(obj, fp, **kwargs):
    json_str = dumps(obj, **kwargs)
    if isinstance(json_str, str):
        fp.write(json_str)
    else:
        fp.write(json_str.decode('utf-8'))


def is_using_orjson():
    return _USE_ORJSON
