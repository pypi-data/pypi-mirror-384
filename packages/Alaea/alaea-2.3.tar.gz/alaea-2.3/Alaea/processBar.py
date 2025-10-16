#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2023/3/10 13:58
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""
processBar such as: ftp sftp
"""
import datetime
import time
import numpy as np

__all__ = ['translate_byte', 'LowSpeed_Error', 'SftpProcessbar', 'FtpProcessbar', 'FtpHtmlProcessbar']


def translate_byte(B):
    """
    :param B: bytes
    :return: 转换后的bytes
    """
    B = float(B)
    KB = float(1024)
    MB = float(KB * 1024)
    GB = float(MB * 1024)
    TB = float(GB * 1024)
    if B < KB:
        return f"{B} {'bytes' if B > 1 else 'byte'}"
    elif KB <= B < MB:
        return '{:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{:.2f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{:.2f} GB'.format(B / GB)
    else:
        return '{:.2f} TB'.format(B / TB)


class LowSpeed_Error(Exception):
    """
    :param value: 低速异常
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SftpProcessbar(object):
    """
    sftp_obj =SftpProcessbar()
    Sprocess_bar = sftp_obj.process_bar

    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect(hostname=host, port=22, username='wave', password='wave', timeout=100)
    # sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    # sftp_obj =SftpProcessbar()
    # Sprocess_bar = sftp_obj.process_bar
    # sftp.put(local_path, a, callback=Sprocess_bar)
    """

    def __init__(self, bar_length=30, change_percent=1):
        self.bar_length = bar_length
        self.lastShownPercent = 0
        self.change_percent = change_percent

    def call_back(self, curr=100, total=100):
        bar_length = self.bar_length
        percents = '\033[32;1m%s\033[0m' % round(float(curr) * 100 / float(total), self.change_percent)
        filled = int(bar_length * curr / float(total))
        bar = '\033[32;1m%s\033[0m' % '=' * filled + '-' * (bar_length - filled)

        percentComplete = round((curr / total) * 100, self.change_percent)
        if self.lastShownPercent != percentComplete:
            self.lastShownPercent = percentComplete
            ddt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{ddt} ---> [{bar}] {percents}% already complete: {translate_byte(curr)}, total: {translate_byte(total)}            \r', end='')

    def process_bar(self):
        """
        :return: call_back
        """
        return self.call_back


class FtpProcessbar(object):
    """
    ******已废弃******
    ******已废弃******
    ******已废弃******
    upload ------------------->:
    Ftp_obj = FtpProcessbar(os.path.getsize(local_path))
    Fprocess_bar = Ftp_obj.process_bar()

    # ftp = ftplib.FTP()
    # ftp.encoding = 'utf-8'
    # ftp.set_debuglevel(0)
    # ftp.connect(host=_host, port=_port)
    # ftp.login(_username, _password)
    # with open(local_path, 'rb') as fp:
    #   Ftp_obj = FtpProcessbar(os.path.getsize(local_path))
    #   Fprocess_bar = Ftp_obj.process_bar()
    #   ftp.storbinary(f'STOR {file}', fp, buf_size, Fprocess_bar)
    #   ==============================================
    download ------------------->:
    Ftp_obj = FtpProcessbar(ftp.size(local_path), fp=fp)
    Fprocess_bar = Ftp_obj.process_bar()

    # ftp = ftplib.FTP()
    # ftp.encoding = 'utf-8'
    # ftp.set_debuglevel(0)
    # ftp.connect(host=_host, port=_port)
    # ftp.login(_username, _password)
    # Ftp_obj = FtpProcessbar(ftp.size(local_path), fp=fp)
    # Fprocess_bar = Ftp_obj.process_bar()
    # with open(local_path, 'rb') as fp:
    #   Ftp_obj = FtpProcessbar(ftp.size(local_path), fp=fp)
    #   Fprocess_bar = Ftp_obj.process_bar()
    #   ftp.retrbinary(f'RETR {file}', Fprocess_bar,  buf_size)
    """

    def __init__(self, totalSize, fp=None, bar_length=30, change_percent=1):
        self.totalSize = totalSize  # 已上传或下载大小
        self.time_start = time.time()  # 开始上传或下载时间(注意是实例化时开始计时)
        self.sizeWritten = 0   # 文件总大小
        self.lastShownPercent = 0  # 上次显示的百分比
        self.bar_length = bar_length  # 进度条长度
        self.change_percent = change_percent  # 进度条变化百分比 0为1%输出 1为0.1%输出 2为0.01%输出
        if fp:
            self.fp = fp                   # 文件对象

    def call_back(self, block):
        """
        :param block: 上传或下载的数据块
        """
        if self.fp:
            self.fp.write(block)
        self.sizeWritten += len(block)
        percents = '\033[32;1m%s\033[0m' % round(float(self.sizeWritten) * 100 / float(self.totalSize), self.change_percent)
        filled = int(self.bar_length * self.sizeWritten / float(self.totalSize))
        bar = '\033[32;1m%s\033[0m' % '=' * filled + '-' * (self.bar_length - filled)
        speed = self.sizeWritten / (time.time() - self.time_start)

        percentComplete = round((self.sizeWritten / self.totalSize) * 100, self.change_percent)  # 粗分辨率,防止刷新过快
        if self.lastShownPercent != percentComplete:
            self.lastShownPercent = percentComplete
            ddt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'{ddt} ---> [{bar}] {percents}% speed:{translate_byte(speed)}/s, already complete: {translate_byte(self.sizeWritten)}, total: {translate_byte(self.totalSize)}            \r', end='')

    def process_bar(self):
        """
        :return: 返回一个函数对象
        """
        return self.call_back


