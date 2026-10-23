# -*- coding: utf-8 -*-
import sys
from config.BasicData import basic_data
import logging

class GlobalVar():
    '''
    :func: 处理全局变量
    :author: css
    :time: 2021/7/10
    '''
    def _init(self):
        global _global_dict
        _global_dict = {}
        if len(sys.argv) > 1:
            env = sys.argv[1]
            self.setattr("env", sys.argv[1])
        else:
            env = "test"
            self.setattr("env", "test")
        setting_data = basic_data.get_env_url(env)
        for k, v in setting_data.items():
            self.setattr(k, v)

    def setattr(self, name, value):
        _global_dict[name] = value

    def getattr(self, name):
        try:
            return _global_dict[name]
        except KeyError:
            logging.getLogger("log").warning("GlobalVar 全局变量 '{}' 未找到，返回空字符串".format(name))
            return ""


gl = GlobalVar()
