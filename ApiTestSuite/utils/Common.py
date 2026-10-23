# -*- coding: utf-8 -*-
import json
import hashlib
import hmac
import os
import csv
import openpyxl
import random
import urllib.parse
import datetime
from utils.Logger import logger
from utils.CustomHandlers import SpecialMethods
import pymysql
from utils.GlobalVar import gl
from jsonpath_rw import parse
import re
from config.BasicData import basic_data

special_methods = SpecialMethods()


class CommonUtils():
    '''
    :func: 存放共用的处理方法
    :author: css
    :time: 2021/7/10
    '''

    def deal_parepare_data(self, data):
        '''
        :func 处理data，替换变量值&{}
        :param data: 要处理的数据
        :return: 处理后的数据
        '''
        if data.find('&{') >= 0:
            pattern = r'&{(.*?)}'
            result = re.findall(pattern, data)
            for i in result:
                key = i.split(".")
                if len(key) == 1:
                    replace_data = gl.getattr(key[0])
                else:
                    # 支持嵌套变量路径，如 &{var.0.field.subfield}
                    replace_data = gl.getattr(key[0])
                    for k in key[1:]:
                        try:
                            idx = int(k)
                            replace_data = replace_data[idx]
                        except (ValueError, TypeError):
                            # k 不是数字，按字典 key 访问
                            replace_data = replace_data[k]
                data = data.replace("&{%s}" % i, str(replace_data))
        return data

    def deal_validate(self, validate, res):
        '''
        :func 处理断言,等于和包含2种校验
        :param validate: 验证的原数据
        :param res: 接口返回的响应内容
        :return:
        '''

        for data in validate:
            # 替换验证数据里面的变量值，转换成dict，进行校验数据对比
            if "&{" in str(data):
                # 解决 json loads转义字符报错问题，将 replace('\'', '\"') 转换方式改成 eval 安全地将 Python dict 字符串转为 dict（数据来源可控）
                data_str = self.deal_parepare_data(str(data))
                try:
                    # 优先尝试 JSON 解析（标准双引号格式）
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    try:
                        # 兼容单引号 Python dict 格式
                        data = eval(data_str)
                    except Exception as e:
                        logger.error("CommonUtils - deal_validate 断言数据解析失败：{} ==>> {}".format(data_str, str(e)))
                        raise
            for k, v in data.items():
                if "." in v[0]:
                    l_result = self.jiexi_data(v[0], res)[0]  # 根据路径从res中提取到数据
                elif v[0] == "res":
                    l_result = res
                else:
                    l_result = v[0]
                if k == "equals":
                    self.equals(l_result, v[1])
                if k == "contains":
                    self.contains(l_result, v[1])

    def equals(self, check_value, expect_value):
        '''
        :func 处理断言,等于校验
        :param check_value: 测试值
        :param expect_value: 预期值
        '''
        logger.info(
            "校验结果：{}, 测试结果为 ==>> {},预期结果为：{}".format(check_value == expect_value, check_value, str(expect_value)))
        assert check_value == expect_value

    def contains(self, check_value, expect_value):
        '''
        :func 处理断言,包含校验
        :param check_value: 测试值
        :param expect_value: 预期值
        '''
        logger.info(
            "校验结果：{}, 测试结果为 ==>> {},预期结果为：{}".format(str(expect_value) in str(check_value), check_value,
                                                           str(expect_value)))
        assert str(expect_value) in str(check_value)

    def get_headers(self, is_header, request_data=None):
        '''
        :func 是否有header，处理header值，支持四种格式：
            1. _s3_headers →  自动构建 S3 签名头（需配合 request_data 中的 _s3_* 字段）
               例: '_s3_headers' + request_data{"_s3_local_path": "D:/a.xlsx", "_s3_key_prefix": "pms"}
            2. key=value   →  {"key": resolved_value}，value 可含 &{var} 变量
               例: 'Authorization=&{SuperAdmin_token}' → {"Authorization": "Bearer xxx"}
            3. &{var} 简写 →  {"Authorization": resolved_value}
               例: '&{SuperAdmin_token}' → {"Authorization": "Bearer xxx"}
            4. 全局变量名  →  直接从 gl 取值（dict 或字符串）
               例: 'apiheaders' → {"auth": "superadmin"}
            5. 空/None     →  {}
        :param is_header: 是否有header
        :param request_data: 请求数据（S3 模式时需包含 _s3_local_path 等字段）
        :return: header dict
        '''
        # 空/None → 直接返回
        if not is_header:
            return {}

        # 格式1: key=value（如 'Authorization=&{token}' 或 'X-Header=plain-value'）
        if '=' in is_header:
            key, value = is_header.split('=', 1)
            key = key.strip()
            if '&{' in value:
                value = self.deal_parepare_data(value)
            return {key: value}

        # 格式2: &{var} 简写，默认 header key 为 Authorization
        if '&{' in is_header:
            value = self.deal_parepare_data(is_header)
            return {"Authorization": value}

        # 格式3: S3 上传 header（_s3_headers）
        if '_s3_headers' in is_header:
            return self.build_s3_headers(request_data or {})

        # 格式4: 全局变量名（如 SuperAdmin_apiheader），直接取值
        return gl.getattr(is_header)

    def deal_data(self, url, deal_data, request_data):
        '''
        :func 处理data，包括url，请求data
        :param url:
        :param deal_data:
        :param request_data:
        :return: url, request_data
        '''
        url = self.deal_parepare_data(url)
        try:
            request_data = json.loads(self.deal_parepare_data(json.dumps(request_data)))
        except:
            # S3 上传模式：request_data 是文件 bytes，跳过 JSON 处理
            request_data = self.deal_parepare_data(json.dumps(request_data))
        if deal_data:  # 特殊方法处理数据（兼容旧版 deal_data: true）
            url, request_data = special_methods.deal_data(url, request_data)
        request_data = self.convert_ids(request_data)
        return url, request_data

    def mysql_connect(self):
        '''
        :func:连接数据库
        :return:
        '''
        host = gl.getattr("host")
        user = gl.getattr("user")
        password = gl.getattr("password")
        db = gl.getattr("db")
        port = gl.getattr("port")
        cur = pymysql.connect(host=host, user=user, password=password, port=port, db=db)
        cursor = cur.cursor()
        return cursor, cur

    def sql_deal(self, sql):
        '''
        :func: sql查询
        :param sql:  sql语句，目前支持1句
        :return: 查询结果
        '''
        if "&{" in json.dumps(sql):
            sql = self.deal_parepare_data(json.dumps(sql))
            sql = json.loads(sql)
            logger.info(
                "查询sql：{}".format(sql))
        cursor, cur = self.mysql_connect()
        for k in sql:
            cursor.execute(sql[k])
            sql_data = cursor.fetchone()
            gl.setattr(k, sql_data[0])
            logger.info("sql语句：{}执行结果 ==>> {}".format(sql[k], str(sql_data[0])))
        cursor.close()

    def deal_output(self, res, output):
        for k, v in output.items():
            if v == "res":
                gl.setattr(k, res[1:-1])
            elif isinstance(v, str) and '->' in v:
                # 条件查找：data.channels -> name=Wayfair -> id
                result = self._find_by_path(res, v)
                gl.setattr(k, result)
                logger.info("全局参数key：{}，value：{}".format(k, result))
            else:
                l_result = self.jiexi_data(v, res)
                if '*' in v:
                    gl.setattr(k, l_result)
                    logger.info("全局参数key：{}，value：{}".format(k, l_result))
                else:
                    gl.setattr(k, l_result[0])
                    logger.info("全局参数key：{}，value：{}".format(k, l_result[0]))

    def _find_by_path(self, res, path_str):
        """data.channels -> name=Wayfair -> id  在数组中找匹配记录并返回指定字段"""
        parts = [p.strip() for p in path_str.split('->')]
        res_obj = json.loads(res) if isinstance(res, str) else res

        # 第一步：jsonpath 定位数组
        arr = parse(parts[0]).find(res_obj)
        if not arr:
            raise ValueError("_find_by_path: 路径 '{}' 未找到".format(parts[0]))
        items = arr[0].value

        # 第二步：逐段匹配
        for cond in parts[1:-1]:
            if '=' in cond:
                k, val = cond.split('=', 1)
                items = [it for it in items if str(it.get(k.strip())) == val.strip()]
                if not items:
                    raise ValueError("_find_by_path: 条件 '{}' 无匹配".format(cond))
                items = [items[0]]  # 取第一个匹配
            else:
                # 无 = → 取字段值继续（如 vcAccounts、records.[0]）
                val = items[0].get(cond)
                if isinstance(val, list):
                    items = val
                else:
                    items = [{cond: val}]

        # 第三步：取目标字段
        return items[0].get(parts[-1].strip())

    def jiexi_data(self, v, res):
        '''
        :func 解析数据
        :param v: 解析路径
        :param res: 解析原数据
        return: 解析后的数据
        '''
        # 添加 JSON 解析异常处理，接口返回非 JSON（如 HTML 错误页）时给出明确错误提示
        try:
            res_obj = json.loads(res)
        except json.JSONDecodeError as e:
            logger.error("解析内容不是有效的 JSON，解析路径失败：{} ==>> 响应内容：{}".format(v, res[:500]))
            raise
        json_exe = parse(v)
        madle = json_exe.find(res_obj)
        l_result = [math.value for math in madle]
        return l_result

    def deal_res(self, res, validate, output, case_name):
        '''
        :func 处理response数据
        :param res: 接口响应内容
        :param validate: 验证的数据
        :param output: 输出的内容
        :param case_name: 接口名称
        '''
        if res:
            logger.info("预期结果validate ==>> {}".format(validate))
            logger.info("接口请求结果 ==>> {}".format(res))
            if output:
                self.deal_output(res, output)
            if validate:
                self.deal_validate(validate, res)
        else:
            logger.info(
                "response为None，需要手动观察结果：{}执行结果 ==>> {},接口请求结果为,：{}".format(case_name, True, str(res)))

    def convert_ids(self, obj):
        """递归转换字典和列表中的 id 与 orderId 字段（数字字符串 → int）"""
        if isinstance(obj, dict):
            new_obj = {}
            for key, value in obj.items():
                if key in ('id', 'orderId') and isinstance(value, str):
                    try:
                        new_obj[key] = int(value)      # 尝试转换为整数
                    except ValueError:
                        new_obj[key] = value           # 非数字字符串保留原样
                else:
                    new_obj[key] = self.convert_ids(value)  # 递归处理子结构
            return new_obj
        elif isinstance(obj, list):
            return [self.convert_ids(item) for item in obj]
        else:
            return obj

    def build_s3_headers(self, request_data=None):
        '''
        构建s3请求需要的请求头
        :param request_data: 测试数据 dict，可含 bucket/region/key_prefix/file_name（优先使用，gl 兜底）
        '''
        rd = request_data or {}

        # S3 参数优先级：测试数据 JSON > 全局变量 gl（BasicData 初始化）
        bucket = rd.get("bucket") or gl.getattr("bucket")
        key_prefix = rd.get("key_prefix") or gl.getattr("key_prefix")
        region = rd.get("region") or gl.getattr("region")
        file_name = rd.get("file_name") or rd.get("file") or gl.getattr("file_name")
        gl.setattr("bucket",bucket)
        gl.setattr("key_prefix", key_prefix)
        gl.setattr("region", region)
        gl.setattr("file_name", file_name)
        # 密钥只从 gl 取，不放入测试数据（安全考虑）
        access_key = gl.getattr("access_key")
        secret_key = gl.getattr("secret_key")

        # 1. 拼接文件路径：testcase/files/files/ + 文件名
        files_dir = os.path.join(basic_data.BASE_PATH, "testcase", "files", "files")
        file_path = os.path.join(files_dir, file_name)

        # 2. 上传前修改文件内容（如 CSV/XLSX 字段值追加随机数，避免订单号重复）
        change_data = rd.get("change_data")
        if change_data:
            self._modify_upload_file(file_path, change_data)

        # 3. 读取文件内容
        with open(file_path, "rb") as f:
            file_data = f.read()

        # 4. 构造 S3 对象键（路径+文件名）
        file_name = os.path.basename(file_path)
        # 确保 key_prefix 以 / 结尾
        if not key_prefix.endswith("/"):
            key_prefix += "/"
        key = key_prefix + file_name  # 例如：tmp/1.png

        # 3. 构造请求参数
        method = "PUT"
        service = "s3"
        host = f"{bucket}.s3.{region}.amazonaws.com"
        # 对 key 进行 URL 编码（保留斜杠）
        encoded_key = urllib.parse.quote(key, safe="/")

        # 4. 时间戳
        t = datetime.datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        # 5. 计算 payload 哈希
        payload_hash = self._s3_sha256_hex(file_data)

        # 6. 构造规范请求（Canonical Request）
        canonical_uri = "/" + encoded_key
        canonical_querystring = ""
        canonical_headers = (
            f"host:{host}\n"
            f"x-amz-content-sha256:{payload_hash}\n"
            f"x-amz-date:{amz_date}\n"
        )
        signed_headers = "host;x-amz-content-sha256;x-amz-date"

        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        # 7. 构造待签名字符串
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
        canonical_request_hash = self._s3_sha256_hex(canonical_request.encode("utf-8"))
        string_to_sign = (
            f"{algorithm}\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{canonical_request_hash}"
        )

        # 8. 计算签名
        signing_key = self._s3_get_signature_key(secret_key, region, date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # 9. 构造 Authorization 头
        authorization_header = (
            f"{algorithm} Credential={access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        # 10. 构造headers
        headers = {
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
            "Authorization": authorization_header
        }
        return headers

    def _modify_upload_file(self, file_path, change_data):
        """修改上传文件：指定列取前8位+8位随机数。change_data: "Col" 或 ["Col1","Col2"]"""
        columns = [change_data] if isinstance(change_data, str) else change_data
        ext = os.path.splitext(file_path)[1].lower()
        logger.info("修改上传文件: {}, 列={}".format(file_path, columns))
        if ext == ".csv":
            self._modify_csv(file_path, columns)
        elif ext in (".xlsx", ".xlsm"):
            self._modify_xlsx(file_path, columns)

    def _modify_csv(self, file_path, columns):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows, fieldnames = list(reader), reader.fieldnames
        for row in rows:
            for col in columns:
                row[col] = str(row[col])[:8] + str(random.randint(1, 99999999)).zfill(8)
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader(); w.writerows(rows)

    def _modify_xlsx(self, file_path, columns):

        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        head = {str(c.value): c.column for c in ws[1] if c.value}
        for col in columns:
            ci = head[col]
            for r in range(2, ws.max_row + 1):
                cell = ws.cell(row=r, column=ci)
                if cell.value:
                    cell.value = str(cell.value)[:8] + str(random.randint(1, 99999999)).zfill(8)
        wb.save(file_path)
        wb.close()

    def _s3_sign(self, key, msg):
        """HMAC-SHA256 签名"""
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _s3_sha256_hex(self, data):
        """SHA256 哈希"""
        return hashlib.sha256(data).hexdigest()

    def _s3_get_signature_key(self, secret_key, region, date_stamp):
        """生成 AWS V4 签名密钥"""
        k_date = self._s3_sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
        k_region = self._s3_sign(k_date, region)
        k_service = self._s3_sign(k_region, "s3")
        return self._s3_sign(k_service, "aws4_request")
