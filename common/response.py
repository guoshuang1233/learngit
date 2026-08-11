from rest_framework.response import Response

class ApiResponse:
    @staticmethod
    def success(data=None, msg="成功", status=200):
        return Response({"code": 0, "msg": msg, "data": data}, status=status)

    @staticmethod
    def fail(msg="失败", code=-1, status=400):
        return Response({"code": code, "msg": msg, "data": None}, status=status)

    @staticmethod
    def error(msg="服务器错误", code=500, status=500):
        return Response({"code": code, "msg": msg, "data": None}, status=status)
