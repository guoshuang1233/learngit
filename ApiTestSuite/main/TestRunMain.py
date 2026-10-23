# -*- coding: utf-8 -*-
import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # 支持从命令行传入环境参数（如 python TestRunMain.py test）、
    # pytest marker 筛选（如 -m "smoke"）、并行执行（如 -n 4）
    # 使用示例：
    #   python main/TestRunMain.py test                    # 测试环境
    #   python main/TestRunMain.py pro                     # 线上环境
    #   python main/TestRunMain.py test -m "pms"           # 只跑 PMS 模块
    #   python main/TestRunMain.py test -n 4               # 4 线程并行执行
    #   python main/TestRunMain.py test -m "login or pms or oms or wms or cms or tms"

    from config.BasicData import basic_data

    # 使用绝对路径，避免 PyCharm / 终端不同工作目录导致找不到文件
    testcase_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 'utils', 'TestcaseRun.py')

    args = [
        '-s', '-q',
        '--clean-alluredir',
        testcase_path,
        '--alluredir', 'allure-results',
        # [FIX] 2026-07-30: 失败/超时自动重试，参数在 config/BasicData.py 中可修改
        '--reruns', str(basic_data.RETRY_COUNT),
        '--reruns-delay', str(basic_data.RETRY_DELAY),
        '--timeout', str(basic_data.CASE_TIMEOUT),
    ]

    # 传递额外的 pytest 参数（如 -m 标记筛选、-n 并行数）
    # 命令行传入的第2个及之后的参数会追加给 pytest
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []
    args.extend(extra_args)
    pytest.main(args)
    os.system("allure serve allure-results")
