#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2025/1/9 11:07
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
 
"""
import numpy as np

__all__ = ['calc_xcyc', 'check_grid_type', 'f_calc_nbve']


def calc_xcyc(lon, lat, nv, Global=False):
    """
    计算三角形的质心坐标
    :param lon: 三角形的经度 {ndarray(node, )}
    :param lat: 三角形的纬度 {ndarray(node, )}
    :param nv: 三角形的节点 {ndarray(nele, 3)}
    :param Global: 是否是全球网格
    :return: lonc, latc
    """
    if nv.shape[0] == 3:  # 如果nv第0维度是3，则转置
        nv = nv.T
    if np.min(nv) == 1:  # 如果nv从1开始，则减1
        nv = nv - 1
    if Global:
        r = 90.0 - lat[nv]
        theta = lon[nv]
        x = r * np.cos(np.deg2rad(theta))
        y = r * np.sin(np.deg2rad(theta))
        
        xc = np.mean(x, axis=1)
        yc = np.mean(y, axis=1)
        rc = np.sqrt(xc ** 2 + yc ** 2)
        thetac = np.degrees(np.arctan2(yc, xc))
        lonc = thetac
        latc = 90.0 - rc
    else:
        lonc = np.mean(lon[nv], axis=1)
        latc = np.mean(lat[nv], axis=1)

    return lonc, latc


def check_grid_type(lon, lat, eps=0.11):
    """
    检查网格类型
    :param lon: 经度
    :param lat: 纬度
    :param eps: 误差
    :return: 'Global' or 'Regional'
    """
    
    ftype = 'Regional'
    
    xlims = [np.min(lon), np.max(lon)]
    ylims = [np.min(lat), np.max(lat)]
    
    if ylims[0] >= -90 and np.abs(ylims[1] - 90) < eps and np.abs(xlims[0]) < eps and np.abs(xlims[1] - 360) < eps:
        if np.all(np.histogram(lon, bins=np.arange(0, 360, 5))[0] > 0):
            ftype = 'Global'
    elif ylims[0] >= -90 and np.abs(ylims[1] - 90) < eps and np.abs(xlims[0] + 180) < eps and np.abs(xlims[1] - 180) < eps:
        if np.all(np.histogram(lon, bins=np.arange(-180, 180, 5))[0] > 0):
            ftype = 'Global'

    return ftype


def f_calc_nbve(fgrid):
    """
    Calculate nbve (cell id around each node)
    :param fgrid: 网格数据
    :return: nbve
    """
    
    nv = fgrid.nvMin0
    node = fgrid.node
    nele = fgrid.nele
    
    # 将 nv 转换为 nv_l，类似于 MATLAB 的操作
    nv_l = np.hstack((
        nv.T.reshape(nele * 3, 1),  # 转置后拉平成一列
        np.repeat(np.arange(1, nele + 1), 3).reshape(-1, 1)  # 单元编号，每个单元重复 3 次
    ))
    # 按照 nv_l 的第一列（节点编号）排序
    nv_l = nv_l[np.argsort(nv_l[:, 0])]
    node_center = nv_l[:, 0]  # 节点编号
    cell_around = nv_l[:, 1]  # 单元编号
    # 计算每个节点的单元连接数
    counts = np.histogram(node_center, bins=np.arange(1, node + 2))[0]
    # 找到最大连接单元数
    max_ntve = np.max(counts)
    # 累积连接数
    counts_accum = np.concatenate(([0], np.cumsum(counts[:-1])))
    # 构造索引
    index = ((node_center - 1) * max_ntve - counts_accum[node_center - 1] + np.arange(1, nele * 3 + 1)).astype(int) - 1
    # 初始化 nbve，默认值是 nele + 1
    nbve = np.full((node, max_ntve), nele + 1, dtype=int)
    # 填充 nbve
    nbve.flat[index] = cell_around
    # 转置为节点优先的形式
    nbve = nbve.T
    return nbve

    