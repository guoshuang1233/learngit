# -*- coding: utf-8 -*-
import os
import random
import datetime
from utils.Logger import logger
from config.BasicData import basic_data


class SpecialMethods():
    '''
    :func: 存放项目特殊的处理方法（数据处理、S3 上传等）
    :author: css
    :time: 2021/1/10
    '''
    pass

    def deal_data(self, url, test_data):
        '''
        项目特殊性定制化的，请求数据处理
        :func 解决cps重复的提单号和箱号问题 -> 具有特殊性的方法,其它项目可以不用
        :param test_data: 测试数据
        :return: 替换后请求测试数据
        '''
        width = 7
        random_num = random.randint(1, 1000000)
        str_num = str(random_num).zfill(width)
        new_time = datetime.datetime.now().strftime("%Y-%m-%d")
        start_time = "%s 00:00:00" % new_time
        end_time = "%s 23:59:59" % new_time

        # [FIX] 2026-07-30: 字符串切片前加长度检查，避免原始值不足 8 位时崩溃
        if "update-order" in url:
            # 避免orderid和tracking num 重复
            original = test_data["order"]["channelOrderId"]
            if len(original) >= 8:
                test_data["order"]["channelOrderId"] = original[:8] + str_num
            else:
                test_data["order"]["channelOrderId"] = original + str_num
                logger.warning("channelOrderId 原值长度不足8位，直接追加随机数：{}".format(original))

        if "updateProduct" in url:
            sku_original = test_data["sku"]
            if len(sku_original) >= 8:
                test_data["sku"] = sku_original[:8] + str_num
            else:
                test_data["sku"] = sku_original + str_num
            factory_original = test_data["productFactorys"]
            if len(factory_original) >= 12:
                test_data["productFactorys"] = factory_original[:12] + str_num
            else:
                test_data["productFactorys"] = factory_original + str_num

        if "cms/cms/saveStrategy" in url:
            original = test_data["name"]
            if len(original) >= 8:
                test_data["name"] = original[:8] + str_num
            else:
                test_data["name"] = original + str_num

        if "updateRelationShip" in url:
            original = test_data["whCode"]
            if len(original) >= 8:
                test_data["whCode"] = original[:8] + str_num
            else:
                test_data["whCode"] = original + str_num
            test_data["whName"] = test_data["whCode"]

        if "amazonaws.com" in url:
            # 1. 读取文件内容：testcase/files/files/ + 文件名
            files_dir = os.path.join(basic_data.BASE_PATH, "testcase", "files", "files")
            file = test_data["file_name"]
            files = os.path.join(files_dir, file)
            with open(files, "rb") as f:
                test_data = f.read()

        return url, test_data

