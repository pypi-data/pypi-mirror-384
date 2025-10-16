#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/4/12 16:45
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Cprintf
#  版本 : python 3
#  摘要 :
"""

"""

import datetime
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import colorlog
from .commonCode import rmfiles, whether_instanced

__all__ = ['Blog', 'debug', 'info', 'warning', 'error', 'critical', 'exception', 'log']


class Blog:
    """
    先创建日志记录器（logging.getLogger），然后再设置日志级别（logger.setLevel），
    接着再创建日志文件，也就是日志保存的地方（logging.FileHandler），然后再设置日志格式（logging.Formatter），
    最后再将日志处理程序记录到记录器（addHandler）

    Loggers：记录器，提供应用程序代码能直接使用的接口；
    Handlers：处理器，将记录器产生的日志发送至目的地；
    Filters：过滤器，提供更好的粒度控制，决定哪些日志会被输出；
    Formatters：格式化器，设置日志内容的组成结构和消息字段。
            %(name)s Logger的名字         #也就是其中的.getLogger里的路径,或者我们用他的文件名看我们填什么
            %(levelno)s 数字形式的日志级别  #日志里面的打印的对象的级别
            %(levelname)s 文本形式的日志级别 #级别的名称
            %(pathname)s 调用日志输出函数的模块的完整路径名，可能没有
            %(filename)s 调用日志输出函数的模块的文件名
            %(module)s 调用日志输出函数的模块名
            %(funcName)s 调用日志输出函数的函数名
            %(lineno)d 调用日志输出函数的语句所在的代码行
            %(created)f 当前时间，用UNIX标准的表示时间的浮 点数表示
            %(relativeCreated)d 输出日志信息时的，自Logger创建以 来的毫秒数
            %(asctime)s 字符串形式的当前时间。默认格式是 “2003-07-08 16:49:45,896”。逗号后面的是毫秒
            %(thread)d 线程ID。可能没有
            %(threadName)s 线程名。可能没有
            %(process)d 进程ID。可能没有
            %(message)s用户输出的消息
    """
    
    def __init__(self, _loger_name='Christmas',  # 日志记录器名称
                 _log_filename=None,  # 日志文件名
                 _switch_write_all_log=False,  # 是否写入日志
                 _switch_write_bug_log=False,  # 是否写入日志
                 _switch_print_log=True,  # 是否打印日志
                 _switch_write_debug_log=False,  # 是否写入单独的debug日志
                 _switch_write_info_log=False,  # 是否写入单独的info日志
                 _switch_write_warning_log=False,  # 是否写入单独的warning日志
                 _switch_write_error_log=False,  # 是否写入单独的error日志
                 _switch_write_critical_log=False,  # 是否写入单独的critical日志
                 _switch_bold_print=True):  # 是否打印彩色日志
        
        self.CRITICAL = logging.CRITICAL
        self.FATAL = self.CRITICAL
        self.ERROR = logging.ERROR
        self.WARNING = logging.WARNING
        self.WARN = self.WARNING
        self.INFO = logging.INFO
        self.DEBUG = logging.DEBUG
        self.NOTSET = logging.NOTSET

        self.loger_name = _loger_name  # 日志记录器名称
        self.logfile_name = _log_filename  # 日志文件名
        self.switch_write_all_log = _switch_write_all_log  # 是否写入全部日志
        self.switch_write_error_plus_log = _switch_write_bug_log  # 是否写入错误日志
        self.switch_print_log = _switch_print_log  # 是否打印日志
        self.switch_write_debug_log = _switch_write_debug_log  # 是否写入单独的debug日志
        self.switch_write_info_log = _switch_write_info_log  # 是否写入单独的info日志
        self.switch_write_warning_log = _switch_write_warning_log  # 是否写入单独的warning日志
        self.switch_write_error_log = _switch_write_error_log  # 是否写入单独的error日志
        self.switch_write_critical_log = _switch_write_critical_log  # 是否写入单独的critical日志
        self.switch_bold_print = _switch_bold_print  # 是否打印彩色日志
        
        self.log_level = None  # 日志级别
        self.maxBytes = None  # 日志文件大小
        self.backupCount = None  # 日志文件数量
        self.write_mode = None  # 日志写入模式
        self.colors_config = None  # 控制台打印颜色配置信息
        self.log_ddt_fmt = None  # 日志文件名时间格式
        self.all_log_filename = None  # 所有日志文件路径
        self.bug_log_filename = None  # 错误日志文件路径
        self.debug_log_filename = None  # debug日志文件路径
        self.info_log_filename = None  # info日志文件路径
        self.warning_log_filename = None  # warning日志文件路径
        self.error_log_filename = None  # error日志文件路径
        self.critical_log_filename = None  # critical日志文件路径
        self.Rotating = None  # 日志文件处理器 time or size
        self.when = None  # 日志文件处理器 time --> S M H D W
        self.interval = None  # 日志文件处理器 time --> 间隔
        self._logger = logging.getLogger(self.loger_name)  # 创建日志记录器
        
        self.PARA_DEFAULT = {
            'maxBytes': 1024 * 1024 * 10,  # 日志文件大小
            'backupCount': 5,  # 日志文件数量
            'colors_config': self.__set_console_color_default(),  # 日志输出颜色
            'log_level': logging.INFO,  # 日志级别
            'log_ddt_fmt': '%Y-%m-%d',  # 日志文件名时间格式
            'logfile_name': 'log',  # 日志文件名
            'write_mode': 'a',  # 日志文件写入模式
            'all_log_filename': 'ALL.log',  # 日志文件路径
            'bug_log_filename': 'BUG.log',  # 日志文件路径
            'debug_log_filename': 'debug.log',  # 日志文件路径
            'info_log_filename': 'info.log',  # 日志文件路径
            'warning_log_filename': 'warning.log',  # 日志文件路径
            'error_log_filename': 'error.log',  # 日志文件路径
            'critical_log_filename': 'critical.log',  # 日志文件路径
            'Rotating': 'size',  # 日志文件处理器 time or size
            'when': 'D',  # 日志文件处理器 time --> S M H D W
            'interval': 1,  # 日志文件处理器 time --> 间隔
        }
        if self.logfile_name is not None:
            self.PARA_DEFAULT['all_log_filename'] = f'{self.logfile_name}_ALL.log'
            self.PARA_DEFAULT['bug_log_filename'] = f'{self.logfile_name}_BUG.log'
            self.PARA_DEFAULT['debug_log_filename'] = f'{self.logfile_name}_debug.log'
            self.PARA_DEFAULT['info_log_filename'] = f'{self.logfile_name}_info.log'
            self.PARA_DEFAULT['warning_log_filename'] = f'{self.logfile_name}_warning.log'
            self.PARA_DEFAULT['error_log_filename'] = f'{self.logfile_name}_error.log'
            self.PARA_DEFAULT['critical_log_filename'] = f'{self.logfile_name}_critical.log'
        
        self.PARA = self.PARA_DEFAULT
        self.setup_Blog()
        # self.console()
    
    def setup_Blog(self, **kwargs):
        
        self.PARA.update(kwargs)
        self.maxBytes = self.PARA['maxBytes']
        self.backupCount = self.PARA['backupCount']
        self.colors_config = self.PARA['colors_config']
        self.log_level = self.PARA['log_level']
        self.log_ddt_fmt = self.PARA['log_ddt_fmt']
        self.write_mode = self.PARA['write_mode']
        self.all_log_filename = self.PARA['all_log_filename']
        self.bug_log_filename = self.PARA['bug_log_filename']
        self.debug_log_filename = self.PARA['debug_log_filename']
        self.info_log_filename = self.PARA['info_log_filename']
        self.warning_log_filename = self.PARA['warning_log_filename']
        self.error_log_filename = self.PARA['error_log_filename']
        self.critical_log_filename = self.PARA['critical_log_filename']
        self.Rotating = self.PARA['Rotating']
        self.when = self.PARA['when']
        self.interval = self.PARA['interval']
        
        if self.write_mode == 'w':  # 删除已存在的日志文件
            rmfiles(self.all_log_filename,
                    self.bug_log_filename,
                    self.debug_log_filename,
                    self.info_log_filename,
                    self.warning_log_filename,
                    self.error_log_filename,
                    self.critical_log_filename)
        self.__rm_single_FileHandler()  # 删除日志记录器handler
        #       实例化之后，再次调用setup_Blog()，会重复添加handler，导致日志重复打印 --> 已解决
        # TODO: 实例化之后，再次调用setup_Blog()，会重复添加handler，删除日志记录器handler时，文件已经存在，需要删除文件 --> 未解决
        # self.console()
    
    def __init_logger_handler(self, logfile_path, Rotating='time', when='H', interval=1):
        # sourcery skip: inline-immediately-returned-variable
        """
        创建日志记录器handler，用于收集日志
        :param logfile_path: 日志文件路径
        :return: 日志记录器
        """
        # 写入文件，如果文件超过1M大小时，切割日志文件
        if Rotating == 'size':
            handler = RotatingFileHandler(filename=logfile_path, maxBytes=self.maxBytes, encoding='utf-8',
                                          mode=self.write_mode, backupCount=self.backupCount)
        elif Rotating == 'time':
            try:
                # noinspection PyArgumentList
                handler = TimedRotatingFileHandler(filename=logfile_path, when=when, interval=interval,
                                                   backupCount=self.backupCount, atTime=datetime.time(0, 0, 0),
                                                   delay=True, utc=False, mode=self.write_mode)
            except TypeError:
                handler = TimedRotatingFileHandler(filename=logfile_path, when=when, interval=interval,
                                                   backupCount=self.backupCount, atTime=datetime.time(0, 0, 0),
                                                   delay=True, utc=False)
        else:
            raise ValueError('Rotating参数错误')
        
        return handler
    
    def __set_log_handler(self, logger_handler, level=logging.DEBUG):
        """
        设置handler级别并添加到logger收集器
        :param logger_handler: 日志记录器
        :param level: 日志记录器级别
        """
        logger_handler.setLevel(level=level)
        self._logger.addHandler(logger_handler)  # 添加到logger收集器
    
    def __set_log_Filter(self, logger_handler, _level):
        """
        设置日志过滤器
        """
        if _level == logging.DEBUG:
            ONLY_LOG = [logging.DEBUG, logging.INFO]
        elif _level == logging.INFO:
            ONLY_LOG = [logging.INFO, logging.WARNING]
        elif _level == logging.WARNING:
            ONLY_LOG = [logging.WARNING, logging.ERROR]
        elif _level == logging.ERROR:
            ONLY_LOG = [logging.ERROR, logging.CRITICAL]
        elif _level == logging.CRITICAL:
            ONLY_LOG = [logging.CRITICAL, float('inf')]
        else:
            raise ValueError('日志级别错误')
        log_filter = logging.Filter()
        logger_handler.setLevel(ONLY_LOG[0])
        log_filter.filter = lambda record: (record.levelno < ONLY_LOG[1])  # 设置过滤等级
        logger_handler.addFilter(log_filter)
        self._logger.addHandler(logger_handler)  # 添加到logger收集器
    
    @staticmethod
    def __set_console_color_default():
        # sourcery skip: inline-immediately-returned-variable
        log_color = {
            # 颜色支持 blue蓝，green绿色，red红色，yellow黄色，cyan青色, purple紫色, white白色, black黑色, grey灰色, bold黑体
            'DEBUG': 'cyan',
            'INFO': 'blue',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'purple',
            'EXCEPTION': 'red',
        }
        return log_color

    def __set_color_formatter(self, console_handle, colors_config):
        """
        设置输出格式-控制台
        :param console_handle: 终端日志记录器
        :param colors_config: 控制台打印颜色配置信息
        :return:
        """
        if self.switch_bold_print:
            formatter = colorlog.ColoredFormatter(
                # 输出那些信息，时间，文件名，函数名等等
                fmt='%(asctime)s ---> %(log_color)s\033[1m[%(levelname)s]\033[0m %(reset)s%(log_color)s%(message)s %(reset)s',
                # 时间格式
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors=colors_config,
                force_color=True,
            )
        else:
            formatter = colorlog.ColoredFormatter(
                # 输出那些信息，时间，文件名，函数名等等
                fmt='%(asctime)s ---> %(log_color)s%(levelname)s] %(reset)s%(log_color)s%(message)s %(reset)s',
                # 时间格式
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors=colors_config,
                force_color=True,
            )
        console_handle.setFormatter(formatter)
    
    @staticmethod
    def __set_log_formatter(file_handler):
        """
        设置日志输出格式-日志文件
        :param file_handler: 日志记录器
        """
        formatter = logging.Formatter(
            fmt='%(asctime)s ---> [%(levelname)s] %(filename)s -> %(funcName)s line:%(lineno)d : %(message)s',
            datefmt='%Y-%m-%d  %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
    
    @staticmethod
    def __close_log_handler(logger_handler):
        """
        关闭日志记录器
        :param logger_handler: 日志记录器
        """
        logger_handler.close()
    
    def console(self):
        """构造日志收集器"""
        self._logger.setLevel(self.log_level)  # 设置日志收集器级别

        if self._logger.hasHandlers():  # 如果已经有日志记录器，先关闭
            self._logger.handlers.clear()
        if self._logger.filters:  # 如果已经有日志过滤器，先关闭
            self._logger.filters.clear()
        if self.switch_write_all_log:  # 是否写入全部日志
            self.__write_all_log()
        if self.switch_write_error_plus_log:  # 是否写入错误日志
            self.__write_error_plus_log()
        if self.switch_print_log:  # 是否打印日志
            self.__print_log()
        if self.switch_write_debug_log:  # 是否写入debug日志
            self.__write_single_log(level=logging.DEBUG, _level_log_name=self.debug_log_filename)
        if self.switch_write_info_log:  # 是否写入info日志
            self.__write_single_log(level=logging.INFO, _level_log_name=self.info_log_filename)
        if self.switch_write_warning_log:  # 是否写入warning日志
            self.__write_single_log(level=logging.WARNING, _level_log_name=self.warning_log_filename)
        if self.switch_write_error_log:  # 是否写入error日志
            self.__write_single_log(level=logging.ERROR, _level_log_name=self.error_log_filename)
        if self.switch_write_critical_log:  # 是否写入critical日志
            self.__write_single_log(level=logging.CRITICAL, _level_log_name=self.critical_log_filename)
            
        # 如果console被执行了一次，那么删除之前的执行结果，重新执行
        return self._logger
    
    def __write_all_log(self):
        all_logger_handler = self.__init_logger_handler(self.all_log_filename, Rotating=self.Rotating, when=self.when,
                                                        interval=self.interval)  # 收集所有日志文件
        self.__set_log_formatter(all_logger_handler)  # 设置日志输出格式-all日志文件
        self.__set_log_handler(all_logger_handler, level=logging.DEBUG)  # 设置handler级别并添加到logger收集器
        self.__close_log_handler(all_logger_handler)  # 关闭handler
    
    def __write_error_plus_log(self):
        error_logger_handler = self.__init_logger_handler(self.bug_log_filename, Rotating=self.Rotating,
                                                          when=self.when, interval=self.interval)  # 收集错误日志信息文件
        self.__set_log_formatter(error_logger_handler)  # 设置日志输出格式-error日志文件
        self.__set_log_handler(error_logger_handler, level=logging.ERROR)  # 设置handler级别并添加到logger收集器
        self.__close_log_handler(error_logger_handler)  # 关闭handler
    
    def __print_log(self):
        console_handle = colorlog.StreamHandler()  # 创建终端日志记录器handler，用于输出到控制台
        self.__set_color_formatter(console_handle, self.colors_config)  # 设置输出格式-控制台
        self.__set_log_handler(console_handle, level=self.log_level)  # 设置handler级别并添加到终端logger收集器
        self.__close_log_handler(console_handle)  # 关闭handler
    
    def __write_single_log(self, level=logging.ERROR, _level_log_name='all.log'):  # 日志单独输出
        single_logger_handler = self.__init_logger_handler(_level_log_name, Rotating=self.Rotating, when=self.when,
                                                           interval=self.interval)  # 收集随机日志信息文件
        self.__set_log_formatter(single_logger_handler)  # 设置日志输出格式-single日志文件
        self.__set_log_Filter(single_logger_handler, level)  # 设置过滤器
        self.__close_log_handler(single_logger_handler)  # 关闭handler

    def __rm_single_FileHandler(self):  # 删除日志文件并关闭日志记录器
        handlers = self._logger.handlers
        for handler in handlers.copy():
            if isinstance(handler, logging.FileHandler):  # 找到文件处理器，进行删除操作
                self._logger.removeHandler(handler)
                handler.close()  # 关闭文件处理器，释放资源

    @property
    def logger(self):
        self.console()
        return self._logger

    @staticmethod
    def addLevelName(level, levelName):
        logging.addLevelName(level, levelName)
    
    @staticmethod
    def getLevelName(level):
        return logging.getLevelName(level)

    def __getitem__(self, item):
        return getattr(self, item)

    def __del__(self):
        # self._logger.handlers.clear()
        # self._logger.filters.clear()
        # del self._logger
        pass

    def __str__(self):
        return 'Blog()'

    def __call__(self, *args, **kwargs):
        return self._logger


def debug(self, *args, **kwargs):
    TF, instanced = whether_instanced(Blog)
    if TF:
        instanced[instanced.keys()[0]].logger.debug(self, *args, **kwargs)
    else:
        Blog().logger.debug(self, *args, **kwargs)


def info(msg, *args, **kwargs):
    TF, instanced = whether_instanced(Blog)
    if TF:
        instanced[instanced.keys()[0]].logger.info(msg, *args, **kwargs)
    else:
        Blog().logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    TF, instanced = whether_instanced(Blog)
    if TF:
        instanced[instanced.keys()[0]].logger.warning(msg, *args, **kwargs)
    else:
        Blog().console().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    Blog().logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    Blog().logger.critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    TF, instanced = whether_instanced(Blog)
    if TF:
        instanced[instanced.keys()[0]].logger.exception(msg, *args, **kwargs)
    else:
        Blog().logger.exception(msg, *args, **kwargs)


def log(level, msg, *args, **kwargs):
    TF, instanced = whether_instanced(Blog)
    if TF:
        instanced[instanced.keys()[0]].logger.log(level, msg, *args, **kwargs)
    else:
        Blog().logger.log(level, msg, *args, **kwargs)


def example_Blog():
    log2 = Blog(_loger_name='Christmas',  # 日志收集器名称
                _log_filename='ChristmasWRITING',  # 日志文件名前缀
                _switch_write_all_log=True,  # 是否写入全部日志 ALL.log
                _switch_write_bug_log=True,  # 是否写入错误日志 BUG.log
                _switch_print_log=True,  # 是否打印日志到控制台
                _switch_write_debug_log=True,  # 是否写入debug日志
                _switch_write_info_log=True,  # 是否写入info日志
                _switch_write_warning_log=True,  # 是否写入warning日志
                _switch_write_error_log=True,  # 是否写入error日志
                _switch_write_critical_log=True,  # 是否写入critical日志
                )
    log2.addLevelName(15, "CUSTOM")  # 自定义日志级别 15 --> CUSTOM
    log2.setup_Blog(write_mode='w')  # 日志写入模式
    log2.setup_Blog(maxBytes=1024 * 1024 * 5)  # 日志文件大小
    log2.setup_Blog(backupCount=5)  # 日志文件数量
    log2.setup_Blog(log_level=1)  # 日志级别
    log2.setup_Blog(log_ddt_fmt='%Y-%m-%d %H:%M:%S')  # 日志时间格式
    log2.setup_Blog(colors_config={
        "CUSTOM": "yellow",
        'DEBUG': 'cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'purple',
        'EXCEPTION': 'red'})  # 日志颜色配置
    log2.setup_Blog(Rotating='time')  # 日志切割模式
    log2.setup_Blog(when='D')  # 日志切割时间
    log2.setup_Blog(interval=1)  # 日志切割间隔
    x = log2.console()  # 日志收集器
    x.debug("这是debug信息")  # 日志输出
    x.log(15, "CUSTOM")  # 自定义日志级别
    x.info("这是日志信息")  # 日志输出
    x.warning("这是警告信息")  # 日志输出
    x.error("这是错误日志信息")  # 日志输出
    x.critical("这是严重级别信息")  # 日志输出


def example_Blog_simple():
    log_1 = Blog()
    log1 = log_1.console()
    log1.debug("这是debug信息")
    log1.info("这是日志信息")
    log1.warning("这是警告信息")
    log1.error("这是错误日志信息")
    log1.critical("这是严重级别信息")


if __name__ == '__main__':
    # example_Blog_simple()
    example_Blog()
