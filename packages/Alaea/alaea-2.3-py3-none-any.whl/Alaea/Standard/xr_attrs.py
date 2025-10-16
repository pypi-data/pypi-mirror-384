#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/9/18 15:38
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
import numpy as np
from .. import new_filename

__all__ = ['add_coors_attrs', 'add_lon_attrs', 'add_lat_attrs', 'add_time_attrs', 'add_TIME_attrs',
           'add_wind_attrs', 'add_temperature_attrs', 'add_precipitation_attrs', 'add_slp_attrs',
           'add_wave_attrs', 'fixed_encoding']


def add_coors_attrs(ds):
    """
    给xarray.Dataset的坐标添加属性
    :param ds: xarray.Dataset
    :return: xarray.Dataset
    """
    lon_name, lat_name, time_name, TIME_name = 'longitude', 'latitude', 'time', 'TIME'
    for i in ds.sizes.keys():  # ds.dims.keys(): --> FutureWarning
        lon_name = i if i in ['lon', 'longitude'] else 'longitude'
        lat_name = i if i in ['lat', 'latitude'] else 'latitude'
        time_name = i if i in ['time'] else 'time'
        TIME_name = i if i in ['TIME'] else 'TIME'
    add_lon_attrs(ds, lon_name)
    add_lat_attrs(ds, lat_name)
    add_time_attrs(ds, time_name)
    add_TIME_attrs(ds, TIME_name, dim_name='DateStr')
    return ds
    

def add_lon_attrs(_ds, lon_name):
    """
    给经度添加属性
    :param _ds: xarray.Dataset
    :param lon_name: 经度维度名
    """
    _ds[lon_name].attrs = {
        'units': 'degrees_east',
        'long_name': 'longitude',
        'standard_name': 'longitude',
        'axis': 'X',
        'westernmost': np.round(_ds[lon_name].data.min(), 2),
        'easternmost': np.round(_ds[lon_name].data.max(), 2),
    }
    _ds[lon_name].encoding = {'_FillValue': None}
    return _ds


def add_lat_attrs(_ds, lat_name):
    """
    给纬度添加属性
    :param _ds: xarray.Dataset
    :param lat_name: 纬度维度名
    """
    _ds[lat_name].attrs = {
        'units': 'degrees_north',
        'long_name': 'latitude',
        'standard_name': 'latitude',
        'axis': 'Y',
        'southernmost': np.round(_ds[lat_name].data.min(), 2),
        'northernmost': np.round(_ds[lat_name].data.max(), 2)
    }
    _ds[lat_name].encoding = {'_FillValue': None}
    return _ds


def add_time_attrs(_ds, time_name):
    """
    给时间添加属性
    :param _ds: xarray.Dataset
    :param time_name: 时间维度名
    """
    _ds[time_name].attrs = {
        'units': 'seconds since 1970-01-01 00:00:00',
        'long_name': 'UTC time',
        'standard_name': 'UTC_time',
        'axis': 'T',
        'calendar': 'gregorian',
    }
    _ds[time_name].encoding = {'_FillValue': None, 'dtype': 'float64', 'unlimited_dims': 'time'}
    return _ds


def add_TIME_attrs(_ds, TIME_name, dim_name='DateStr'):
    """
    给TIME添加属性
    :param _ds: xarray.Dataset
    :param TIME_name: TIME名
    :param dim_name: TIME维度名
    """
    _ds[TIME_name].attrs = {
        'reference_time': ''.join(_ds[TIME_name].data[0].astype(str))[:10],
        'long_name': 'UTC time',
        'standard_name': 'UTC_time',
        'calendar': 'gregorian',
        'start_time': ''.join(_ds[TIME_name].data[0].astype(str)),
        'end_time': ''.join(_ds[TIME_name].data[-1].astype(str))
    }
    _ds[TIME_name].encoding['char_dim_name'] = dim_name
    return _ds


def add_wind_attrs(_ds):
    """
    给xarray.Dataset的风添加属性
    :param _ds: xarray.Dataset
    """
    U10_name, V10_name = 'U10', 'V10'
    for i in list(_ds.data_vars.keys()):
        U10_name = i if i in ['U10', 'u10'] else 'U10'
        V10_name = i if i in ['V10', 'v10'] else 'V10'
    _ds[U10_name].attrs = {
        'units': 'm s-1',
        'long_name': '10 meter U wind component',
        'standard_name': 'eastward_wind',
    }
    _ds[V10_name].attrs = {
        'units': 'm s-1',
        'long_name': '10 meter V wind component',
        'standard_name': 'northward_wind',
    }
    _ds[U10_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)
    _ds[V10_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)
    return _ds


def add_temperature_attrs(_ds):
    """
    给xarray.Dataset的温度添加属性
    :param _ds: xarray.Dataset
    """
    T2_name = 'temperature'
    for i in list(_ds.data_vars.keys()):
        T2_name = i if i in ['T2', 't2'] else T2_name
    _ds[T2_name].attrs = {
        'units': 'K',
        'long_name': 'temperature at 2m',
        'standard_name': 'temperature_at_2m'
    }
    _ds[T2_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)
    return _ds


def add_precipitation_attrs(_ds):
    """
    给xarray.Dataset的降水添加属性
    :param _ds: xarray.Dataset
    """
    precipitation_name = 'precipitation'
    for i in list(_ds.data_vars.keys()):
        precipitation_name = i if i in ['tp', 'TP'] else precipitation_name
    _ds[precipitation_name].attrs = {
        'units': 'mm',
        'long_name': 'precipitation, positive for ocean gaining water',
        'standard_name': 'precipitation_positive_ocean_gaining_water'
    }
    _ds[precipitation_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)
    return _ds


