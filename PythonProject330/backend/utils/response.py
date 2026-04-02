from flask import jsonify

def success_response(data=None, msg="success"):
    """
    统一成功返回格式
    :param data: 返回的数据
    :param msg: 提示信息
    :return: JSON响应
    """
    return jsonify({
        "code": 200,
        "msg": msg,
        "data": data
    })

def error_response(msg="error", code=400):
    """
    统一错误返回格式
    :param msg: 错误提示
    :param code: 错误码
    :return: JSON响应

    """
    return jsonify({
        "code": code,
        "msg": msg,
        "data": None
    })