# -*- coding: utf-8 -*-
#  日期 : 2022/11/30 11:33
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""

import contextlib
import datetime
import os
import shutil
import sys
import time
import warnings
import numpy as np

__all__ = ['convertToTime', 'new_filename', 'get_date', 'makedirs', 'rmfiles', 'rmtree', 'rmdirs',
           'movefiles', 'split_path', 'timer', 'whether_instanced', 'checkOS']


def convertToTime(strDate=None, listDate=None, _input_format=None, tzinfo=datetime.timezone.utc):
    """
    将 %Y%m%d 格式的8位字符串，转换为日期
    :param strDate: %Y%m%d 格式的8位日期字符串
    :param listDate: %Y%m%d 格式的8位日期字符串列表
    :param _input_format: 输入日期格式
    :param tzinfo: 时区
    :return: datetime 类型的日期
    """
    date = datetime.datetime.now()  # 默认取当天日期

    if strDate is not None and isinstance(strDate, str):
        with contextlib.suppress(Exception):
            if _input_format == 'WRF_output':
                date = datetime.datetime.strptime(strDate, "%Y-%m-%d_%H:%M:%S")  # 2022-11-09_01:00:00
            elif len(strDate) == 8:
                date = datetime.datetime.strptime(strDate, "%Y%m%d")
            elif len(strDate) == 10:
                date = datetime.datetime.strptime(strDate, "%Y%m%d%H")
            elif len(strDate) == 12:
                date = datetime.datetime.strptime(strDate, "%Y%m%d%H%M")
            elif len(strDate) == 14:
                date = datetime.datetime.strptime(strDate, "%Y%m%d%H%M%S")
            elif len(strDate) == 19:
                if strDate[10] == ' ':
                    date = datetime.datetime.strptime(strDate, "%Y-%m-%d %H:%M:%S")  # 2022-11-09 01:00:00
                elif strDate[10] == '_':
                    date = datetime.datetime.strptime(strDate, "%Y-%m-%d_%H:%M:%S")  # 2022-11-09_01:00:00
                elif strDate[10] == 'T':
                    date = datetime.datetime.strptime(strDate, "%Y-%m-%dT%H:%M:%S")  # 2022-11-09T01:00:00
        date = date.replace(tzinfo=tzinfo)
    elif listDate is not None and isinstance(listDate, list):
        with contextlib.suppress(Exception):
            date = [convertToTime(i, _input_format) for i in listDate]
    elif isinstance(strDate, str) is False and isinstance(listDate, list) is False:
        raise TypeError('strDate must be str or listDate must be list')
    return date


def new_filename(_pre, _lon, _lat, _date, _res):
    """
    根据前缀、经纬度、日期、分辨率生成输出文件名
    :param _pre: 输出文件前缀
    :param _lon: 经度
    :param _lat: 纬度
    :param _date: 日期
    :param _res: 分辨率
    :return: 输出文件名
    """
    if np.min(_lon) < 0:
        lon_1 = str(format(abs(np.min(_lon)), '.2f')).zfill(6) + 'W'
    else:
        lon_1 = str(format(abs(np.min(_lon)), '.2f')).zfill(6) + 'E'
    if np.max(_lon) < 0:
        lon_2 = str(format(abs(np.max(_lon)), '.2f')).zfill(6) + 'W'
    else:
        lon_2 = str(format(abs(np.max(_lon)), '.2f')).zfill(6) + 'E'
    if np.min(_lat) < 0:
        lat_1 = str(format(abs(np.min(_lat)), '.2f')).zfill(5) + 'S'
    else:
        lat_1 = str(format(abs(np.min(_lat)), '.2f')).zfill(5) + 'N'
    if np.max(_lat) < 0:
        lat_2 = str(format(abs(np.max(_lat)), '.2f')).zfill(5) + 'S'
    else:
        lat_2 = str(format(abs(np.max(_lat)), '.2f')).zfill(5) + 'N'
    filename = f'{_pre}_{lon_1}_{lon_2}_{lat_1}_{lat_2}_{str(_date)}_{str(_res)}.nc'
    del lon_1, lon_2, lat_1, lat_2
    return filename


def get_date():
    """
    获取日期
    :return:
    """
    date = ''
    if len(sys.argv) == 1:
        date = datetime.datetime.now().strftime("%Y%m%d")
    elif len(sys.argv) >= 2 and len(sys.argv[1]) == 8:
        date = sys.argv[1]
    return date


def makedirs(*path, exist_ok=False):
    """
    创建文件夹
    :param path: 文件夹路径
    :param exist_ok: 是否忽略错误
    :return:
    """
    for p in path:
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=exist_ok)


def rmfiles(*path):
    """
    删除文件
    :param path: 文件路径
    :return:
    """
    for p in path:
        try:
            if os.path.exists(p):
                os.remove(p)
        except PermissionError:
            warnings.warn(f'Maybe {p} is a directory, use rmtree() instead', SyntaxWarning)


def rmtree(*path, ignore_errors=False, onerror=None):
    """
    删除文件夹及包含的所有文件
    :param path: 文件夹路径
    :param ignore_errors: 是否忽略错误
    :param onerror: 错误处理
    :return:
    """
    for p in path:
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=ignore_errors, onerror=onerror)


def rmdirs(*path):
    """
    删除文件夹
    :param path: 文件夹路径
    :return:
    """
    for p in path:
        try:
            if os.path.exists(p):
                os.removedirs(p)
        except OSError:
            warnings.warn(f'Maybe {p} is not empty, use rmtree() instead', SyntaxWarning)


def movefiles(*src, dst, cover=True):
    """
    移动文件
    :param src: 源文件路径
    :param dst: 目标文件路径
    :param cover: 是否覆盖
    :return: 0
    """
    for s in src:
        if os.path.exists(s):
            if cover:
                rmtree(dst)
            shutil.move(s, dst)
    
    return 0


def split_path(_path, _split='/'):
    """
    如果路径名最后一位是'/'，则去掉
    :param _path: 路径名
    :param _split: 分隔符
    :return: 路径名
    """
    with contextlib.suppress(IndexError):
        if _path[-1] == _split:
            _path = _path[:-1]
    return _path


def timer(func):
    def inside(self):
        t1 = time.time()
        func(self)
        t2 = time.time()
        print('task time:{:.2f}s'.format(t2 - t1))

    return inside


def whether_instanced(_class):
    """
    判断是否被实例化
    :param _class: 类名
    """
    has_instance = False
    instanced = {}
    instances = globals().copy()

    for var_name, var_value in instances.items():
        if isinstance(var_value, _class):
            has_instance = True
            instanced[var_name] = var_value

    return has_instance, instanced


def checkOS(_os=None):
    """
    检查操作系统
    :param _os: 操作系统
    :return: 操作系统 LNX WIN MAC
    """
    if sys.platform == 'linux':
        OS = 'LNX'
    elif sys.platform == 'win32':
        OS = 'WIN'
    elif sys.platform == 'darwin':
        OS = 'MAC'
    else:
        OS = 'UNKNOW'
    
    if _os is not None:
        if _os == OS:
            return True
        else:
            return False
    else:
        return OS