# -*- coding: utf-8 -*-
import yaml
import os
import glob
from utils.Logger import logger
from config.BasicData import basic_data
import json
from utils.GlobalVar import gl


class OperationPrepareData():
    '''
    :func: 操作yaml文件
    author:css
    time: 2022/5/26
    '''

    def get_file_path(self, file):
        '''
        func: 文件模糊路径
        :return: 返回文件绝对路径
        '''
        file_path = glob.glob(file)
        return file_path

    def read_yaml_file(self, filename):
        '''
        func: 读取单独yaml的文件内容
        :return: yaml的文件内容
        '''
        # [FIX] 2026-07-30: 使用 with 语句确保文件正确关闭，避免文件句柄泄漏
        with open(filename, encoding='utf-8') as f:
            content = yaml.safe_load(f)
        return content

    def get_file_content(self):
        '''
        func：返回testcase的yaml文件
        :return: 返回testcase的yaml文件
        '''
        contents = []
        for file in self.get_file_path(basic_data.testcase_yaml):
            content = self.read_yaml_file(file)
            contents.append((file, content))
        return contents

    def get_prepare_url(self, prefix):
        '''
        func：返回请求url地址
        :return: 返回请求url地址
        '''
        return basic_data.get_env_url(gl.getattr("env"))[prefix]

    def read_json_data(self, file_path):
        '''
        :func: 读取json文件内容
        :return: json内容
        '''
        # [FIX] 2026-07-30: 使用 with 语句确保文件正确关闭
        with open(file_path, "r", encoding='utf-8') as f:
            data = f.read()
            return json.loads(data)

    def get_json_data(self, request_data):
        '''
            func：返回testcase的json依赖数据
            :return: 返回testcase的json依赖数据
        '''
        file_name = request_data.split(":")[0] + ".json"
        data_key = request_data.split(":")[1]
        file_path = os.path.join(basic_data.json_path, file_name)  # 模糊路径
        file_real_path = self.get_file_path(file_path)  # 真实路径
        data = self.read_json_data(file_real_path[0])[data_key]['testData']
        return data

    def get_prepare_data(self):
        '''
        func：返回testcase的yaml用例
        :return: 返回testcase的yaml用例
        '''
        prepare_data_tcs = []
        testcase = self.get_file_content()
        for tc in testcase:
            file = os.path.split(tc[0])[1]
            yaml_tc = tc[1]
            for yaml_tc in yaml_tc:
                request_data = output = None
                case_name = yaml_tc["case_name"]
                tc_name = "文件名：%s-->用例名：%s" % (str(file), str(case_name))
                url_prefix = yaml_tc["url_prefix"]
                url = yaml_tc["url"]
                if url_prefix and url:
                    url = self.get_prepare_url(url_prefix) + yaml_tc['url']
                elif url_prefix:
                    url = self.get_prepare_url(url_prefix)
                elif url:
                    url = yaml_tc['url']
                method = yaml_tc["method"]
                is_header = yaml_tc["is_header"]
                deal_data = yaml_tc["deal_data"]
                is_request_data = yaml_tc['request_data']
                if is_request_data:
                    request_data = self.get_json_data(is_request_data)
                data_method = yaml_tc["data_method"]
                sql = yaml_tc["sql"]
                validate = yaml_tc["validate"]
                if yaml_tc['output']:
                    output = yaml_tc['output']
                markers = yaml_tc.get("markers", [])
                l1 = [file, tc_name, url, method, is_header, deal_data, request_data, data_method, sql, validate,
                      output, markers]
                prepare_data_tcs.append(l1)
        logger.info("运行环境 ==>> {},TC总数 ==>> {}".format(gl.getattr("env"), len(prepare_data_tcs)))
        return prepare_data_tcs


prepare_data = OperationPrepareData()
