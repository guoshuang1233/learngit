# -*- coding: utf-8 -*-
import sys

sys.path.append("../")
from utils.RunMethod import RunMethod
import allure
from utils.Common import CommonUtils

# pytest_generate_tests 钩子conftest.py动态注入，解决导入时即加载数据的问题，支持运行时筛选和并行执行。
run_method = RunMethod()
com_utils = CommonUtils()


class TestcaseRun():
    '''
    :func: 用例运行类
    :author: css
    :time: 2021/7/10
    '''

    @allure.title('{case_name}')
    # 参数由 conftest.py 的 pytest_generate_tests 动态注入，不使用 @pytest.mark.parametrize 装饰器，避免 "duplicate" 冲突
    def test_main(self, file, case_name, url, method, is_header, deal_data, request_data, data_method, sql, validate,
                  output):
        allure.dynamic.story(file.split(".")[0])
        headers = com_utils.get_headers(is_header, request_data)
        url, request_data = com_utils.deal_data(url, deal_data, request_data)
        res = run_method.request(case_name, url, method, data_method, data=request_data, headers=headers)
        if sql:
            com_utils.sql_deal(sql)
        com_utils.deal_res(res.text, validate, output, case_name)

        # 下面2行代码为 fiddler 调试代码
        # fiddler_proxies = {'http': 'http://127.0.0.1:8888', 'https': 'http://127.0.0.1:8888'}
        # res = run_method.request(case_name, url, method, data_method, data=request_data, headers=headers, proxies=fiddler_proxies)
