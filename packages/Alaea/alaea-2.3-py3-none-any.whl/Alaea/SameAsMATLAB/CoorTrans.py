#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/11/27 16:11
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
Converting Degrees, Minutes, Seconds formatted coordinate strings to decimal.

Formula:
DEC = (DEG + (MIN * 1/60) + (SEC * 1/60 * 1/60))

Assumes S/W are negative.
"""

import re

__all__ = ['dms2degree']


def dms2degree(dms_str):
    """
    Return decimal representation of DMS

    \\>>>dms2degree(utf8(48°53'10.18"N))
    48.8866111111F

    \\>>>dms2degree(utf8(2°20'35.09"E))
    2.34330555556F

    \\>>>dms2degree(utf8(48°53'10.18"S))
    -48.8866111111F

    \\>>>dms2degree(utf8(2°20'35.09"W))
    -2.34330555556F

    """
    
    dms_str = re.sub(r'\s', '', dms_str)

    if re.search('[NSEWnsew]', dms_str) is None:
        sign = -1 if re.search('[swSW]', dms_str) else 1
    else:
        sign = 1

    numbers = [*filter(len, re.split(r'\D+', dms_str, maxsplit=4))]

    degree = numbers[0]
    minute = numbers[1] if len(numbers) >= 2 else '0'
    second = numbers[2] if len(numbers) >= 3 else '0'
    frac_seconds = numbers[3] if len(numbers) >= 4 else '0'

    second += f".{frac_seconds}"
    return sign * (int(degree) + float(minute) / 60 + float(second) / 3600)
