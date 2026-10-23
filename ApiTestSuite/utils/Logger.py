# -*- coding: utf-8 -*-
import logging, time, os
from config.BasicData import basic_data


class Logger():
    '''
    :func: 日志封装
    :author: css
    :time: 2021/7/10
    '''

    def __init__(self):
        self.logname = os.path.join(basic_data.LOG_PATH, "{}.log".format(time.strftime("%Y%m%d")))
        self.logger = logging.getLogger("log")
        self.logger.setLevel(logging.DEBUG)

        # 避免重复初始化导致 handler 累积，每次创建前检查是否已有 handler
        if self.logger.handlers:
            return

        self.formater = logging.Formatter(
            '[%(asctime)s][%(filename)s %(lineno)d][%(levelname)s]: %(message)s')

        self.filelogger = logging.FileHandler(self.logname, mode='a', encoding="UTF-8")
        self.console = logging.StreamHandler()
        self.console.setLevel(logging.DEBUG)
        self.filelogger.setLevel(logging.DEBUG)
        self.filelogger.setFormatter(self.formater)
        self.console.setFormatter(self.formater)
        self.logger.addHandler(self.filelogger)
        self.logger.addHandler(self.console)


logger = Logger().logger
