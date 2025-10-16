#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/3/9 14:06
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
https://pypi.org/project/Alaea/#history
"""
import os

# /Users/christmas/opt/anaconda3/lib/python3.9/site-packages

PROJECT = 'Alaea'
os.chdir(f'/Users/christmas/Documents/Code/Project/A-pypi/{PROJECT}')
os.system('rm -rf dist build')
os.system('python3 setup.py sdist bdist_wheel')
os.system('twine upload dist/*')
os.system(f'rm -rf /Users/christmas/Documents/Code/Project/A-pypi/{PROJECT}/{PROJECT}.egg-info')
os.system(f'rm -rf /Users/christmas/Documents/Code/Project/A-pypi/{PROJECT}/dist')
os.system(f'rm -rf /Users/christmas/Documents/Code/Project/A-pypi/{PROJECT}/build')
os.system(f'rm -rf /Users/christmas/Documents/Code/Project/A-pypi/{PROJECT}/{PROJECT}.egg-info')
