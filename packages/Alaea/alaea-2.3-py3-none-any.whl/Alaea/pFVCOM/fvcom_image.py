#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2025/1/9 11:32
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
 
"""
import matplotlib.pyplot as plt
from matplotlib import tri
import numpy as np

_all_ = ['f_2d_mesh', 'f_2d_image']


def f_2d_mesh(fgrid, Global=False, Color='k'):
    """
    draw 2d mesh
    :param fgrid: FVCOM grid
    :param Global: True or False
    :param Color: color
    :return: handle
    """
    
    x = fgrid.x
    y = fgrid.y
    nv = fgrid.nvMin0
    
    if Global or fgrid.type == 'Global':
        edge_cell = np.where(np.max(x[nv], axis=1) - np.min(x[nv], axis=1) > 181)[0]
        nv = np.delete(nv, edge_cell, axis=0)
    
    tri_nv = tri.Triangulation(x, y, nv.T)
    
    # plt.figure()
    h = plt.triplot(tri_nv, 'k-', lw=0.5)
    plt.setp(h, color=Color)
    # plt.show()
    
    return h


def f_2d_image(fgrid, var):
    """
    draw 2d image
    :param fgrid: FVCOM grid
    :param var: variable
    :return: handle
    """
    
    def changem(array, new_vals, old_vals):
        """将 array 中的 old_vals 替换为 new_vals"""
        mapping = dict(zip(old_vals, new_vals))
        return np.vectorize(mapping.get, otypes=[array.dtype])(array)
    
    MaxLon = fgrid.MaxLon
    MinLon = MaxLon - 360.
    MidLon = MaxLon - 180.
    
    x = fgrid.x
    y = fgrid.y
    nv = fgrid.nvMin0
    node = fgrid.node
    nele = fgrid.nele
    
    if var.size == node:
        pass
    else:
        if var.size == var.shape[0]:
            var = var[:, 0]
        elif var.size == var.shape[1]:
            var = var[0]

    if var.size == node:
        pass
    elif var.size == nele:
        raise UserWarning('Not implemented yet !!!')
    else:
        raise ValueError('Wrong size of variable !!!')
    
    if fgrid.type == 'Global':
        # 1. 找到 y == 90 的节点 (北极点)
        Pole_node = np.where(y == 90.)[0]
        # 2. 计算三角形单元的最大和最小经度
        max_cell_x = np.max(x[nv], axis=1)
        min_cell_x = np.min(x[nv], axis=1)
        # 3. 找到满足条件的边界单元
        edge_cell = (max_cell_x > MidLon) & (min_cell_x < MidLon) & ((max_cell_x - min_cell_x) > 180.)
        # 4. 提取边界单元和边界节点
        edge_nv = nv[edge_cell]
        edge_node = np.setdiff1d(np.unique(edge_nv), Pole_node)
        # 5. 处理边界节点的经度
        edge_x = x[edge_node]
        k1 = np.where(edge_x < MidLon)[0]
        k2 = np.where(edge_x > MidLon)[0]
        edge_x[k1] += 360.0
        edge_x[k2] -= 360.0
        # 6. 处理边界节点的纬度
        edge_y = y[edge_node]
        # 7. 修改边界单元中的节点索引
        edge_nv_right = changem(edge_nv, k1 + node, edge_node[k1])
        edge_nv_left = changem(edge_nv, k2 + node, edge_node[k2])
        # 8. 扩展节点和单元信息
        x = np.concatenate((x, edge_x))
        y = np.concatenate((y, edge_y))
        nv = np.vstack((nv[~edge_cell], edge_nv_right, edge_nv_left))
        var = np.concatenate((var, var[edge_node]))
    else:
        pass
    tri_nv = tri.Triangulation(x, y, nv.T)
    
    # plt.interactive(False)
    # plt.figure()
    h = plt.tripcolor(tri_nv, var)
    # plt.colorbar()
    # plt.show()
    
    return h

