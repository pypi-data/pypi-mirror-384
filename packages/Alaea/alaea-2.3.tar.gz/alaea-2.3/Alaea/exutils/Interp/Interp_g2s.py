#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  日期 : 2023/3/1 20:22
#  作者 : Dovelet, Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
用于将网格数据转换为单点数据， 并将单点数据转换为json｜txt文件
Have done!!!
"""
import argparse
import datetime
import itertools
import json
import math
import os
import contextlib
import netCDF4
import numpy as np
import scipy.spatial as spt
from Alaea import osprint2

__all__ = ['Grid2Sca']


class Grid2Sca:
    def __init__(self, s_lon, s_lat, _input, _output, _name, value_list, title_list, m_hours=216, time_zone=8, search_point=4, _location=None, _method=None):
        self.s_lon = s_lon  # 单点经度
        self.s_lat = s_lat  # 单点纬度
        self._input = _input  # 输入数据文件夹， 如：'/home/ocean/ForecastSystem/WW3_6.07/Output/ww3_dql/', 内存有'yyyymmdd/ww3.yyyymmdd.nc'文件
        self._output = _output    # 输出数据文件夹， 如：'/home/ocean/PostProcess/160/Data/single_json/'
        self._name = _name          # 输出文件名称， 如：'dql01_'
        self.value_list=value_list  # 需要提取的变量列表
        self.title_list=title_list    # 需要提取的变量名称列表
        self.m_hours = list(range(m_hours))  # 预报时效
        self.time_zone = time_zone    # 时间区间， 如：8
        self.search_point = search_point  # 搜索点数
        self._location = _location  # json文件的location信息
        self.method = _method  # 插值方法

    @staticmethod
    def getTime(_date, _hour):
        """
        获取预报的日期/小时
        :param _date: 任务日期
        :param _hour: 小时
        :return: 日期/小时(10位长度的字符串)
        """
        if _hour == 215:
            _hour = 215

        date = convertToTime(_date)
        date_t = date + datetime.timedelta(hours=int(_hour))

        return date_t.strftime('%Y%m%d%H')

    def makefore(self, _date, _txt=True, _json=True):
        # sourcery skip: extract-duplicate-method, low-code-quality
        """
        txt 预报单的生成
        :param _date: 任务日期
        :param _txt: 是否生成txt文件
        :param _json: 是否生成json文件
        :return: none
        """
        if isinstance(_date, int):
            _date = str(_date)

        file_path = self._output
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        methond, para1, para2 = self.judge_method(_date)  # 并不知道所采用的是什么方法，但都会传回三个参数
        # 写入文件内容----------------------------------begin

        if _txt and not _json:  # 只生成txt文件
            osprint2('INFO', '生成txt文件中')

            tmp = self.m_hours

            file_name = self._name + _date + ".txt"

            file = os.path.join(file_path, file_name)

            with open(file, "w") as fl:
                # 写入文件头----------------------------------begin
                fl.writelines("UTC{0:+03d}".format(self.time_zone).rjust(10, " "))
                for ele in self.title_list:
                    fl.writelines(ele.rjust(14, " "))
                fl.writelines('\n')
                # 写入文件头----------------------------------end

                for i in range(max(tmp) + 1):
                    fc_time = self.getTime(_date, i)  # 获取时间
                    txt_ele, json_ele = self.getfore(_date, i, methond, para1, para2)  # 获取
                    del json_ele
                    if i in self.m_hours:
                        fl.writelines(fc_time)
                        fl.writelines(txt_ele)
                        fl.writelines('\n')
                        osprint2('SUCCESS', f"hour in={str(i)}")
        elif _txt:
            osprint2('INFO', '开始生成txt和json文件')

            tmp = self.m_hours
            json_data_list = []
            txt_data_list = []
            for i in range(max(tmp) + 1):
                # 创建json数据----------------------------------begin
                fc_time = self.getTime(_date, i)  # 第一列日期留空白

                txt_ele, json_ele = self.getfore(_date, i, methond, para1, para2)  # 获取
                del txt_ele
                for j in range(len(json_ele)):
                    if str(json_ele[j]).strip() == "--":
                        json_ele[j]=np.nan

                JsonData, TxtData = self.getTxtJsonData(fc_time, json_ele)  # dict()
                ## json
                json_data_list.append(JsonData)
                ## txt
                txt_data_list.append(TxtData)

                # 创建json数据----------------------------------end
                if i in self.m_hours:
                    osprint2('SUCCESS', f"hour in={str(i)}")
            # 创建json文件----------------------------------begin
            file_name_json = self._name + _date + ".json"
            file_json = os.path.join(file_path, file_name_json)
            if self._location is None:
                new_dict = {"location": {"lon": self.s_lon, "lat": self.s_lat}, "data": json_data_list}
            else:
                new_dict = {"location": self._location, "data": json_data_list}

            with open(file_json, "w") as f:
                json.dump(new_dict, f, ensure_ascii=False, indent=10)
            # 写入json文件内容----------------------------------end

            # 创建txt文件----------------------------------begin
            file_name_txt = self._name + _date + ".txt"
            file_txt = os.path.join(file_path, file_name_txt)
            # 写入txt文件内容----------------------------------begin
            with open(file_txt, "w") as fl:
                fl.writelines("UTC{0:+03d}".format(self.time_zone).rjust(10, " "))
                for ele in self.title_list:
                    fl.writelines(ele.rjust(14, " "))
                fl.writelines('\n')
                for row in txt_data_list:
                    fl.writelines(row)
                    fl.writelines('\n')
            # 写入txt文件内容----------------------------------end
        elif _json:
            osprint2('INFO', '开始生成json文件')

            tmp = self.m_hours
            json_data_list = []
            for i in range(max(tmp) + 1):
                # 创建json数据----------------------------------begin
                fc_time = self.getTime(_date, i)  # 第一列日期留空白

                txt_ele, json_ele = self.getfore(_date, i, methond, para1, para2)  # 获取
                del txt_ele
                for j in range(len(json_ele)):
                    if str(json_ele[j]).strip() == "--":
                        json_ele[j]=np.nan

                JsonData = self.getJsonData(fc_time, json_ele)  # dict()
                ## json
                json_data_list.append(JsonData)

                # 创建json数据----------------------------------end
                if i in self.m_hours:
                    osprint2('SUCCESS', f"hour in={str(i)}")
            # 创建json文件----------------------------------begin
            file_name = self._name + _date + ".json"
            file = os.path.join(file_path, file_name)
            if self._location is None:
                new_dict = {"location": {"lon": self.s_lon, "lat": self.s_lat}, "data": json_data_list}
            else:
                new_dict = {"location": self._location, "data": json_data_list}

            with open(file, "w") as f:
                json.dump(new_dict, f, ensure_ascii=False, indent=10)
            # 写入json文件内容----------------------------------end

    def getJsonData(self, fc_time, json_ele):
        postData = {'date': fc_time}
        for i in range(len(self.value_list)):
            postData[self.title_list[i]] = np.float64(json_ele[i])

        return postData
    
    def getTxtJsonData(self, fc_time, json_ele):
        postJsonData = {'date': fc_time}
        PostTxtData = [fc_time]
        for i in range(len(self.value_list)):
            postJsonData[self.title_list[i]] = json_ele[i]
            PostTxtData.append(str(json_ele[i]).format('.2f').rjust(14, " "))

        return postJsonData, PostTxtData

    def getfore(self, _date, _idx, methond, para1, para2):
        # sourcery skip: low-code-quality
        """
        获取数据
        :param methond:
        :param para2:
        :param para1:
        :param _date: 任务日期
        :param _idx: 小时
        :return: 有效波高，平均周期，谱峰周期，平均波向...
        """
        # 时间处理，将UTC转为CST
        date1 = datetime.datetime.strptime(f'{_date}00', '%Y%m%d%H')
        _idx = _idx - self.time_zone  # 向前8个钟头，找到CST当天的0点, 如CST应为 - 8
        date2 = date1 + datetime.timedelta(hours=_idx)
        idx = _idx % 24
        filename = os.path.join(self._input, f"{date2.strftime('%Y%m%d')}/ww3.{date2.strftime('%Y%m%d')}.nc")  # ww3 nc文件名

        w = netCDF4.Dataset(filename)  # 读取ww3_Wp的nc文件，传入w中
        lons = w.variables['longitude'][:]
        lats = w.variables['latitude'][:]
        interp_value=[]
        interp_num=[]
        if methond=='nearest':
            for ele in self.value_list:
                element= w.variables[ele][idx, :, :]
                if ele=='fp':
                    temp=1/self.gts_nearest(lons, lats, element, self.s_lon, self.s_lat)
                elif ele=='hmaxe':
                    element = w.variables['hs'][idx, :, :]
                    temp=1.46*self.gts_nearest(lons, lats, element, self.s_lon, self.s_lat)
                else:
                    temp=self.gts_nearest(lons, lats, element, self.s_lon, self.s_lat)
                interp_value, interp_num = self.return_str_value(interp_value, interp_num, temp)
        elif methond=='onelon':
            for ele in self.value_list:
                element= w.variables[ele][idx, :, :]
                if ele=='dir':
                    u = -1 * np.sin(np.deg2rad(element))  # 波向分解
                    u_new=self.gts_onelon(lats, u, para1, para2)
                    v = -1 * np.cos(np.deg2rad(element))  # 波向分解
                    v_new=self.gts_onelon(lats, v, para1, para2)
                    temp=np.rad2deg(np.arctan2(u_new, v_new))+180
                elif ele=='fp':
                    temp = 1/self.gts_onelon(lats, element, para1, para2)
                elif ele=='hmaxe':
                    element = w.variables['hs'][idx, :, :]
                    temp = 1.46*self.gts_onelon(lats, element, para1, para2)
                else:
                    temp=self.gts_onelon(lats, element, para1, para2)
                interp_value, interp_num = self.return_str_value(interp_value, interp_num, temp)
        elif methond=='onelat':
            for ele in self.value_list:
                element= w.variables[ele][idx, :, :]
                if ele == 'dir':
                    u = -1 * np.sin(np.deg2rad(element))  # 波向分解
                    u_new = self.gts_onelat(lats, u, para1, para2)
                    v = -1 * np.cos(np.deg2rad(element))  # 波向分解
                    v_new = self.gts_onelat(lats, v, para1, para2)
                    temp=np.rad2deg(np.arctan2(u_new, v_new))+180
                elif ele=='fp':
                    temp = 1/self.gts_onelat(lats, element, para1, para2)
                elif ele=='hmaxe':
                    element = w.variables['hs'][idx, :, :]
                    temp = 1.46*self.gts_onelat(lats, element, para1, para2)
                else:
                    temp = self.gts_onelat(lats, element, para1, para2)
                interp_value, interp_num = self.return_str_value(interp_value, interp_num, temp)

        elif methond=='linear':
            for ele in self.value_list:
                element= w.variables[ele][idx, :, :]
                if ele == 'dir':
                    u = -1 * np.sin(np.deg2rad(element))  # 波向分解
                    u_new = self.gts_linear(lons, lats, u, self.s_lon, self.s_lat, para1, para2)
                    v = -1 * np.cos(np.deg2rad(element))  # 波向分解
                    v_new = self.gts_linear(lons, lats, v, self.s_lon, self.s_lat, para1, para2)
                    temp=np.rad2deg(np.arctan2(u_new, v_new))+180
                elif ele=='fp':
                    temp = 1/self.gts_linear(lons, lats, element, self.s_lon, self.s_lat, para1, para2)
                elif ele=='hmaxe':
                    element = w.variables['hs'][idx, :, :]
                    temp =1.46* self.gts_linear(lons, lats, element, self.s_lon, self.s_lat, para1, para2)
                else:
                    temp=self.gts_linear(lons, lats, element, self.s_lon, self.s_lat, para1, para2)
                interp_value, interp_num = self.return_str_value(interp_value, interp_num, temp)
        elif methond=='idw':
            for ele in self.value_list:
                element= w.variables[ele][idx, :, :]
                if ele =='dir':
                    u = -1 * np.sin(np.deg2rad(element))  # 波向分解
                    u_new = self.gts_idw(u, para1, para2)
                    v = -1 * np.cos(np.deg2rad(element))  # 波向分解
                    v_new = self.gts_idw(v, para1, para2)
                    temp=np.rad2deg(np.arctan2(u_new, v_new))+180
                elif ele == 'fp':
                    temp = 1/self.gts_idw(element, para1, para2)
                elif ele=='hmaxe':
                    element = w.variables['hs'][idx, :, :]
                    temp=1.46*self.gts_idw(element, para1, para2)
                else:
                    temp=self.gts_idw(element, para1, para2)
                interp_value, interp_num = self.return_str_value(interp_value, interp_num, temp)
        return interp_value, interp_num

    @staticmethod
    def return_str_value(interp_value, interp_num, _value, retract=14):
        if str(_value).strip() == "--":
            _value = np.nan
        _value = np.round(_value, 2)
        interp_value.append(str(_value).format('.2f').rjust(retract, " "))
        interp_num.append(_value)
        return interp_value, interp_num

    @staticmethod
    def find_index(g_lon, g_lat, s_lon, s_lat):
        """
        获取经纬度索引
        :param g_lon: 一维格点经度
        :param g_lat: 一维格点纬度
        :param s_lon: 散点经度
        :param s_lat: 散点纬度
        :return: 纬度索引 经度索引
        """
        latli = np.argmin(np.abs(g_lat - s_lat))
        lonli = np.argmin(np.abs(g_lon - s_lon))
        return latli, lonli

    def search_tree(self, g_lon, g_lat, s_lon, s_lat, k):
        # sourcery skip: list-comprehension, merge-duplicate-blocks
        """
        找到离指定散点最近的K个格点
        :param g_lon: 一维格点经度
        :param g_lat: 一维格点纬度
        :param s_lon: 散点经度
        :param s_lat: 散点纬度
        :param k: 寻找近邻点的个数
        :return: 格点经纬度fp 索引id 距离d
        """
        lat_number = len(g_lat)
        lon_number = len(g_lon)
        # 生成格点坐标，放进一个二维平面
        grid = []
        for i, j in itertools.product(range(lon_number), range(lat_number)):
            x = [g_lon[i], g_lat[j]]
            grid.append(x)
        point = np.array(grid)

        # 用于快速查找的KDTree类
        kt = spt.KDTree(data=point, leafsize=10)
        ckt = spt.cKDTree(point)  # 用C写的查找类，执行速度更快
        find_point = np.array([s_lon, s_lat])  # 原点
        distance, sequence = kt.query(find_point, k)  # 返回最近邻点的距离d和在数组中的顺序sequence
        fp = []
        for i in range(len(point)):
            if k == 1:
                if i == sequence:
                    fp.append(point[i])
            elif i in sequence:
                fp.append(point[i])

        index = []
        for f in fp:
            id = self.find_index(g_lon, g_lat, f[0], f[1])
            index.append(id)

        # 找出最近邻点的位置坐标
        # for i in range(len(point)):
        #     if i == x:
        #         fp = point[i]

        # print('最近邻点距离：', d)
        # print('最近邻点位置：', fp)
        # print('最近邻点索引', index)
        return fp, index, distance

    @staticmethod
    def detect_nan(value):
        """
        判断格点数据是否满足双线性插值条件
        :param value: 取出的格点数据
        :return: 满足则返回1，不满足则返回0
        """
        try:
            if value.mask:
                return 0
        except Exception:
            return 1

    def gts_nearest(self, g_lon, g_lat, value, s_lon, s_lat):
        # sourcery skip: inline-immediately-returned-variable
        """
        最近插值
        :param g_lon: 一维格点经度
        :param g_lat: 一维格点纬度
        :param value: 二维数据
        :param s_lon: 散点经度
        :param s_lat: 散点纬度
        :return: 插值后的数据
        """
        latli, lonli = self.find_index(g_lon, g_lat, s_lon, s_lat)
        result = value[latli, lonli]
        return result

    @staticmethod
    def gts_linear(g_lon, g_lat, value, s_lon, s_lat, fp, id):
        # sourcery skip: inline-immediately-returned-variable
        """
        双线性插值
        :param g_lon: 一维格点经度
        :param g_lat: 一维格点纬度
        :param value: 二维数据
        :param s_lon: 散点经度
        :param s_lat: 散点纬度
        :param fp: 最近邻点的经纬度
        :param id: 最近邻点的索引
        :return: 插值后的数据
        """
        # 获取分辨率
        lat_re = g_lat[1] - g_lat[0]
        lon_re = g_lon[1] - g_lon[0]
        # 获取值
        bot_l = value[id[0]]  # 左下
        bot_r = value[id[1]]  # 右下
        top_l = value[id[2]]  # 左上
        top_r = value[id[3]]  # 右上
        # 获取经纬度
        lon_l = fp[0][0]
        lon_r = fp[2][0]
        lat_t = fp[1][1]
        lat_b = fp[0][1]

        # 第一次插值
        t_line = ((lon_r - s_lon) / lon_re) * top_l + ((s_lon - lon_l) / lon_re) * top_r
        b_line = ((lon_r - s_lon) / lon_re) * bot_l + ((s_lon - lon_l) / lon_re) * bot_r

        # 第二次插值
        result = ((lat_t - s_lat) / lat_re) * b_line + ((s_lat - lat_b) / lat_re) * t_line

        return result

    def gts_onelon(self, g_lat, value, fp, id):
        # sourcery skip: inline-immediately-returned-variable
        """
        只需要一次线性插值
        :param g_lat:
        :param value:
        :param fp:
        :param id:
        :return:
        """
        # 获取分辨率
        lat_re = g_lat[1] - g_lat[0]

        # 获取值
        top = value[id[0]]  # 下
        bot = value[id[1]]  # 上

        # 获取纬度
        lat_t = fp[1][1]
        lat_b = fp[0][1]

        # 插值
        result = ((lat_t - self.s_lat) / lat_re) * bot + ((self.s_lat - lat_b) / lat_re) * top
        return result

    def gts_onelat(self, g_lon, value, fp, id):
        # sourcery skip: inline-immediately-returned-variable
        # 获取分辨率
        lon_re = g_lon[1] - g_lon[0]

        # 获取值
        left = value[id[0]]  # 左
        right = value[id[1]]  # 右

        # 获取经度
        lon_l = fp[0][0]
        lon_r = fp[1][0]

        # 插值
        result = ((lon_r - self.s_lon) / lon_re) * left + ((self.s_lon - lon_l) / lon_re) * right
        return result

    @staticmethod
    def gts_idw(value, cal_id, cal_pa):
        result=0
        for i in range(len(cal_id)):
            result=result+cal_pa[i]*value[cal_id[i]]
        return result

    def judge_method(self, _date):
        # sourcery skip: extract-duplicate-method, inline-variable, low-code-quality, remove-unnecessary-else
        # 读取文件
        _date1=datetime.datetime.strptime(f'{_date}', '%Y%m%d')
        filename = os.path.join(self._input, f"{_date1.strftime('%Y%m%d')}/ww3.{_date1.strftime('%Y%m%d')}.nc")  # ww3 nc文件名
        osprint2('INFO', '正在判断插值方法')
        w = netCDF4.Dataset(filename)  # 读取ww3_Wp的nc文件，传入w中
        lons = w.variables['longitude'][:]
        lats = w.variables['latitude'][:]
        value = w.variables[self.value_list[0]][0, :, :]

        if self.method == 'linear':  # 手动选择插值方法
            fp, id, d = self.search_tree(lons, lats, self.s_lon, self.s_lat, 4)
            osprint2('INFO', '手动选择插值方法 -- 双线性插值')
            return self.method, fp, id
        elif self.method == 'idw':
            cal_id, cal_pa = self.idw_para(lons, lats, value, self.s_lon, self.s_lat)
            osprint2('INFO', '手动选择插值方法 -- 反距离加权插值')
            return self.method, cal_id, cal_pa
        elif self.method == 'nearest':
            fp, id, d = self.search_tree(lons, lats, self.s_lon, self.s_lat, 1)
            osprint2('INFO', '手动选择插值方法 -- 最近邻插值')
            return self.method, fp, id
        else:  # 自动判断
            # 判断该散点是否落在格点经纬线上，如果在那么只需要进行一次插值即可
            if self.s_lon in lons and self.s_lat not in lats:
                fp, id, d = self.search_tree(lons, lats, self.s_lon, self.s_lat, 2)
                top = value[id[0]]  # 下
                test = [self.detect_nan(top)]
                bot = value[id[1]]  # 上
                test.append(self.detect_nan(bot))
                if 0 < test.count(0) < 2:
                    osprint2('INFO', '该点附近存在nan值，不满足线性插值条件，使用反距离权重插值')
                    method = 'idw'
                    cal_id, cal_pa=self.idw_para(lons, lats, value, self.s_lon, self.s_lat)
                    return method, cal_id, cal_pa
                elif test.count(0) == 2:
                    osprint2('INFO', '该点附近全是nan值，识别为陆地，使用临近插值')
                    method = 'nearest'
                    return method, fp, id
                else:
                    osprint2('INFO', '该点落在格点经线上，使用一次线性插值即可')
                    method='onelon'
                    return method, fp, id
    
            elif self.s_lat in lats and self.s_lon not in lons:
                fp, id, d = self.search_tree(lons, lats, self.s_lon, self.s_lat, 2)
                left = value[id[0]]  # 左
                test = [self.detect_nan(left)]
                right = value[id[1]]  # 右
                test.append(self.detect_nan(right))
                if 0 < test.count(0) < 2:
                    osprint2('INFO', '该点附近存在nan值，不满足线性插值条件，使用反距离权重插值')
                    method = 'idw'
                    cal_id, cal_pa = self.idw_para(lons, lats, value, self.s_lon, self.s_lat)
                    return method, cal_id, cal_pa
    
                elif test.count(0) == 2:
                    osprint2('INFO', '该点附近全是nan值，识别为陆地，使用临近插值')
                    method = 'nearest'
                    return method, fp, id
                else:
                    osprint2('INFO', '该点落在格点经线上，使用一次线性插值即可')
                    method='onelat'
                    return method, fp, id
            else:
                fp, id, d = self.search_tree(lons, lats, self.s_lon, self.s_lat, 4)
                # print(fp)
                # print(id)
    
                # 判断该散点是否为格点
    
                if 0 in d:
                    osprint2('INFO', '该点为格点，使用临近插值')
                    method = 'nearest'
                    return method, fp, id
                else:
                    # 获取值
                    bot_l = value[id[0]]  # 左下
                    test = [self.detect_nan(bot_l)]
                    bot_r = value[id[1]]  # 右下
                    test.append(self.detect_nan(bot_r))
                    top_l = value[id[2]]  # 左上
                    test.append(self.detect_nan(top_l))
                    top_r = value[id[3]]  # 右上
                    test.append(self.detect_nan(top_r))
                    # print(bot_r, bot_l, top_r, top_l)
                    # 判断格点是否满足双线性插值条件
                    if 0 < test.count(0) < 4:
                        osprint2('INFO', '该点附近存在nan值，不满足线性插值条件，使用反距离权重插值')
                        method = 'idw'
                        cal_id, cal_pa = self.idw_para(lons, lats, value, self.s_lon, self.s_lat)
                        return method, cal_id, cal_pa
    
                    elif test.count(0) == 4:
                        osprint2('INFO', '该点附近全是nan值，识别为陆地，使用临近插值')
                        method = 'nearest'
                        return method, fp, id
                    else:
                        osprint2('INFO', '该点满足线性插值条件,使用双线性插值')
                        method = 'linear'
                        return method, fp, id

    def idw_para(self, g_lon, g_lat, value, s_lon, s_lat):
        lat_number = len(g_lat)
        lon_number = len(g_lon)
        # 生成格点坐标，放进一个二维平面
        grid = []
        for i, j in itertools.product(range(lon_number), range(lat_number)):
            x = [g_lon[i], g_lat[j]]
            grid.append(x)
        point = np.array(grid)

        # 用于快速查找的KDTree类
        kt = spt.KDTree(data=point, leafsize=10)
        ckt = spt.cKDTree(point)  # 用C写的查找类，执行速度更快
        find_point = np.array([s_lon, s_lat])  # 原点
        distance, sequence = kt.query(find_point, self.search_point)  # 返回最近邻点的距离d和在数组中的顺序sequence
        fp = []  # 存格点
        if self.search_point == 1:
            fp.extend(point[i] for i in range(len(point)) if i == sequence)
        else:
            fp.extend(point[p] for p in sequence)
        index = []  # 存索引
        for f in fp:
            id = self.find_index(g_lon, g_lat, f[0], f[1])
            index.append(id)

        cal_id=[]  # 存可以进入计算的点的索引
        cal_d=[]
        for i in range(len(index)):
            if self.detect_nan(value[index[i]]):
                cal_id.append(index[i])
                cal_d.append(distance[i])
        #反距离加权参数的计算
        cal_pa=[]
        total = 0
        for item in cal_d:
            total = total + 1 / item
        cal_pa.extend((1/dis)/total for dis in cal_d)
        return cal_id, cal_pa

    @staticmethod
    def uv2dir(u, v):
        # u,v为波的去向，该函数得到的角度为波的来向(单位为：度，正北为0°，顺时针旋转)
        u *= -1
        v *= -1
        degree = math.degrees(np.arctan(u / v))
        if u > 0 and v > 0:
            pass
        elif u > 0 > v:
            # 这种情况下原degree < 0
            degree += 180
        elif u < 0 < v:
            # 这种情况下原degree < 0
            degree += 360
        elif u < 0 and v < 0:
            degree += 180
        elif u == 0 and v > 0:
            degree = 0
        elif u == 0 and v < 0:
            degree = 180
        elif v == 0 and u > 0:
            degree = 90
        elif v == 0 and u < 0:
            degree = 270
        return degree


def convertToTime(strDate):
    """
    将 %Y%m%d 格式的8位字符串，转换为日期
    :param strDate: %Y%m%d 格式的8位日期字符串
    :return: datetime 类型的日期
    """
    date = datetime.datetime.now()  # 默认取当天日期
    
    with contextlib.suppress(Exception):
        if len(strDate) == 8:
            date = datetime.datetime.strptime(strDate, "%Y%m%d")
        elif len(strDate) == 10:
            date = datetime.datetime.strptime(strDate, "%Y%m%d%H")
        elif len(strDate) == 12:
            date = datetime.datetime.strptime(strDate, "%Y%m%d%H%M")
        elif len(strDate) == 14:
            date = datetime.datetime.strptime(strDate, "%Y%m%d%H%M%S")
    return date
    

def getToday():
    """
    返回当天日期的 %Y%m%d 格式的8位字符串
    :return:
    """
    return datetime.datetime.now().strftime('%Y%m%d')


## 外参部分 argparse
def get_parser():
    # Grid2scatter.conf文件路径
    baysalt_path = os.path.dirname(os.path.abspath(__file__))
    Conf_Grid2scatter_file = os.path.join(baysalt_path, 'Configures', 'Grid2scatter.conf')
    # 区分参数大小写
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="End help",
        add_help=False,
        prog=f'./{os.path.basename(__file__)}',
        conflict_handler='error',
        formatter_class=argparse.RawTextHelpFormatter,
        allow_abbrev=True,
        prefix_chars='-+',
        # description='Usages',
    )
    parser.add_argument_group(
        'Usages Help', '%(prog)s \n'
        '                -m liner \n'
        '                -t 8 \n'
        '                -p 4 \n'
        '                -lon 114 \n'
        '                -lat 35 \n'
        '                -iv hs lm \n'
        '                -ov swh mwl \n'
        '                -i  /data/ForecastSystem/WW3_6.07/Output/ww3_WPacific/ \n'
        '                -o  ./ \n'
        '                -n try \n'
        '                -d 20230301 \n'
        '%(prog)s \n'
        '                -conf 1 \n'
        )
    parser.usage = '%(prog)s [options] parameter'
    parser.add_argument('-h',    '--help', action='help', help='show this help message and exit')
    parser.add_argument('-m',    required=False, type=str,   metavar='', default=None,                                                 help='set method',              choices=['linear', 'nearest', 'idw', 'auto'])
    parser.add_argument('-t',    required=False, type=int,   metavar='', default=8,                                                    help='set time zone')
    parser.add_argument('-p',    required=False, type=int,   metavar='', default=4,                                                    help='set search point')
    parser.add_argument('-lon',  required=False, type=float, metavar='', default=0,                                                    help='set longitude')
    parser.add_argument('-lat',  required=False, type=float, metavar='', default=0,                                                    help='set latitude')
    parser.add_argument('-iv',   required=False, type=str,   metavar='', default=['hs', 't02', 'dir', 'fp',   'lm',  'hmaxe'],         help='set input variable name', choices=['hs', 't02', 'dir', 'fp', 'lm', 'hmaxe'], nargs='+')
    parser.add_argument('-ov',   required=False, type=str,   metavar='', default=['swh', 'mwp', 'mwd', 'pp1d', 'mwl', 'hmax'],         help='set output variable name', nargs='+')
    parser.add_argument('-i',    required=False, type=str,   metavar='', default='/data/ForecastSystem/WW3_6.07/Output/ww3_WPacific/', help='set input path')
    parser.add_argument('-o',    required=False, type=str,   metavar='', default='./',                                                 help='set output path')
    parser.add_argument('-n',    required=False, type=str,   metavar='', default='g2s_',                                                help='set output file name')
    parser.add_argument('-d',    required=False, type=str,   metavar='', default=getToday(),                               help='set date')
    parser.add_argument('-conf', required=False, type=str,   metavar='', default=Conf_Grid2scatter_file,                               help='set conf')

    return parser.parse_args(), Conf_Grid2scatter_file


def print_args(_args):
    print('-----------------args default-----------------')
    for k, v in vars(_args).items():
        print(f'{k} : {v}')
    print('-----------------args default-----------------')


def example():
    args, _ = get_parser()
    print_args(args)

    X = Grid2Sca(122.247, 35.22,
                 _input=args.i,
                 _output=args.o,
                 _name=args.n,
                 value_list=args.iv,
                 title_list=args.ov,
                 _method=args.m)
    X.makefore(_date=args.d, _json=True, _txt=False)


if __name__ == '__main__':
    example()
