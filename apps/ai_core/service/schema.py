def build_default_testcase():
    return {"case_no":"","module_name":"","suite_name":"","scenario":"","description":"",
            "related_tables":"","related_fields":"","preconditions":"","steps":"",
            "expected_result":"","priority":"","case_type":""}
def build_default_module():
    return {"name":"","description":"","suite_name":"","testcases":[]}
def build_default_design_result():
    return {"title":"","rule_text":"","summary":"","rows":[],"modules":[]}
def build_default_script_result():
    return {"suite_name":"","rule_text":"","script_content":"","testcases":[]}
