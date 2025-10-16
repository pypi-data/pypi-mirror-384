#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/4/11 13:35
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
import os
import warnings
import time
from .commonCode import checkOS

__all__ = ['osprint', 'osprint2', 'cprintf']


def osprint(_str):
    """
    打印信息
    :param _str: 打印信息
    :return:
    """
    if not checkOS('WIN'):
        os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> {_str}"')
    else:
        ddt_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f'{ddt_str} ---> {_str}')


def osprint2(_status, _str):
    """
    打印信息
    :param _status: 状态
    :param _str: 打印信息
    :return:
    """
    if not checkOS('WIN'):
        os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> [{_status}] {_str}"')
    else:
        ddt_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f'{ddt_str} ---> [{_status}] {_str}')


def cprintf(_status=None, _str=None, _voice=True, _log_level='INFO'):
    """
    以颜色打印信息
    :param _status: 状态
    :param _str: 打印信息
    :param _voice: 是否语音提示
    :param _log_level: 日志级别
    :return:
    """
    warnings.simplefilter('always', DeprecationWarning)
    if not _status:
        os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> {_str}"')
    elif _status == 'SUCCESS':  # 绿色
        os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> \033[1;32m[{_status}]\033[0m\033[32m {_str}\033[0m"')
    elif _status == 'INFO':  # 蓝色
        os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> \033[1;34m[{_status}]\033[0m\033[34m {_str}\033[0m"')
    elif _status == 'WARNING':  # 橙色
        os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> \033[1;33m[{_status}]\033[0m\033[33m {_str}\033[0m"')
    elif _status == 'ERROR':  # 红色
        if _voice:
            os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> \033[1;31m[{_status}]\033[0m\033[31m {_str}\033[0m\a"')
        else:
            os.system(f'echo -e `date "+%Y-%m-%d %T"` "---> \033[1;31m[{_status}]\033[0m\033[31m {_str}\033[0m"')
