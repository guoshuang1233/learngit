import json
from urllib.parse import urlparse
from collections import defaultdict

pathfile = r"C:\Users\Administrator\Desktop\\"   # .har处理和生成文件的路径
httpfile = pathfile + r'xms-test.noviland.com.har'   # 要处理的.har文件的路径
filename = "testcase"   #要生成的文件名，对应json和yaml文件名称
spl = "noviland.com/"  # 生成的teastcase中url的前缀分隔符号


def safe_parse_json(text):
    """尝试解析 JSON，失败则返回原始字符串"""
    if not text:
        return None
    try:
        return json.loads(text)
    except:
        return text  # 非 JSON 格式（如 plain text）保留原样


def extract_last_segment(url):
    """返回 URL 路径的最后一段，不含查询参数"""
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    return path.split('/')[-1] if path else ''


#

def deal_http_data():
    with open(httpfile, 'r', encoding='utf-8') as f:
        har = json.load(f)

    result = []
    for e in har['log']['entries']:
        req = e['request']
        res = e['response']

        # 提取请求体（可能是 JSON 或表单等）
        raw_data = None
        if 'postData' in req:
            raw_data = req['postData'].get('text')
            # 如果 content-type 是 application/json，则解析
            # 也可强制解析，失败则保留原字符串
        parsed_data = safe_parse_json(raw_data)

        # 提取响应体
        raw_res = res.get('content', {}).get('text', '')
        parsed_res = safe_parse_json(raw_res)

        result.append({
            "url": req['url'],
            "method": req['method'],
            "data": parsed_data,  # 现在是 dict 或 None 或原字符串
            "status": res['status'],
            "res": parsed_res  # 现在是 dict 或 None 或原字符串
        })

    with open(pathfile + 'extracted_requests.json', 'w', encoding='utf-8') as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
    print(f"已提取 {len(result)} 条记录，保存到 extracted_requests.json")


def product_yaml_file():
    # 读取提取的 JSON 数据
    with open(pathfile + 'extracted_requests.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    yaml_lines = []
    counter = {}

    for item in items:
        url = item['url']
        method = item['method']
        data = item.get('data')  # 可能为 None 或 dict

        # 只处理包含 "app/order/" 的 URL（跳过 S3 等）
        if spl not in url:
            continue

        # 解析路径，去掉查询参数
        parsed = urlparse(url)
        path = parsed.path

        # 提取 "app/order/" 之后的部分
        if spl in path:
            after = path.split(spl, 1)[1]
        else:
            after = path  # 备用

        # 最后一段作为 case_name 和 request_data 的后半部分
        base_segment = path.rstrip('/').split('/')[-1]

        # 处理重复名称
        if base_segment in counter:
            counter[base_segment] += 1
            unique_segment = f"{base_segment}_{counter[base_segment]}"
        else:
            counter[base_segment] = 0
            unique_segment = base_segment

        # ---- 根据是否有请求体决定 data_method 和 request_data ----
        has_data = data is not None and data != {}  # 非空字典才认为有请求体
        if has_data:
            data_method = 'json' if method == 'POST' else ('params' if method == 'GET' else '')
            req_data = f'%s:{unique_segment}' % filename
        else:
            data_method = ''
            req_data = ''
        # ---------------------------------------------------------

        # 构建 entry
        entry = {
            'case_name': unique_segment,
            'url_prefix': 'base_url',
            'url': after,
            'method': method,
            'data_method': data_method,
            'is_header': "'&{SuperAdmin_token}'",
            'deal_data': '',
            'request_data': req_data,
            'pro_env': '',
            'sql': '',
            'validate': [{'contains': ['res', 'success']}],
            'output': ''
        }

        # 转换为 YAML 格式（手动构建缩进）
        yaml_lines.append('- case_name: ' + entry['case_name'])
        yaml_lines.append('  url_prefix: ' + entry['url_prefix'])
        yaml_lines.append('  url: ' + entry['url'])
        yaml_lines.append('  method: ' + entry['method'])
        yaml_lines.append('  data_method: ' + entry['data_method'])
        yaml_lines.append('  is_header: ' + entry['is_header'])
        yaml_lines.append('  deal_data: ' + entry['deal_data'])
        yaml_lines.append('  request_data: ' + entry['request_data'])
        yaml_lines.append('  pro_env: ' + entry['pro_env'])
        yaml_lines.append('  sql: ' + entry['sql'])
        yaml_lines.append('  validate:')
        for cond in entry['validate']:
            yaml_lines.append('   - contains: ' + str(cond['contains']))
        yaml_lines.append('  output: ' + entry['output'])
        yaml_lines.append('')  # 空行分隔

    # 写入文件
    with open(pathfile + filename + '.yaml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(yaml_lines))

    total = len([l for l in yaml_lines if l.startswith('- case_name:')])
    print(f"YAML 文件已生成，共 {total} 条记录。")


def product_json_file():
    # 读取提取好的 JSON 数据
    with open(pathfile + 'extracted_requests.json', 'r', encoding='utf-8') as f:
        entries = json.load(f)

    result = {}
    count_map = defaultdict(int)  # 统计每个基础 key 实际出现的次数（仅非空 data）

    for item in entries:
        url = item['url']
        data = item.get('data')  # 可能为 None 或 dict

        # ---- 新增：如果 data 为空，则跳过该条目 ----
        if data is None or data == {}:
            continue
        # ----------------------------------------

        # 只处理包含 app/order/ 的请求（可根据需要修改）
        if spl not in url:
            continue

        key = extract_last_segment(url)
        if not key:
            continue

        base_key = str(key)
        # 如果该 key 尚未存在，则直接添加
        if base_key not in result:
            result[base_key] = {
                "TC": base_key,
                "testData": data
            }
            # 首次出现时，计数器保持为 0（但 defaultdict 会自动初始化）
        else:
            # 已存在，生成带后缀的新 key
            count_map[base_key] += 1
            new_key = f"{base_key}_{count_map[base_key]}"
            result[new_key] = {
                "TC": new_key,
                "testData": data
            }

    # 输出到文件
    output_file = pathfile + filename + '.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"成功生成 {len(result)} 条记录，保存至 {output_file}")


if __name__ == "__main__":
    deal_http_data()
    product_yaml_file()
    product_json_file()
