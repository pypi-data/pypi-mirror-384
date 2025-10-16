#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2024/4/23 下午9:41
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
from .writeFile import *
from .fvcom_load import *
from .fvcom_tools import *
from .fvcom_image import *
from .fvcom_class import *


def example_pFVCOM():
    """
    Example for pFVCOM
    """
    print('This is an example for pFVCOM')
    fin = '/Users/christmas/Desktop/exampleNC/SCS_avg_0001.nc'
    fgrid = f_load_grid(fin)
    Ttimes = f_load_time(fin)
    ncid = Dataset(fin, 'r')
    zeta = ncid.variables['zeta'][:].data
    u = ncid.variables['u'][:].data
    v = ncid.variables['v'][:].data
    ncid.close()
    plt.figure()
    f_2d_image(fgrid, zeta)
    f_2d_mesh(fgrid, Color='b')
    ind = range(0, fgrid.nele, 5)
    plt.quiver(fgrid.xc[ind], fgrid.yc[ind], u[0, 0, ind], v[0, 0, ind])
    ax = plt.gca()
    ax.set_aspect('equal')
    plt.xlabel('Longitude (degrees)')
    plt.ylabel('Latitude (degrees)')
    plt.title('zeta (m)')
    plt.colorbar()
    plt.show()
    print('End of example')