def add_slp_attrs(_ds):
    """
    给xarray.Dataset的海平面气压添加属性
    :param _ds: xarray.Dataset
    """
    slp_name = 'slp'
    for i in list(_ds.data_vars.keys()):
        slp_name = i if i in ['slp', 'SLP'] else slp_name
    _ds[slp_name].attrs = {
        'units': 'Pa',
        'long_name': 'sea level pressure',
        'standard_name': 'sea_level_pressure'
    }
    _ds[slp_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)
    return _ds


def add_wave_attrs(_ds):
    """
    给xarray.Dataset的海浪添加属性
    """
    swh_name, mwp_name, mwd_name, mwl_name = 'swh', 'mwp', 'mwd', 'mwl'
    pp1d_name = 'pp1d'
    shww_name, shts_name, mdww_name, mdts_name = 'shww', 'shts', 'mdww', 'mdts'
    mpww_name, mpts_name, hmax_name = 'mpww', 'mpts', 'hmax'

    for i in list(_ds.data_vars.keys()):
        swh_name = i if i in ['swh'] else swh_name
        mwp_name = i if i in ['mwp'] else mwp_name
        mwd_name = i if i in ['mwd'] else mwd_name
        mwl_name = i if i in ['mwl'] else mwl_name
        pp1d_name = i if i in ['pp1d'] else pp1d_name
        shww_name = i if i in ['shww'] else shww_name
        shts_name = i if i in ['shts'] else shts_name
        mdww_name = i if i in ['mdww'] else mdww_name
        mdts_name = i if i in ['mdts'] else mdts_name
        mpww_name = i if i in ['mpww'] else mpww_name
        mpts_name = i if i in ['mpts'] else mpts_name
        hmax_name = i if i in ['hmax'] else hmax_name

    if swh_name in _ds:
        _ds[swh_name].attrs = {
            'units': 'm',
            'long_name': 'significant wave height',
            'standard_name': 'significant_wave_height'
        }
        _ds[swh_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mwp_name in _ds:
        _ds[mwp_name].attrs = {
            'units': 's',
            'long_name': 'mean wave period',
            'standard_name': 'mean_wave_period'
        }
        _ds[mwp_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mwd_name in _ds:
        _ds[mwd_name].attrs = {
            'units': 'degrees',
            'long_name': 'mean wave direction',
            'standard_name': 'mean_wave_direction',
            'direction_0': 'coming from the north',
            'direction_90': 'coming from the east'
        }
        _ds[mwd_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mwl_name in _ds:
        _ds[mwl_name].attrs = {
            'units': 'm',
            'long_name': 'mean wave length',
            'standard_name': 'mean_wave_length'
        }
        _ds[mwl_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if pp1d_name in _ds:
        _ds[pp1d_name].attrs = {
            'units': 's',
            'long_name': 'peak period',
            'standard_name': 'peak_period'
        }
        _ds[pp1d_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if shww_name in _ds:
        _ds[shww_name].attrs = {
            'units': 'm',
            'long_name': 'significant height of wind waves',
            'standard_name': 'significant_height_of_wind_waves'
        }
        _ds[shww_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if shts_name in _ds:
        _ds[shts_name].attrs = {
            'units': 'm',
            'long_name': 'significant height of total swell',
            'standard_name': 'significant_height_of_total_swell'
        }
        _ds[shts_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mdww_name in _ds:
        _ds[mdww_name].attrs = {
            'units': 'degrees',
            'long_name': 'mean direction of wind waves',
            'standard_name': 'mean_direction_of_wind_waves',
            'direction_0': 'coming from the north',
            'direction_90': 'coming from the east'
        }
        _ds[mdww_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mdts_name in _ds:
        _ds[mdts_name].attrs = {
            'units': 'degrees',
            'long_name': 'mean direction of total swell',
            'standard_name': 'mean_direction_of_total_swell',
            'direction_0': 'coming from the north',
            'direction_90': 'coming from the east'
        }
        _ds[mdts_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mpww_name in _ds:
        _ds[mpww_name].attrs = {
            'units': 's',
            'long_name': 'mean period of wind waves',
            'standard_name': 'mean_period_of_wind_waves'
        }
        _ds[mpww_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if mpts_name in _ds:
        _ds[mpts_name].attrs = {
            'units': 's',
            'long_name': 'mean period of total swell',
            'standard_name': 'mean_period_of_total_swell'
        }
        _ds[mpts_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    if hmax_name in _ds:
        _ds[hmax_name].attrs = {
            'units': 'm',
            'long_name': 'maximum wave height',
            'standard_name': 'maximum_wave_height'
        }
        _ds[hmax_name].encoding = dict(_FillValue=9.962100e+36, dtype='single', zlib=True)

    return _ds


def fixed_encoding(_ds, **kwargs):
    """
    修正xarray.Dataset的encoding
    """
    _ds.encoding['unlimited_dims'] = kwargs.get('unlimited_dims', 'time')
    _ds.encoding['format'] = kwargs.get('format', 'NETCDF4')
    _ds.encoding['engine'] = kwargs.get('engine', 'h5netcdf')
    _ds.encoding['dtype'] = kwargs.get('dtype', 'float32')
    _ds.encoding['complevel'] = kwargs.get('complevel', 4)
    _ds.encoding['zlib'] = kwargs.get('zlib', True)
    _ds.encoding['shuffle'] = kwargs.get('shuffle', True)
    _ds.encoding['fletcher32'] = kwargs.get('fletcher32', True)
    _ds.encoding['contiguous'] = kwargs.get('contiguous', True)
    _ds.encoding.update(kwargs)
    return _ds
