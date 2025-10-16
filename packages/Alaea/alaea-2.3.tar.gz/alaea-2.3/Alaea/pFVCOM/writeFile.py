#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2024/4/23 下午9:42
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
Reference: https://www.bilibili.com/read/cv6944361/
"""

import numpy as np
from netCDF4 import Dataset

_all_ = ['convert_nc22dm', 'write_2dm']


def convert_nc22dm(_fnc: str, _f2dm: str):
    with Dataset(_fnc) as f1:
        lon = f1.variables['lon'][:]
        lat = f1.variables['lat'][:]
        nv = f1.variables['nv'][:]
        dep = f1.variables['h'][:]
    write_2dm(_f2dm, lon, lat, nv, dep)


def write_2dm(_f2dm, _x, _y, _nv, _h=None):  # sourcery skip: extract-method
    if _h is None:
        _h = np.zeros(_x.shape)
    # regular transport content
    elehd = np.tile(['E3T'], (1, _nv.shape[1]))  # build 'E3T' string as head
    ndhd = np.tile(['ND'], _x.shape)  # build 'E3T' string as head
    #  E3T nvnum nv1 nv2 nv3 1
    e3t = np.vstack((elehd, np.arange(_nv.shape[1])+1, _nv, np.ones(_nv.shape[1], dtype=int)))
    #  ND ndnum lon lat depth
    nd = np.vstack((ndhd, np.arange(_x.shape[0])+1, _x, _x, _h))
    e3t = np.transpose(e3t)
    nd = np.transpose(nd)
    #create 2dm
    with open(_f2dm, 'w') as f2:
        f2.write('MESH2D\n')
        f2.write('MESHNAME "Mesh"\n')
        for i in range(e3t.shape[0]):
            f2.write(' '.join(e3t[i, :])+'\n')
        for j in range(nd.shape[0]):
            f2.write(' '.join(nd[j, :])+'\n')
        f2.write('BEGPARAMDEF'+'\n')
        f2.write('GM  "Mesh"'+'\n')
        f2.write('SI  0'+'\n')
        f2.write('DY  0'+'\n')
        f2.write('TU  ""'+'\n')
        f2.write('TD  0  0'+'\n')
        f2.write('NUME  3'+'\n')
        f2.write('BCPGC  0'+'\n')
        f2.write('BEDISP  0 0 0 0 1 0 1 0 0 0 0 1'+'\n')
        f2.write('BEFONT  0 2'+'\n')
        f2.write('BEDISP  1 0 0 0 1 0 1 0 0 0 0 1'+'\n')
        f2.write('BEFONT  1 2'+'\n')
        f2.write('BEDISP  2 0 0 0 1 0 1 0 0 0 0 1'+'\n')
        f2.write('BEFONT  2 2'+'\n')
        f2.write('ENDPARAMDEF'+'\n')
        f2.write('BEG2DMBC'+'\n')
        f2.write('MAT  1 "material 01"'+'\n')
        f2.write('END2DMBC'+'\n')
