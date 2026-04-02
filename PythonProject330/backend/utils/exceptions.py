# 自定义异常，不管代码报错、参数错误、数据库错误，全部返回JSON，不崩溃

class ApiException(Exception):
    """自定义接口异常"""
    def __init__(self, msg="接口异常", code=400):
        self.msg = msg
        self.code = code
        super().__init__(self.msg)