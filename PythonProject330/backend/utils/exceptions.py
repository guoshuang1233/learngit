
class ApiException(Exception):
    """自定义接口异常"""
    def __init__(self, msg="接口异常", code=400):
        self.msg = msg
        self.code = code
        super().__init__(self.msg)