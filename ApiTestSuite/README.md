
##文件结构说明：  
    - config: 存放config的配置信息  
    - conftest: 存放pytest的配置信息  
    - log: 存放生成日志, 调试中可删除该文件夹, 会自动生成  
    - report: 存放生成报告文件, 调试中可删除该文件夹, 会自动生成  
    - utils: 封装的工具类  
    - main: 框架运行的主入口 
    - tools: 存放处理http数据的小工具，直接运行生产json和yaml文件 
    - requirement.txt: 框架依赖的python库
      安装依赖：pip install -r requirement.txt    
##yaml样例说明：    

  - *case_name :*  &ensp; 用例名称 
  - *markers: &ensp; [login, smoke]*    &ensp; 执行用例打表记
  - *url_prefix :* &ensp; 执行url前缀      
  - *url :* &ensp; url后缀  &ensp;  
  - *method :* &ensp; 请求方式  &ensp; eg: get、post、put、delete、option   
  - *is_header :* &ensp; 请求头信息，&ensp; eg：'header.Authorization=&{Admin_token}'  or   apiheaders        
  - *request_data :* &ensp; json文件名:key &ensp;   
  - *data_method :* &ensp; 参数请求类型 &ensp; eg：params、json、data    
  - *deal_data :* &ensp; 是否处理入参，常见导入数据重复，入参值依赖上一个接口 &ensp; eg：True    
  - *sql :* &ensp; 赋值变量：要查询的sql &ensp; eg：True 辅助结果判断
  - *validate :* &ensp; 断言 &ensp; 支持等于equals和包含 contains
  - *output :* &ensp; 输出：   
    全局变量key：response解析 &ensp; eg：id: records.[0].id    

---
  ### 扩展：  
  **markers写法：**  
  &ensp;&ensp;给用例打标，执行时可以用标记来完成哪些用例执行哪些不执行
   - markers: [login, smoke]&ensp;&ensp; 同时打 login 和 smoke  
   - markers: [pms]&ensp;&ensp;只打 pms标记  
   - 不写 &ensp; &ensp;&ensp;不打标记 — 始终运行（除非用 -m "not ..." 排除）

  **is_header写法：**   
    'header.Authorization=&{Admin_token}'      
    含义： 取值配置文件的header,然后赋值      
    apiheader     
    含义： 直接取配置文件的值     
    
  **output写法：**   
  - id: records.[0].id  &ensp; 含义：获取response里面的records的第0个元素的id的值，赋值给全局变量id   
    使用： &{id} 
  - id: records.[*].id  &ensp; 含义：获取response里面的records的所有元素的id的值，赋值给全局变量id    
    使用：&{id.0}  &ensp;  &{id.1}  
  - 穿透取值，没有办法确定返回的数据值，比如，cms的getChannelInfo接口，可以采用这种办法写  
  - wayfair_code_id: "data -> name=Wayfair -> vcAccounts -> code=Wayfair-Nvl -> id"  
    含义：找到data数据里，name=Wayfair的那组数据下面的vcAccounts里面的code=Wayfair-Nvl对应的id值
    
  **validate写法：**   
  validate:    
  &ensp;&ensp;  - equals: [data.permissions."order/supplier-vendor",all] &ensp;  
  &ensp;&ensp;    - equals: ['&{sql_result}','&{total}'] &ensp;  
  &ensp;&ensp;    - contains: [200, data."code"] &ensp;    
  &ensp;&ensp;    - contains: [res, success] &ensp;    

  &ensp;&ensp;       第1种写法含义：获取response["data"]["permissions"]["order/supplier-vendor""]的值和all值做相等比较   
  &ensp;&ensp;       第2种写法含义：获取变量sql_result和total的值，做相等比较      
  &ensp;&ensp;       第3种写法含义：判断200再response["data"]["code"] 里面      
  &ensp;&ensp;       第4种写法含义：判断"success"再response里面      
        
  &ensp;      *注意*：&ensp;&ensp;如果需要从response获取数据，需要用.书写
    
### 目录结构
├─README.md   
├─requirements.txt    
├─config    
│  └─BasicData.py    
├─conftest.py  
├─log    
├─tools  
│  └─tiquhttp.py  
├─main    
│  └─TestRunMain.py   
├─report   
├─testcase   
│  ├─1登录模块   
│  │  └─login.json    
│  │  └─login.yaml   
│  ├─2File   
│  │  └─存放excel和图片文件    
│  └─TC场景       
│  │  └─正常流程.json     
│  │  └─正常流程.yaml     
├─utils    
│  ├─CommonUtils.py   
│  ├─GlobalVar.py    
│  ├─Logger.py    
│  ├─OperationPrepareData.py    
│  ├─RunMethod.py    
│  ├─SpecialMethods.py    
│  ├─TestcaseRun.py    
