# -*- coding: utf-8 -*-

# @File    : shell_try.py
# @Date    : 2023-06-26
# @Author  : Dovelet
# -*- coding: utf-8 -*-

# @File    : shell_python.py
# @Date    : 2023-06-25
# @Author  : Dovelet
import os
import re
from platform import system
from .. import Blog

__all__ = ['RS_file', 'RS_example', 'read_env_sh', 'source_env']

logger_RS = Blog(_loger_name='ReadSourceENV').logger


def filter_dict(_pattern, _char, _dict):
    """
    :param _pattern: 正则表达式
    :param _char: 要替换的字符
    :param _dict: 要处理的字典
    """
    for kkey, vvalue in _dict.items():
        _alter = re.findall(_pattern, vvalue)
        for _al in _alter:
            _rekey = _al.strip(_char)
            if _rekey in _dict.keys():
                vvalue = vvalue.replace(_al, _dict[_rekey])
                _dict[kkey] = vvalue
    return _dict


def read_env_sh(_Sfile, _logger=logger_RS):  # sourcery skip: low-code-quality
    """
    读取bash.oneapi文件中的加载环境变量的行，并写入os.environ里，
    以 #, if, source开头的行不读取
    非export开头的行不加入os.environ
    """
    # 获取基本路径, 非export开头的行
    path_dict = {}
    with open(_Sfile, 'r') as f:
        for line in f:
            # 跳过以 # 开头的行
            if line.startswith('#') or line.startswith('if') or line.startswith('source') or line.startswith('export'):
                continue
            # 分割键值对
            parts = line.strip().split('=')
            if len(parts) != 2:
                continue
            if '#' in parts[1]:
                parts[1] = parts[1].split('#')[0]
            # 添加键值对
            key, value = parts
            path_dict[key.strip()] = value.strip()

    # 路径的拼接
    pattern1 = r'\$\{[^\}]+\}'  # 匹配${...}的值
    _char = '${}'
    path_dict = filter_dict(pattern1, _char, path_dict)

    # 将export'开头的line一句一句的读取出来
    export_dict = {}
    pattern2 = r'\$([^:]+)'  # 匹配$...的值
    with open(_Sfile, 'r') as f:
        for line in f:
            if line.startswith('export'):
                parts = line.strip().split('=')
                if len(parts) != 2:
                    continue
                if '#' in parts[1]:
                    parts[1] = parts[1].split('#')[0]
                # 检查键是否已经存在
                ex_key, ex_value = parts
                ex_key = ex_key.replace('export', '').strip()  # 去掉export
                ex_value = ex_value.strip()  # 去掉空格
                # 头一次出现的键，添加到字典中
                if ex_key in export_dict:
                    # 多次出现的键，替换字典中的值
                    # 替换${...}
                    alter = re.findall(pattern1, ex_value)
                    for al in alter:
                        rekey = al.strip('${}')
                        if rekey in path_dict.keys():
                            ex_value = ex_value.replace(al, path_dict[rekey])
                    # 替换$...
                    alter = re.findall(pattern2, ex_value)
                    for al in alter:
                        rekey = al.strip('$')
                        if rekey in export_dict:
                            ex_value = ex_value.replace(f'${al}', export_dict[rekey])
                            export_dict[ex_key] = ex_value.strip()
                else:
                    try:
                        # 替换${...}
                        alter = re.findall(pattern1, ex_value)
                        for al in alter:
                            rekey = al.strip('${}')
                            if rekey in path_dict.keys():
                                ex_value = ex_value.replace(al, path_dict[rekey])
                                export_dict[ex_key] = ex_value.strip()
                        # 替换$...
                        alter = re.findall(pattern2, ex_value)
                        for al in alter:
                            # 头一次出现时说明要从环境变量里面取值
                            if al == f'{ex_key}':
                                _logger.debug(f'${al} appears for the first time')
                                env_old = os.environ[ex_key]
                                ex_value = ex_value.replace(f'${al}', env_old)
                                export_dict[ex_key] = ex_value.strip()
                            else:
                                rekey = al.strip('$')
                                if rekey in export_dict:
                                    ex_value = ex_value.replace(f'${al}', export_dict[rekey])
                                    export_dict[ex_key] = ex_value.strip()
                    except KeyError:
                        # 判断系统是windows linux还是mac
                        if system() == 'Windows':
                            _logger.debug(f'KeyError: {ex_key} is not in os.environ')
    # 把通过export添加的路径给替换掉
    export_dict = filter_dict(pattern1, _char, export_dict)
    for key, value in export_dict.items():
        _logger.debug([key, value])
    return export_dict


def source_env(_export_dict):
    """
    :param _export_dict: 读取bash.oneapi文件中的加载环境变量的行，并写入os.environ里，
    :return: 返回一个字典
    """
    for key, value in _export_dict.items():
        os.environ[key] = value


def RS_file(_Sfile, _logger=logger_RS):
    """
    :param _Sfile: bash.oneapi文件的路径
    :param _logger: 日志记录器
    :return: None
    """
    source_env(read_env_sh(_Sfile, _logger))


def RS_example():
    """
    :return: None
    """
    _Sfile = r'D:\Graduate_1\new_grid\move_file\bash.oneapi'
    RS_file(_Sfile, logger_RS)


if __name__ == '__main__':
    RS_example()
