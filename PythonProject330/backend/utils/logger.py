# 日志切割，生产级日志，不会无限变大，自动按天切割
# 日志：后端运行过程中记录的消息（比如报错、调试信息、关键操作记录。）
import logging
from logging.handlers import TimedRotatingFileHandler
import os

def init_logger(app):
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # 日志按天切割，保留 30 天
    # 创建日志处理器
    file_handler = TimedRotatingFileHandler( # 定时切割日志文件的处理器：TimedRotatingFileHandler
        "logs/app.log", # 日志文件的路径
        when="midnight", # 每天午夜切割一个新日志。若按小时切换，则when="H"
        backupCount=30, # 最多保留30个旧日志文件
        encoding="utf-8" # 文件编码
    )

    # 设置日志格式
    file_handler.setFormatter(logging.Formatter(
        # 时间、日志等级（INFO\ERROR\WARNING...）、日志发生的模块、函数名和行号以及日志内容
        "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    ))
    # 配置logger
    # 把日志处理器绑定到Flask，addHander把日志处理器加到Flask自带的logger上
    app.logger.addHandler(file_handler)
    # 设置日志等级（INFO及以上都会记录，常见等级：DEBUG调试信息、INFO普通运行信息、WARNING警告、ERROR错误、CRITICAL严重错误）
    app.logger.setLevel(logging.INFO)