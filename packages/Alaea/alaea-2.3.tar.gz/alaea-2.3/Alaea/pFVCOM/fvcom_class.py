#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2025/1/10 15:10
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
 
"""
from .fvcom_load import f_load_grid, f_load_time
from .fvcom_image import f_2d_image, f_2d_mesh

__all__ = ['FVCOM']


class FVCOM:
    def __init__(self,
                 fin,
                 Coordinate='geo',
                 MaxLon=180,
                 Global=False,
                 Nodisp=False):
        self.fin = fin
        self.grid = None
        self.Ttimes = None
        
        self.Coordinate = Coordinate
        self.MaxLon = MaxLon
        self.Global = Global
        self.Nodisp = Nodisp
        
        self.load()
    
    def load(self):
        self.grid = f_load_grid(self.fin, Coordinate=self.Coordinate, MaxLon=self.MaxLon, Global=self.Global, Nodisp=self.Nodisp)
        self.Ttimes = f_load_time(self.fin)

    def draw_2d_mesh(self, Color='k'):
        f_2d_mesh(self.grid, Global=self.Global, Color=Color)

    def draw_2d_image(self, var):
        f_2d_image(self.grid, var)