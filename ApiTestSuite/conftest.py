# -*- coding: utf-8 -*-
"""
[FIX] 2026-07-30: pytest conftest.py
将全局状态初始化（GlobalVar._init）和测试数据加载通过 pytest_generate_tests 钩子实现，
解决原先模块导入时即加载数据的问题，支持动态筛选用例和并行执行（pytest-xdist）。
"""
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# [FIX] 2026-07-30: 使用 pytest_generate_tests 替代模块级固定数据加载，
# 每次 test_main 被调用前动态读取 YAML/JSON 测试用例并注入参数
def pytest_generate_tests(metafunc):
    """动态生成测试用例参数，替代 TestcaseRun 中模块级的 testdata 硬加载
    同时从 YAML 的 markers 字段读取标签，转为 pytest mark 实现 -m 筛选"""
    if "file" in metafunc.fixturenames and "case_name" in metafunc.fixturenames:
        from utils.GlobalVar import gl
        gl._init()
        from utils.DataLoader import prepare_data
        testdata = prepare_data.get_prepare_data()

        # 将 markers 转为 pytest.param 的 marks，支持 pytest -m 筛选
        params = []
        for item in testdata:
            # item: [file, case_name, url, method, is_header, deal_data,
            #        request_data, data_method, sql, validate, output, markers]
            *test_params, markers = item
            import re
            mark_list = []
            if markers:
                for m in markers:
                    if not m:
                        continue
                    # 带参数标记：order(1) → pytest.mark.order(1)
                    m_obj = re.match(r'(\w+)\((\d+)\)', m)
                    if m_obj:
                        name = m_obj.group(1)
                        idx = int(m_obj.group(2))
                        mark_list.append(getattr(pytest.mark, name)(idx))
                    else:
                        mark_list.append(getattr(pytest.mark, m))
            params.append(pytest.param(*test_params, marks=mark_list))

        metafunc.parametrize(
            'file,case_name,url,method,is_header,deal_data,request_data,data_method,sql,validate,output',
            params
        )


def pytest_collection_finish(session):
    """在 pytest 收集 + 筛选完成后（-m/-k 之后），输出本次实际执行的用例数"""
    import logging
    logger = logging.getLogger("log")
    logger.info("本次执行用例数 ==>> {}".format(len(session.items)))


@pytest.fixture(scope="session")
def global_var_init():
    """会话级别的全局变量初始化 fixture（向后兼容）"""
    from utils.GlobalVar import gl
    gl._init()
    return gl


# [FIX] 2026-07-30: 注册 pytest 自定义 marker，支持按模块/优先级筛选执行
# 使用方式示例：
#   pytest -m "smoke"           # 只跑冒烟测试
#   pytest -m "pms"             # 只跑 PMS 模块
#   pytest -m "not slow"        # 排除慢速用例
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "login: 登录模块测试用例"
    )
    config.addinivalue_line(
        "markers", "pms: PMS产品管理系统测试用例"
    )
    config.addinivalue_line(
        "markers", "wms: WMS仓库管理系统测试用例"
    )
    config.addinivalue_line(
        "markers", "oms: OMS订单管理系统测试用例"
    )
    config.addinivalue_line(
        "markers", "tms: TMS运输管理系统测试用例"
    )
    config.addinivalue_line(
        "markers", "cms: CMS渠道管理系统测试用例"
    )
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试用例"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试用例"
    )
    config.addinivalue_line(
        "markers", "login: 登录系统测试用例"
    )
