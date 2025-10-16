#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/3/25 11:23
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
import contextlib
import fractions
import re
import unicodedata  # 处理ASCii码的包
import numpy as np
from .commonCode import split_path
from .cprintfs import osprint

__all__ = ['read_conf']


# 从file中读取配置信息
def read_conf(_config_file, ele=None):
    conf = {}
    key_same_num = 1
    with open(_config_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 去除空格和注释
            line = line.strip()
            if line.startswith('#') or line.startswith('!') or line.startswith('//') or line.startswith(';'):
                continue
            if line == '':
                continue

            key, value = line.split('=', maxsplit=1)
            key = key.strip()
            value = value.strip()
            value = value.split('#')[0].strip().strip("'").strip('"')
            value = split_path(value)
            [key, value] = char_fill_dic(key, value)
            if value == '':
                value = None
            # 如果conf中已经存在key，则跳过
            if key in conf:
                conf[f'{key}_{key_same_num}'] = value
                key_same_num += 1
            else:
                key_same_num = 1
                conf[key] = value
    try:
        if ele is not None:
            conf = conf[ele]
    except KeyError:
        osprint(f'"{ele} is not in the config file"')
    return conf


def char_fill_dic(key, _str):  # sourcery skip: low-code-quality
    # 不区分大小写比较
    if _str.lower() == '.true.':
        _str = True
    elif _str.lower() == '.false.':
        _str = False
    elif _str.startswith('['):
        _str_1 = _str.split(',')
        _str = _str[1:-1].split(',')
        _str = [x for x in _str if x.strip()]
        try:
            for i in range(len(_str)):
                if is_number(_str[i]):
                    _str[i] = float(_str[i])
                else:
                    tmp_1 = _str[i].strip().split(':')
                    if '/' in tmp_1[0]:  # 否则会出现 误判
                        try:
                            tmp_1 = [float(fractions.Fraction(x)) for x in tmp_1]  # '1/2' -> 0.5
                        except ValueError:  # (1/24) -> 0.041666666666666664
                            tmp_1 = [float(eval(x)) for x in tmp_1]
                    _str[i] = np.arange(float(tmp_1[0]), float(tmp_1[2]) + float(tmp_1[1]), float(tmp_1[1])).tolist()  # [1:1,120]
            _str = flatten_list(_str, [])
        except ValueError:
            try:
                if isinstance(_str[0], str):  # type(_str[0]) == str:
                    _str = [_str[i].replace('[', '').replace(']', '').split() for i in range(len(_str))]
                    with contextlib.suppress(ValueError):
                        _str = [float(x) for _str in _str for x in _str]  # ['1', '2', '3'] -> [1, 2, 3]
                    with contextlib.suppress(TypeError):
                        _str = [x.strip("'").strip('"') for _str in _str for x in _str]  # [["'hs'"], ["'t02'"]] -> ['hs', 't02']
            except IndexError:
                for i in range(len(_str)):
                    _str[i] = _str[i].strip().strip("'").strip('"')
        except IndexError:  # [1,120]
            _str = _str[0].strip().strip("'").strip('"')
            tmp_1 = _str.split(':')
            _str = np.arange(float(tmp_1[0]), float(tmp_1[1])+1).tolist()  # [1:1,120]
    elif _str.startswith('{'):
        # "{'KK' :'sds', 'YY' : 'asd'}" ->  {'KK' :'sds', 'YY' : 'asd'}
        _str = _str[1:-1].split(',')
        _str = {i.split(':')[0].strip().strip("'").strip('"'): i.split(':')[1].strip().strip("'").strip('"') for i in _str}
    elif _str.startswith("'") or _str.startswith('"'):
        _str = _str.strip().strip("'").strip('"')
    elif is_number(_str):
        _str = float(_str)
    else:
        with contextlib.suppress(IndexError):
            if bool(re.match(r'^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$', _str.strip()[0])):
                with contextlib.suppress(ValueError):
                    _str = [float(i) for i in _str.split()]
    key = 'None' if key == '' else key
    return key, _str


def is_number(s):
    with contextlib.suppress(ValueError):
        float(s)
        return True
    with contextlib.suppress(TypeError, ValueError):
        unicodedata.numeric(s)  # 把一个表示数字的字符串转换为浮点数返回的函数
        return True
    return False


def flatten_list(_lst, flattened_lst):
    # sourcery skip: default-mutable-arg
    for item in _lst:
        if isinstance(item, list):
            flatten_list(item, flattened_lst)
        else:
            flattened_lst.append(item)
    return flattened_lst