class FtpHtmlProcessbar(object):
    """
    FTP_upload ------------------->:
    Ftp_obj = FtpHtmlProcessbar(ftp.size(local_path))
    Fprocess_bar = Ftp_obj.callback_ftp()

    ftp = ftplib.FTP()
    ftp.encoding = 'utf-8'
    ftp.set_debuglevel(0)
    ftp.connect(host=_host, port=_port)
    ftp.login(_username, _password)
    try:
        with open(local_path, 'rb') as fp:
            Ftp_obj = FtpHtmlProcessbar(os.path.getsize(local_path))
            Fprocess_bar = Ftp_obj.callback_ftp()
            ftp.storbinary(f'STOR {file}', fp, buf_size, Fprocess_bar)
    except LowSpeed_Error as e:
        print(e.value)
    #-----------------------------------------------#
    FTP_download ------------------->:
    Ftp_obj = FtpHtmlProcessbar(ftp.size(local_path), fp=fp)
    Fprocess_bar = Ftp_obj.callback_ftp()

    ftp = ftplib.FTP()
    ftp.encoding = 'utf-8'
    ftp.set_debuglevel(0)
    ftp.connect(host=_host, port=_port)
    ftp.login(_username, _password)
    try:
        with open(local_path, 'rb') as fp:
            Ftp_obj = FtpHtmlProcessbar(ftp.size(local_path), fp=fp)
            Fprocess_bar = Ftp_obj.callback_ftp()
            ftp.retrbinary(f'RETR {file}', Fprocess_bar,  buf_size)
    except LowSpeed_Error as e:
        print(e.value)

    #===============================================#
    HTML_download ------------------->:
    r = requests.get(url, stream=True)
    if r.status_code == 200:  # 请求成功
        chunksize = 102400    # 每次下载的数据大小
        try:
            with open(f'{self.grb_outpath}/{file}', "wb") as f:
                Html_obj = processBar.FtpHtmlProcessbar(int(r.headers['content-length']), fp=f, exit_num=20)  # 单位是byte
                for chunk in r.iter_content(chunksize):
                    if chunk:
                        Html_obj.callback_html(chunk)
        except LowSpeed_Error as e:
            print(e.value)
    """

    def __init__(self, totalSize, lowSpeed_floor=512*1024, fp=None, lowSpeed_exit_num=30, bar_length=30, change_percent=1, INFO=True):
        self.totalSize = totalSize                        # 文件总大小
        self.lowSpeed_floor = lowSpeed_floor              # 上传或下载退出速度(单位是byte),默认512KB/s
        self.time_start = np.float64(time.time())         # 开始上传或下载时间(注意是实例化时开始计时)
        self.sizeWritten = 0                              # 已上传或下载大小
        self.__lastShownPercent = 0                       # 上次显示的百分比
        self.lowSpeed_num = 0                             # 低速的次数
        self.lowSpeed_exit_num = lowSpeed_exit_num  # 退出次数
        self.__bar_length = bar_length                      # 进度条长度
        self.change_percent = change_percent              # 进度条变化百分比 0为1%输出 1为0.1%输出 2为0.01%输出
        self.INFO = INFO                                  # 是否显示进度条信息
        self.speed_list = []                              # 速度列表
        if fp:
            self.fp = fp                                  # 文件对象

    def callback_html(self, block):
        """
        :param block: 上传或下载的数据块
        """
        if self.fp:
            self.fp.write(block)
        self.sizeWritten += len(block)
        percents = '\033[32;1m%s\033[0m' % round(float(self.sizeWritten) * 100 / float(self.totalSize), self.change_percent)
        filled = int(self.__bar_length * self.sizeWritten / float(self.totalSize))
        bar = '\033[32;1m%s\033[0m' % '=' * filled + '-' * (self.__bar_length - filled)
        speed = self.sizeWritten / (np.float64(time.time()) - self.time_start)
        self.speed_list.append(speed)

        percentComplete = round((self.sizeWritten / self.totalSize) * 100, self.change_percent)  # 粗分辨率,防止刷新过快
        if self.__lastShownPercent != percentComplete:
            self.__lastShownPercent = percentComplete
            if self.INFO:
                ddt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print('\r'+f'{ddt} ---> [{bar}] {percents}% speed:{translate_byte(speed)}/s, already complete: {translate_byte(self.sizeWritten)}, total: {translate_byte(self.totalSize)}', end='')
        if speed < self.lowSpeed_floor:
            self.lowSpeed_num += 1
            if self.lowSpeed_num >= self.lowSpeed_exit_num and percentComplete <= 85:
                raise LowSpeed_Error(speed)

    def callback_ftp(self):
        """
        :return: 返回一个函数对象
        """
        return self.callback_html
