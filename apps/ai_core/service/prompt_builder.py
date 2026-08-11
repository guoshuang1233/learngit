import json, re

SYSTEM_PROMPT_WRITER = '你是资深测试架构师。阅读需求文档后,从真实功能角度(页面/弹窗/操作流程/数据表)拆出测试模块,为每个模块设计具体可执行的测试用例。模块名绝对不能使用文档章节标题。只输出JSON,field名必须是rows。'

class PromptBuilder:
    @staticmethod
    def _clean_markdown(text):
        text = re.sub(r'\|[-\s:|=|]+\|', '', text)
        text = re.sub(r'\n\s*\|', '\n', text)
        text = re.sub(r'\|\s*\n', '\n', text)
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'\n-{3,}\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def build_test_design_prompt(*, title, requirement_text, rule_text=''):
        doc_text = PromptBuilder._clean_markdown(requirement_text)[:12000]
        row_schema = {
            'case_no': 'TC-FUNC-001', 'module_name': '用户资产列表',
            'suite_name': '用户资产列表 Test Suite', 'scenario': '具体测试场景',
            'description': '', 'related_tables': 'user_assets', 'related_fields': 'user_assets.type',
            'preconditions': '已登录', 'steps': '1.xxx\n2.xxx',
            'expected_result': '1.xxx\n2.xxx', 'priority': 'P0', 'case_type': '功能测试',
        }
        return '\n'.join([
            '你是资深测试架构师。阅读需求文档,从真实功能角度(页面/弹窗/流程/数据表)拆测试模块,生成用例。',
            '模块名=功能名。禁止:文档标题、版本号、编号。如有数据库表,单独拆XXX表-字段值校验模块。',
            '每个模块覆盖:加载 筛选 创建 校验 权限 异常。scenario=具体场景。steps=每步一个动作。expected_result=可验证检查点。',
            '只输出JSON,field名=rows:',
            json.dumps({'title':title,'summary':'','rows':[row_schema]},ensure_ascii=False,indent=2),
            f'需求标题:{title}\n规则:{rule_text or "无"}\n正文:\n{doc_text}',
        ])

    @staticmethod
    def build_script_generation_prompt(*, suite_name, suite_text, api_text, rule_text='', testcase_list=None):
        return '\n'.join([
            '根据测试用例和接口文档生成pytest脚本。要求:pytest+requests,独立test_xxx(),状态码+响应体断言,异常单独处理。只输出JSON。',
            f'测试集:{suite_name}\n用例:{suite_text}\n接口:{api_text}',
            json.dumps({'suite_name':suite_name,'script_content':'# pytest','testcases':[]},ensure_ascii=False,indent=2),
        ])
