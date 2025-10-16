#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2024/11/6 16:36
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
 
"""
import math
import numpy as np
import warnings

warnings.warn('This module has not been checked yet', UserWarning)


def haversine(origin, destination, units='km', ellipsoid="WGS84"):
    """
    To calculate distance between two points in Earth giving their coordinates (lat,lon)
    Parameters
    ----------
    origin:array like (lat,lon)
    coordinates of origin point
   
    destination: array like (lat,lon)
    coordinates of destinations points
   
    units: str
    units to return distance
    aviable units are kilometers (km), meters (m) and miles (mi)
   
    ellipsoid: String: type of projection
    aviables: Airy (1830), Bessel,Clarke (1880),FAI sphere,GRS-67,International,Krasovsky,NAD27,WGS66,WGS72,IERS (2003),WGS84- default WGS84
    return distance between points
    """
    if units == "km" or units == "kilometers":
        factor = 1
    elif units == "m" or units == "meters":
        factor = 1000
    elif units == "miles" or units == "mi":
        factor = 0.621371
    else:
        raise ValueError('aviable units are kilometers (km), meters (m) and miles (mi)')
    lat0, lon0 = origin
    
    ellipsoids = {
        "Airy (1830)": (6377.563, 6356.257),  # Ordnance Survey default
        "Bessel": (6377.397, 6356.079),
        "Clarke (1880)": (6378.249145, 6356.51486955),
        "FAI sphere": (6371, 6371),  # Idealised
        "GRS-67": (6378.160, 6356.775),
        "International": (6378.388, 6356.912),
        "Krasovsky": (6378.245, 6356.863),
        "NAD27": (6378.206, 6356.584),
        "WGS66": (6378.145, 6356.758),
        "WGS72": (6378.135, 6356.751),
        "WGS84": (6378.1370, 6356.7523),  # GPS default
        "IERS (2003)": (6378.1366, 6356.7519),
    }
    
    r1, r2 = ellipsoids[ellipsoid]
    lat, lon = destination
    mean_latitude = (lat0 + lat) / 2
    A = (r1 * r1 * math.cos(mean_latitude)) ** 2
    B = (r2 * r2 * math.sin(mean_latitude)) ** 2
    C = (r1 * math.cos(mean_latitude)) ** 2
    D = (r2 * math.sin(mean_latitude)) ** 2
    radius = np.sqrt((A + B) / (C + D))  # radius of the earth in km
    
    dlat = math.radians(lat - lat0)
    dlon = math.radians(lon - lon0)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat0)) \
        * math.cos(math.radians(lat)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = radius * c * factor
    
    return distance


if __name__ == '__main__':
    lat1 = 22.5
    lon1 = -74.3
    lat2 = 23.8
    lon2 = -83.2
    
    haversine((lat1, lon1), (lat2, lon2), units='km')
