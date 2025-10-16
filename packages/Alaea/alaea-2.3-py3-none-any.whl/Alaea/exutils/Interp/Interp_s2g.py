# -*- coding: utf-8 -*-

# @File    : interp_s2g.py
# @Date    : 2023-03-27
# @Author  : Dovelet
"""
程序算法：必须严格限制范围，拒绝遍历所有点！
先算水点的最近格点，再算格点的最近水点
Have done!!!
"""
import itertools
import json
import os
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import scipy.spatial as spt
from ... import Blog
from netCDF4 import Dataset

__all__ = ['s_search_g', 'save_id', 'read_id', 'get_interp', 'check_weight_exist', 'draw_value',
           'find_index', 'region_define', 'g_search_s']


logger_interps2g = Blog("interp_s2g").logger


def find_index(g_lon, g_lat, _s_lon, _s_lat):
    """
    获取经纬度索引
    :param g_lon: 一维格点经度
    :param g_lat: 一维格点纬度
    :param _s_lon: 散点经度
    :param _s_lat: 散点纬度
    :return: 纬度索引 经度索引
    """
    _s_lon = np.array(_s_lon)
    _s_lat = np.array(_s_lat)
    _latli = np.where(g_lat == _s_lat[:, None])[-1]
    _lonli = np.where(g_lon == _s_lon[:, None])[-1]

    return _latli.tolist(), _lonli.tolist()


def region_define(lonmin, lonmax, latmin, latmax, re_ra):
    """
    插值范围的确定
    :param lonmin: 经度最小值
    :param lonmax: 经度最大值
    :param latmin: 纬度最小值
    :param latmax: 纬度最大值
    :param re_ra: 分辨率的倒数
    :return: 一维的经度和一维的纬度
    """
    lat_num_grid = int(round(latmax - latmin, 2) * re_ra)
    lon_num_grid = int(round(lonmax - lonmin, 2) * re_ra)

    glon = np.linspace(lonmin, lonmax, lon_num_grid)
    glat = np.linspace(latmin, latmax, lat_num_grid)
    return glon, glat


def s_search_g(s_lon, s_lat, lonmin, lonmax, latmin, latmax, re_ra, k=8):
    """
    提取需要插值的格点索引
    :param s_lon: 散点经度
    :param s_lat: 散点纬度
    :param lonmin: 网格经度最小值
    :param lonmax: 网格经度最大值
    :param latmin: 网格纬度最小值
    :param latmax: 网格纬度最大值
    :param re_ra: 分辨率倒数
    :param k: 寻找点的个数
    :param k: 寻找点的个数
    :return:
    """
    g_lon, g_lat=region_define(lonmin, lonmax, latmin, latmax, re_ra)
    lat_number = g_lat.shape[0]
    lon_number = g_lon.shape[0]
    grid = []
    grid=deque(grid)
    for i, j in itertools.product(range(lon_number), range(lat_number)):
        x = [g_lon[i], g_lat[j]]
        grid.append(x)
    point = np.array(grid)
    fp_lon = []
    fp_lon=deque(fp_lon)
    fp_lat = []
    fp_lat=deque(fp_lat)
    Fp=[]
    Fp=deque(Fp)

    # 用于快速查找的KDTree类
    ckt = spt.cKDTree(point)  # 用C写的查找类，执行速度更快
    logger_interps2g.debug('正在判断哪些格点需要赋值')
    for i in range(s_lon.shape[0]):
        if (latmin-1/re_ra<=s_lat[i]<=latmax+1/re_ra) and (lonmin-re_ra<=s_lon[i]<=lonmax+re_ra):
            find_point = np.array([s_lon[i], s_lat[i]])
            distance, sequence = ckt.query(find_point, k)

            for item in sequence:
                if grid[item] not in Fp:
                    Fp.append(grid[item])
                    fp_lon.append(grid[item][0])
                    fp_lat.append(grid[item][1])

    logger_interps2g.debug(f'判断完毕,共有{len(Fp)}个格点需要赋值')
    ilat, ilon = find_index(g_lon, g_lat, fp_lon, fp_lat)
    # 现在已经找齐了需要插值的格点，我们现在需要知道，这些格点都由谁来赋值
    logger_interps2g.info('赋值索引查找中')
    fill_id=g_search_s(s_lon, s_lat, Fp, k=1)

    logger_interps2g.debug('赋值索引查找完毕')
    return ilat, ilon, fill_id


