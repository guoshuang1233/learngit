# -*- coding: utf-8 -*-
import os


class BasicInfo:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # 使用 os.path.join 替代硬编码反斜杠，兼容 Linux/Mac
    testcase_yaml = os.path.join(BASE_PATH, "testcase", "*", "*.yaml")
    json_path = os.path.join(BASE_PATH, "testcase", "*")  # 关键字管理测试请求数据
    files_path = os.path.join(BASE_PATH, "testcase", "2File") + os.sep  # 依赖文件路径

    # 定义日志文件路径
    LOG_PATH = os.path.join(BASE_PATH, "log")
    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    # 失败/超时重试配置，解决环境卡顿导致用例偶发失败问题
    RETRY_COUNT = 2  # 失败后最多重试次数（总共执行 1 + 2 = 3 次）
    RETRY_DELAY = 30  # 重试前等待秒数
    CASE_TIMEOUT = 120  # 单个用例超时秒数（2分钟），超时后触发重试



    def get_env_url(self, run_env):
        if run_env == "test":
            # 测试环境
            # 敏感信息（数据库连接、密码等）优先从环境变量读取，无环境变量时使用默认值
            return {
                "base_url": "https://xms-test.noviland.com/",
                "s3_url": "https://&{bucket}.s3.&{region}.amazonaws.com/",
                "secret_key": os.environ.get("secret_key", ""),
                "access_key": os.environ.get("access_key", ""),
                # SuperAdmin账户
                "SuperAdmin_name":  "superadmin",
                "SuperAdmin_pwd":  os.environ.get("SuperAdmin_pwd", ""),
                # 数据库连接信息从环境变量读取，避免硬编码在代码中
                "host": os.environ.get("XMS_DB_HOST", ""),
                "user": os.environ.get("XMS_DB_USER", ""),
                "password": os.environ.get("XMS_DB_PASSWORD", ""),
                "db": os.environ.get("XMS_DB_NAME", ""),
                "port": int(os.environ.get("XMS_DB_PORT", "3306"))
            }
        elif run_env == "pre":
            # 预发环境
            pass
        elif run_env == "pro":
            return {
                    }


basic_data = BasicInfo()
