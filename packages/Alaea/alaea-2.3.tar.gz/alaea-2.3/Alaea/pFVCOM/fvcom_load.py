#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2024/12/13 20:47
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
"""

from netCDF4 import Dataset
from .. import Ttime
import numpy as np
from datetime import datetime, timedelta
from matplotlib import tri
# from easydict import EasyDict
from .. import P_para
from .fvcom_tools import calc_xcyc, check_grid_type, f_calc_nbve

_all_ = ['f_load_time', 'f_load_grid']


def f_load_time(fin, fmethod='time'):
    """
    Load FVCOM time
    :param fin: file name
    :param fmethod: 'time' or 'Times'
    return: Ttimes
    """

    ncid = Dataset(fin, 'r')

    if fmethod == 'Times' and 'Times' in ncid.variables.keys():
        Times_fvcom = ncid.variables['Times'][:]
        TIME = np.apply_along_axis(lambda row: b''.join(row).decode(), 1, Times_fvcom.data).tolist()
        Times = [datetime.fromisoformat(TIME[i]) for i in range(len(TIME))]
    else:
        Itime = ncid.variables['Itime'][:]
        Itime2 = ncid.variables['Itime2'][:]
        time = Itime + Itime2 / 1000 / 3600 / 24  # --> day
        if 'format' in ncid.variables['Itime'].ncattrs() and 'MJD' in ncid.variables['Itime'].format:
            Times = [datetime(1858, 11, 17) + timedelta(days=x) for x in time]
        else:
            return None
    Ttimes = Ttime(Times=Times)
    return Ttimes


def f_load_grid(fin,
                Coordinate='geo',
                MaxLon=180,
                Global=False,
                Nodisp=False):
    """
    Load FVCOM grid class
    :param fin: grid file
    :param Coordinate: 'geo' or 'xy'
    :param MaxLon: 180 or 360
    :param Global: True or False
    :param Nodisp: True or False
    :return: fgrid
    """
    
    # fgrid = EasyDict()
    fgrid = P_para()

    if fin.endswith('.nc'):
        ncid = Dataset(fin, 'r')
        if Coordinate == 'geo':
            fgrid.x = ncid.variables['lon'][:].data
            fgrid.y = ncid.variables['lat'][:].data
            fgrid.nv = ncid.variables['nv'][:].data
        else:
            fgrid.x = ncid.variables['x'][:].data
            fgrid.y = ncid.variables['y'][:].data
            fgrid.nv = ncid.variables['nv'][:].data
        
        fgrid.MaxLon = MaxLon
        fgrid.LON = fgrid.x
        fgrid.LAT = fgrid.y
        fgrid.nvMin0 = fgrid.nv - 1 if np.min(fgrid.nv) == 1 else fgrid.nv
        fgrid.nvMin1 = fgrid.nvMin0 + 1
        fgrid.tri = tri.Triangulation(fgrid.x, fgrid.y, fgrid.nvMin1.transpose()-1)
        
        fgrid.h = ncid.variables['h'][:] if 'h' in ncid.variables.keys() else None
        fgrid.siglay = ncid.variables['siglay'][:] if 'siglay' in ncid.variables.keys() else None
        ncid.close()
    
    elif fin.endswith('grd.dat'):  # 读取grd文件
        pass
    elif fin.endswith('.2dm'):  # 读取2dm文件
        pass
    elif fin.endswith('.msh'):  # 读取msh文件
        pass
    elif fin.endswith('.14'):  # 读取fort.14文件
        pass
    elif fin.endswith('.mesh'):  # 读取mike mesh文件
        pass
    else:
        raise ValueError('Unknown grid file format !!!')
    
    if Global:
        fgrid.type = 'Global'
    else:
        fgrid.type = check_grid_type(fgrid.x, fgrid.y)
    
    fgrid.xc, fgrid.yc = calc_xcyc(fgrid.x, fgrid.y, fgrid.nv, Global=[True if fgrid.type == 'Global' else False][0])
    fgrid.node = len(fgrid.x)
    fgrid.nele = len(fgrid.xc)
    fgrid.nbve = f_calc_nbve(fgrid)
    
    if 'siglay' in fgrid.keys():
        fgrid.kbm1 = fgrid.siglay.shape[0]
        fgrid.kb = fgrid.kbm1 + 1
    
    if not Nodisp:
        print(' ')
        print('------------------------------------------------')
        print('FVCOM grid:')
        print('   Dimension :  ')
        print(f'              node    : {fgrid.node}')
        print(f'              nele    : {fgrid.nele}')
        print(f'              nsiglay : {fgrid.kbm1}') if 'siglay' in fgrid.keys() else None
        print(f'   X / Longitude : {min(fgrid.x):.2f} ~ {max(fgrid.x):.2f}')
        print(f'   Y / Latitude  : {min(fgrid.y):.2f} ~ {max(fgrid.y):.2f}')
        print(f'   Depth         : {min(fgrid.h):.2f} ~ {max(fgrid.h):.2f}') if 'h' in fgrid.keys() else None
        print('------------------------------------------------')
        print(' ')
    
    return fgrid
    