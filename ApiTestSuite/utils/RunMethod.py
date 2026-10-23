# -*- coding: utf-8 -*-
import requests
import json as complexjson
from utils.Logger import logger
from config.BasicData import basic_data
import datetime
import time
# [FIX] 2026-07-30: 新增 time 模块用于重试延时


class RunMethod():
    '''
    :func: 请求方法的封装
    :author: css
    :time: 2021/7/10
    '''

    def __init__(self):
        # 使用 Session + trust_env=False 绕过系统代理，解决vpn打开运行报 ProxyError
        self.session = requests.Session()
        self.session.trust_env = False

    def get(self, url, **kwargs):
        return self.request(url, "get", **kwargs)

    def post(self, url, data=None, json=None, verify=False, **kwargs):
        return self.request(url, "post", data, json, verify, **kwargs)

    def put(self, url, data=None, json=None, verify=False, **kwargs):
        return self.request(url, "put", data, json, verify, **kwargs)

    def delete(self, url, data=None, json=None, verify=False, **kwargs):
        return self.request(url, "delete", data, json, verify, **kwargs)

    def patch(self, url, data=None, json=None, verify=False, **kwargs):
        return self.request(url, "patch", data, json, verify, **kwargs)

    def request(self, name, url, method, data_type, data=None, json=None, params=None, **kwargs):
        headers = dict(**kwargs).get("headers")
        files = dict(**kwargs).get("files")
        if data_type == "json":
            json = data
            data = None
        elif data_type == "data":
            data = data
        elif data_type == "params":
            params = data
            data = None
        elif data_type == "files":
            for k, v in data.items():
                data = basic_data.files_path + v
                files = {k: open(data, 'rb')}
                data = None
        self.request_log(name, url, method, data, json, params, headers, files)
        method = method.lower()
        # 添加请求重试机制（遇到网络异常/5xx 时最多重试 3 次）和超时控制（默认 30 秒）
        max_retries = 3
        retry_delay = 2  # 重试间隔（秒）
        last_exception = None
        timeout = dict(**kwargs).get("timeout", 30)
        for attempt in range(1, max_retries + 1):
            try:
                if method == "get":
                    res = self.session.get(url, params=params, timeout=timeout, **kwargs)
                    return res
                if method == "post":
                    res = self.session.post(url=url, data=data, json=json, files=files, timeout=timeout, **kwargs)
                    return res
                if method == "put":
                    res = self.session.put(url, json=json, data=data, timeout=timeout, **kwargs)
                    return res
                if method == "delete":
                    res = self.session.delete(url, data=data, json=json, timeout=timeout, **kwargs)
                    return res
                if method == "patch":
                    if json:
                        data = complexjson.dumps(json)
                    res = self.session.patch(url, data=data, json=json, timeout=timeout, **kwargs)
                    return res
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                last_exception = e
                logger.warning("接口请求异常（第{}次/共{}次）：{} ==>> {}".format(attempt, max_retries, name, str(e)))
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue
            except requests.exceptions.RequestException as e:
                # 非网络类异常不重试，直接抛出
                logger.error("接口请求致命错误：{} ==>> {}".format(name, str(e)))
                raise

        # 所有重试都失败
        logger.error("接口请求重试{}次后仍然失败：{} ==>> {}".format(max_retries, name, str(last_exception)))
        raise last_exception

    def request_log(self, name, url, method, data=None, json=None, params=None, headers=None, files=None):
        logger.info("接口请求名称 ==>> {}".format(name))
        logger.info("接口请求地址 ==>> {}".format(url))
        logger.info("接口请求方式 ==>> {}".format(method))
        # 处理 None 值，避免 json.dumps(None) 输出 "null" 影响日志可读性
        logger.info("接口请求头 ==>> {}".format(
            complexjson.dumps(headers, indent=4, ensure_ascii=False) if headers else "无"))
        logger.info("接口请求 params 参数 ==>> {}".format(
            complexjson.dumps(params, indent=4, ensure_ascii=False) if params else "无"))
        try:
            logger.info("接口请求体 data 参数 ==>> {}".format(
                complexjson.dumps(data, indent=4, ensure_ascii=False) if data else "无"))
        except:
            logger.info("接口请求体 data 参数 ==>> {}".format(data))
        logger.info("接口请求体 json 参数 ==>> {}".format(
            complexjson.dumps(json, indent=4, ensure_ascii=False) if json else "无"))
        logger.info("接口上传附件 files 参数 ==>> {}".format(files if files else "无"))
        logger.info("接口请求时间 ==>> {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

