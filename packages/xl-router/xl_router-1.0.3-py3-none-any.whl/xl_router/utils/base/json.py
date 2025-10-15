import re
from typing import Callable


def lowcase(text: str) -> str:
    """驼峰转下划线
    lowcase('sayHello')
    """
    ls = list(set(re.findall('[a-z][A-Z]', text)))
    ll = [x[0] + '_' + chr(ord(x[1]) + 32) for x in ls]
    for x, y in zip(ls, ll):
        text = text.replace(x, y)
    return text

def camel(text: str) -> str:
    """下划线转驼峰"""
    if isinstance(text, str):
        if '_' in text:
            first, *others = text.split('_')
            return ''.join([first.lower(), *map(str.title, others)])
        else:
            return text
    else:
        return text

def to_lowcase(data: dict):
    """将字典键转化为小写"""
    return {lowcase(k): data.get(k) for k in data}

def to_camel(data: dict):
    """"将字典键转化为驼峰"""
    return {camel(k): data.get(k) for k in data}

def iter_list(data: list, func: Callable):
    """深层遍历字典数组，将键进行转化"""
    rt_list = []
    for item in data:
        if isinstance(item, dict):
            rt_list.append(iter_dict(item, func))
        elif isinstance(item, list):
            rt_list.append(iter_list(item, func))
        else:
            rt_list.append(item)
    return rt_list

def iter_dict(data: dict, func: Callable) -> dict:
    """深层遍历字典，将键进行转化"""
    rt_dict = {}
    for k, v in data.items():
        if isinstance(v, dict):
            rt_dict[func(k)] = iter_dict(v, func)
        elif isinstance(v, list):
            rt_dict[func(k)] = iter_list(v, func)
        else:
            rt_dict[func(k)] = v
    return rt_dict

def iter_lowcase(data: dict) -> dict:
    """深层遍历字典，将键转化为小写"""
    return iter_dict(data, lowcase)

def iter_camel(data: dict) -> dict:
    """深层遍历字典，将键转化为驼峰"""
    return iter_dict(data, camel)