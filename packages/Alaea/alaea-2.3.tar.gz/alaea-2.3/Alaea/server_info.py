#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2022/12/2 00:10
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
import contextlib
import getpass
import os
import socket
import requests

__all__ = ['get_free_core', 'get_serve_info', 'get_server_ip_local', 'get_server_ip_public', 'get_serve_ip',
           'grep_from_top', 'grep_from_top_mpi']


def grep_from_top(_exe):  # sourcery skip: inline-immediately-returned-variable
    """
    从top命令中获取进程信息
    :param _exe: 进程名
    :return:
    """
    # ps -ef | grep top | grep -v grep | awk '{print $2}'
    script = f'ps -ef  | grep {_exe}' + ' | grep -v  grep | awk \'{print $2}\''
    pid = os.popen(script).read()
    return pid


def grep_from_top_mpi(_exe):
    """
    从top命令中获取进程信息
    :param _exe: 进程名
    :return:
    """
    # ps -ef | grep top | grep -v grep | awk '{print $2}'
    script = f'ps -ef  | grep {_exe}' + ' | grep -v  grep | awk \'{print $2}\' | wc -l'
    mpi_num = int(os.popen(script).read())
    if mpi_num != 0:
        mpi_num -= 1
    return mpi_num


def get_free_core():
    """
    获取空闲可用的cpu数
    :return: 空闲可用的cpu数
    """
    cpu_num = os.popen("echo $(grep processor /proc/cpuinfo | wc -l)").read()
    used_cpu_percent = os.popen("echo $(top -n 1 -b | grep Cpu | awk '{print $2}')").read()
    used_cpu_num = int(float(used_cpu_percent) / 100 * int(cpu_num))
    cpu_num = int(cpu_num)
    free_cpu_num = cpu_num - used_cpu_num
    return cpu_num, free_cpu_num


def get_serve_info():
    """
    获取服务器信息
    :return: 服务器信息
    """
    user = getpass.getuser()
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return user, hostname, ip


def get_server_ip_local():
    """
    获取服务器内网ip
    :return: 服务器内网ip
    """
    return socket.gethostbyname(socket.gethostname())


def get_server_ip_public():
    """
    获取服务器公网ip
    :return: 服务器公网ip
    """
    # https://ident.me
    # https://ifconfig.me/ip
    # http://icanhazip.com
    # https://checkip.amazonaws.com
    # http://jsonip.com/
    # http://ip.jsontest.com/
    # http://www.trackip.net/ip?json
    _public_ip = None
    with contextlib.suppress(Exception):
        _public_ip = requests.get('https://ident.me').text.strip()
    return _public_ip


def get_serve_ip(_area='ALL'):
    """
    获取服务器ip
    :return: 服务器ip
    """
    if _area == 'ALL':
        return {'local': get_server_ip_local(), 'public': get_server_ip_public()}
    elif _area == 'local':
        return get_server_ip_local()
    elif _area == 'public':
        return get_server_ip_public()
