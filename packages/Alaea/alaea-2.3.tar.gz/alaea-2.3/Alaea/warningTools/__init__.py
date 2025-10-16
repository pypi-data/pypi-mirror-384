#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2024/11/18 23:15
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
https://docs.python.org/3/library/warnings.html
"""

import warnings

warnings.warn("UserWarning", UserWarning)  # --> 默认
warnings.warn("DeprecationWarning", DeprecationWarning)  # --> 弃用警告
warnings.warn("PendingDeprecationWarning", PendingDeprecationWarning)  # --> 将来将弃用警告
warnings.warn("SyntaxWarning", SyntaxWarning)  # --> 语法警告
warnings.warn("RuntimeWarning", RuntimeWarning)  # --> 运行时警告
warnings.warn("FutureWarning", FutureWarning)  # --> 未来警告
warnings.warn("ImportWarning", ImportWarning)  # --> 导入警告
warnings.warn("UnicodeWarning", UnicodeWarning)  # --> Unicode警告
warnings.warn("BytesWarning", BytesWarning)  # --> 字节警告
warnings.warn("ResourceWarning", ResourceWarning)  # --> 资源警告
warnings.warn("Warning", Warning)  # --> 警告