def g_search_s(s_lon, s_lat, Fp, k=1):
    """
    根据格点找散点
    :param s_lon:
    :param s_lat:
    :param Fp:
    :param k:
    :return:
    """
    s_grid = []
    s_grid=deque(s_grid)
    for i in range(s_lon.shape[0]):
        s_grid.append([s_lon[i], s_lat[i]])
    s_point = np.array(s_grid)
    ckt = spt.cKDTree(s_point)  # 用C写的查找类，执行速度更快
    fill_id=[]
    fill_id=deque(fill_id)
    for ip in Fp:
        find_point = np.array(ip)
        distance, sequence = ckt.query(find_point, k)

        fill_id.append(sequence)

    return fill_id


def save_id(latli, lonli, fill_id, out_path):
    """
    保存权重
    :param latli: 纬度索引
    :param lonli: 经度索引
    :param fill_id: 赋值索引
    :param out_path: 输出文件地址
    :return:
    """
    weight={'latli': list(latli), 'lonli': list(lonli), 'fill_id': list(fill_id)}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(weight, f)


def read_id(weight_json):
    """
    读取权重
    :param weight_json: 权重文件地址
    :return:
    """
    with open(weight_json, 'r', encoding='utf-8') as f:
        weight = json.load(f)

    return weight


def get_interp(lonmin, lonmax, latmin, latmax, re_ra, s_data, weight):
    """
    插值
    :param lonmin:
    :param lonmax:
    :param latmin:
    :param latmax:
    :param re_ra:
    :param s_data:
    :param weight:
    :return:
    """
    olon, olat = region_define(lonmin, lonmax, latmin, latmax, re_ra)
    lat_number = olat.shape[0]
    lon_number = olon.shape[0]
    # make new matrix
    # Eg: (24,30,40,80)
    #      24: time
    #      30: level
    #      40: lat
    #      80: lon
    size_new = list(s_data.shape)
    size_new[-1] = lat_number
    size_new.append(lon_number)
    _new = np.full(size_new, np.nan)

    latli = weight['latli']
    lonli = weight['lonli']
    fill_id = weight['fill_id']
    if np.ndim(s_data) == 1:
        _new[latli, lonli] = s_data[fill_id]
    else:
        s_data = np.reshape(s_data, (-1, s_data.shape[-1]))
        _new = np.reshape(_new, (-1, _new.shape[-2], _new.shape[-1]))

        for i in range(s_data.shape[0]):
            _new[i, latli, lonli] = s_data[i, fill_id]
        _new = np.reshape(_new, size_new)

    return _new


def check_weight_exist(weight_path):
    """
    检查权重文件是否存在
    :param weight_path:
    :return:
    """
    return bool(os.path.exists(weight_path))


def draw_value(value):
    """
    画个图康康
    :param value:
    :return:
    """
    plt.figure()
    plt.contourf(value, cmap='rainbow')
    plt.colorbar()
    # plt.savefig('test2.png')
    plt.show()


def example():
    """
    example
    """
    lonmin = 119.75
    lonmax = 119.95
    latmin = 35.55
    latmax = 35.65
    re_ra = 400
    a = Dataset('/data/Output_160/ww3_djk/20230409/ww3.20230409.nc')
    s_lon = a.variables['longitude'][:]
    s_lat = a.variables['latitude'][:]
    hs = a.variables['hs'][:, :]
    latli, lonli, fill = s_search_g(s_lon, s_lat, lonmin, lonmax, latmin, latmax, re_ra, k=4)
    save_id(latli, lonli, fill, 'weight.json')
    weight = read_id('weight.json')
    _new = get_interp(lonmin, lonmax, latmin, latmax, re_ra, hs, weight)
    draw_value(_new[0, :])


if __name__ == '__main__':
    example()
