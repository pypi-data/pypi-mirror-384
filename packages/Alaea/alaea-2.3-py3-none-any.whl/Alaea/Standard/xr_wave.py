#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2025/10/16 14:13
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
 
"""
import xarray as xr
from datetime import datetime
from .. import Ttime
import numpy as np
from .xr_attrs import add_lon_attrs, add_lat_attrs, add_time_attrs, add_TIME_attrs, fixed_encoding, add_wave_attrs


def xr_wave_dateset(_lon: np.ndarray,
                    _lat: np.ndarray,
                    _time: list,
                    **kwargs):
    """
    _swh = _viss['swh']     # swh: 有效波高 (m) significant wave height
    _mwd = _viss['mwd']     # mwd: 平均波向 (deg) mean wave direction
    _mwp = _viss['mwp']     # mwp: 平均波周期 (s) mean wave period
    _mwl = _viss['mwl']     # mwl: 平均波长 (m) mean wave length
    _pp1d = _viss['pp1d']   # pp1d: 谱峰周期 (s) peak period
    _shww = _viss['shww']   # shww: 风浪有效波高 (m) significant wave height of wind
    _shts = _viss['shts']   # shts: 涌浪有效波高 (m) significant wave height of total
    _mdww = _viss['mdww']   # mdww: 风浪波向 (deg) mean wave direction of wind wave
    _mdts = _viss['mdts']   # mdts: 涌浪波向 (deg) mean wave direction of total swe
    _mpww = _viss['mpww']   # mpww: 风浪平均周期 (s) mean wave period of wind waves
    _mpts = _viss['mpts']   # mpts: 涌浪平均周期 (s) mean wave period of total swell
    _hmax = _viss['hmax']   # hmax: 最大波高 (m) maximum wave height
    生成波浪数据的xarray.Dataset
    :param _lon: 经度
    :param _lat: 纬度
    :param _time: 时间
    :param kwargs: swh, mwd, mwp, mwl, pp1d, shww, shts, mdww, mdts, mpww, mpts, hmax,
                    engine, dtype, complevel, zlib, shuffle, fletcher32, contiguous,
                    product_name, source, start
        swh: significant height of combined wind waves and swell(m) 有效波高
        mwd: mean wave direction (deg) 平均波向
        mwp: mean wave period (s) 平均波周期
        mwl: mean wave length (m) 平均波长
        pp1d: peak period (s) 谱峰周期
        shww: significant height of wind waves (m) 风浪有效波高
        shts: significant height of total swell (m) 涌浪有效波高
        mdww: mean direction of wind waves (deg) 风浪波向
        mdts: mean direction of total swell (deg) 涌浪波向
        mpww: mean period of wind waves (s) 风浪平均周期
        mpts: mean period of total swell (s) 涌浪平均周期
        hmax: expected maximum wave height (linear, 1st order) (m) 最大波高
        engine: h5netcdf(default), netcdf4, scipy
        dtype: float32(default), float64
        complevel: 4(default) 0-9
        zlib: True(default)
        shuffle: True(default)
        fletcher32: True(default)
        contiguous: True(default)
        product_name: None(default) 产品名称
        source: Alaea(default) 数据来源
        start: None(default) 数据起始时间
    :return: xarray.Dataset
    """
    program_version = 'V1.0'
    history = 'Created by Python' + ' at ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if _time[0].__class__ == str:
        Ttimes = Ttime(TIME=_time)
    elif _time[0].__class__ == datetime:
        Ttimes = Ttime(Times=_time)
    else:
        raise ValueError(_time[0].__class__)

    xr_wave = xr.Dataset(
        data_vars={
            "TIME": ("time", Ttimes.TIME)},
        coords={
            "longitude": _lon,
            "latitude": _lat,
            "time": Ttimes.time,
        },
        attrs={
            "product_name": kwargs.get('product_name', 'None'),
            "source": kwargs.get('source', 'Alaea'),
            "start": kwargs.get('start', 'None'),
            "history": history,
            "program_version": program_version,
        }
    )
    xr_wave = add_lon_attrs(xr_wave, lon_name='longitude')
    xr_wave = add_lat_attrs(xr_wave, lat_name='latitude')
    xr_wave = add_time_attrs(xr_wave, time_name='time')
    xr_wave = add_TIME_attrs(xr_wave, TIME_name='TIME', dim_name='DateStr')
    
    if 'swh' in kwargs:
        _swh = kwargs.get('swh')
        xr_wave['swh'] = (("time", "latitude", "longitude"), _swh)
    
    if 'mwd' in kwargs:
        _mwd = kwargs.get('mwd')
        xr_wave['mwd'] = (("time", "latitude", "longitude"), _mwd)
    
    if 'mwp' in kwargs:
        _mwp = kwargs.get('mwp')
        xr_wave['mwp'] = (("time", "latitude", "longitude"), _mwp)
    
    if 'mwl' in kwargs:
        _mwl = kwargs.get('mwl')
        xr_wave['mwl'] = (("time", "latitude", "longitude"), _mwl)
    
    if 'pp1d' in kwargs:
        _pp1d = kwargs.get('pp1d')
        xr_wave['pp1d'] = (("time", "latitude", "longitude"), _pp1d)
    
    if 'shww' in kwargs:
        _shww = kwargs.get('shww')
        xr_wave['shww'] = (("time", "latitude", "longitude"), _shww)
    
    if 'shts' in kwargs:
        _shts = kwargs.get('shts')
        xr_wave['shts'] = (("time", "latitude", "longitude"), _shts)
    
    if 'mdww' in kwargs:
        _mdww = kwargs.get('mdww')
        xr_wave['mdww'] = (("time", "latitude", "longitude"), _mdww)

    if 'mdts' in kwargs:
        _mdts = kwargs.get('mdts')
        xr_wave['mdts'] = (("time", "latitude", "longitude"), _mdts)
    
    if 'mpww' in kwargs:
        _mpww = kwargs.get('mpww')
        xr_wave['mpww'] = (("time", "latitude", "longitude"), _mpww)
    
    if 'mpts' in kwargs:
        _mpts = kwargs.get('mpts')
        xr_wave['mpts'] = (("time", "latitude", "longitude"), _mpts)
    
    if 'hmax' in kwargs:
        _hmax = kwargs.get('hmax')
        xr_wave['hmax'] = (("time", "latitude", "longitude"), _hmax)
    
    xr_wave = add_wave_attrs(xr_wave)
    
    # 去掉上面用过的key
    for key in ['swh', 'mwd', 'mwp', 'mwl', 'pp1d', 'shww', 'shts', 'mdww', 'mdts', 'mpww', 'mpts', 'hmax',
                'product_name', 'source', 'start']:
        if key in kwargs:
            kwargs.pop(key)
    xr_wave = fixed_encoding(xr_wave, **kwargs)
    
    # 排序
    ordered_vars = ['longitude', 'latitude', 'time', 'TIME',
                    'swh', 'mwd', 'mwp', 'mwl', 'pp1d', 'shww', 'shts', 'mdww', 'mdts', 'mpww', 'mpts', 'hmax']
    existing_vars = [var for var in ordered_vars if var in xr_wave.variables]
    xr_wave = xr_wave[existing_vars]

    return xr_wave
