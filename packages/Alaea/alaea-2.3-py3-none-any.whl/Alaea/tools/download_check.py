#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/7/20 19:56
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
下载记录器
"""
import json
import os
from collections import OrderedDict
from .. import Blog


class deal_download_json:
    def __init__(self, file_all, json_file, logger=Blog().logger, **kwargs):
        self.file_all = file_all
        self.json_file = json_file
        self.logger = logger
        self.kwargs = kwargs
    
    def operate_json(self):  # sourcery skip: low-code-quality
        """
        生成json文件，里面的key是数据文件名以及一个download_sign，value为0或1或2
        0 --> 未下载
        1 --> 已下载
        2 --> 已转换
        """
        if not os.path.exists(self.json_file):  # 不存在先制作一个列表，里面的元素是要下载数据文件名
            file_need_down, file_need_trans = self.generate_json()
        else:  # 存在检查是否全部下载完成
            file_need_down, file_need_trans = self.regenerate_json()
        return file_need_down, file_need_trans
    
    def generate_json(self):
        """
        不存在json文件，生成json文件
        """
        download_sign = OrderedDict()  # 有序字典
        download_sign.update(self.kwargs)
        # 不存在先制作一个列表，里面的元素是要下载数据文件名
        file_need_down = []  # 要下载的文件名列表
        file_need_trans = []  # 要转换的文件名列表
        # 生成文件名
        for filename in self.file_all:
            download_sign[filename] = 0
            file_need_down.append(filename)
        with open(self.json_file, "w", encoding='utf-8') as f:
            json.dump(download_sign, f, indent=2, sort_keys=False, ensure_ascii=False)  # 如果sort_keys=True,则为排序
        self.logger.debug(f'初始{os.path.basename(self.json_file)}文件已生成')
        return file_need_down, file_need_trans
    
    def regenerate_json(self):
        """
        存在json文件，读取json文件
        """
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data_ori = json.load(f)
        file_list_ori = [k for k in data_ori.keys() if data_ori[k] in [1, 2]]
        file_list_plus = list(set(file_list_ori) - (set(file_list_ori) & set(self.file_all)))
        file_list_plus = sorted(file_list_plus, key=lambda x: file_list_ori.index(x))
        
        data_new = OrderedDict()
        data_new.update(self.kwargs)
        data_new_key = self.file_all + file_list_plus
        for kkey in data_new_key:
            data_new[kkey] = data_ori[kkey] if kkey in data_ori.keys() else 0
        if 0 in data_new.values():
            self.logger.debug('开始补充下载')
        elif 1 in data_new.values():
            self.logger.debug('开始补充转化')
        else:
            self.logger.debug('当前没有文件需要下载或转化')
        file_need_down = [k for k, v in data_new.items() if v == 0]
        file_need_trans = [k for k, v in data_new.items() if v == 1]
        with open(self.json_file, "w", encoding='utf-8') as f:
            json.dump(data_new, f, indent=2, sort_keys=False, ensure_ascii=False)  # 如果sort_keys=True,则为排序
        self.logger.debug(f'更新{os.path.basename(self.json_file)}文件')
        return file_need_down, file_need_trans
    
    def update_json(self, file, status_code):
        """
        更新json文件中的value
        :param file: 文件名 --> gfs.t00z.pgrb2.0p25.f001
        :param status_code: 状态码 --> 0:未下载 1:已下载 2:已转化
        """
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data_all = json.load(f)
        data_all[file] = status_code
        with open(self.json_file, "w", encoding='utf-8') as f:
            json.dump(data_all, f, indent=2, sort_keys=False, ensure_ascii=False)
        self.logger.debug(f'已更新json文件中{file}的状态！')
