#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2025/1/9 13:36
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
 
"""
import numpy as np

_all_ = ['calc_uv2sd', 'calc_uv2wind', 'calc_uv2current']


def calc_uv2sd(u, v, opt):
    """
    计算速度的速度方向和大小
    :param u: 东向速度
    :param v: 北向速度
    :param opt: 选项 wind current ww3
    :return: spd0, dir0
    """
    
    if opt == 'wind':
        spd0, dir0 = __uv2sd_to(u, v)
    elif opt == 'current':
        spd0, dir0 = __uv2sd_from(u, v)
    elif opt == 'ww3':
        spd0, dir0 = __uv2sd_from(u, v)
    else:
        raise ValueError(f"opt must be one of 'current','wind','wave','ww3', but you set '{opt}'")
    return spd0, dir0


def __uv2sd_from(u, v):
    """
    % uv to direction(from), such as wind, wave --> 来向 0 为正北，顺时针，90为正东
    :param u: 东向速度
    :param v: 北向速度
    :return: spd0, dir0
    """
    
    spd0, dir0 = calc_uv2wind(u, v)
    return spd0, dir0


def __uv2sd_to(u, v):
    """
    % uv to direction(to), such as current, --> 与矢量方向定义相同， 0为正东，逆时针，90为正北
    :param u: 东向速度
    :param v: 北向速度
    :return: spd0, dir0
    """
    
    spd0, dir0 = calc_uv2current(u, v)
    return spd0, dir0


def calc_uv2wind(u, v):
    """
    Calculate wind speed and direction from u, v
    :param u: 东向速度
    :param v: 北向速度
    :return: spd0, dir0
    """
    
    spd0 = np.sqrt(u ** 2 + v ** 2)
    dir0 = np.mod(270 - np.rad2deg(np.arctan2(v, u)), 360)
    return spd0, dir0


def calc_uv2current(u, v):
    """
    Calculate wind speed and direction from u, v
    :param u: 东向速度
    :param v: 北向速度
    :return: spd0, dir0
    """
    
    spd0 = np.sqrt(u ** 2 + v ** 2)
    dir0 = np.mod(np.rad2deg(np.arctan2(v, u)), 360)
    return spd0, dir0