# ======================
# 一、固定导包
# ======================
from flask import Blueprint, request, jsonify
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from openai import embeddings

# 一导入的数据库模型
from backend.extensions import db
from backend.models import Goods # 商品表
from backend.models import Order # 订单表
from backend.models import User # 用户表
from backend.utils.jwt_auth import jwt_required

rag_bp = Blueprint('rag', __name__, url_prefix="/api/rag")

# 全局缓存向量库
vector_store = None

# 二、从MySQL读取【商品+订单】数据，到自动生成知识库（这个过程是全自动的，不用管）

def get_knowledge_from_mysql():
    knowledge = ""
    # --定义空字符串用于拼接，循环必须拼接字符串，不能直接赋值
    # 1.读取所有商品信息
    goods_list = Goods.query.all()
    knowledge += "商品信息： \n"
    for g in goods_list:
        knowledge += f"商品名：{g.title}，价格：{g.price}, 库存：{g.stock}, 描述：{g.desc} \n"
    knowledge += "\n-----------------------\n"
    # 2.读取所有订单信息
    order_list = Order.query.all()
    knowledge += "订单信息： \n"
    for o in order_list:
        status = "待支付" if o.status == 0 else "已支付" if o.status == 1 else "已发货" if o.status == 2 else "已完成"
        knowledge += f"订单编号：{o.id}，用户ID：{o.user_id}，订单金额：{o.total_amount}，订单状态：{o.status} \n"
    knowledge += "\n-----------------------\n"
    knowledge += "客服规则：7天无理由退货，24小时内发货，包邮，退款1-3天到账"
    return knowledge

#=========================
# 三、文本切分（固定）
#====================
def split_documents():
    text = get_knowledge_from_mysql() # 从MySQL中获取数据,读取知识库的文本内容，返回的是一长字符串
    # 创建文本切分器
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    # 开始切分，把一整篇长文本，按照规则切成多个短文本片段，比如：[“商品信息： 商品1，商品2，商品3”，“订单信息： 订单1，订单2，订单3”]
    chunks = splitter.split_text(text)
    # 把切好的文本片段，包装成AI框架能用的Document对象，每个document里只存一段小内容page_content, page_content属性就是上面切好的文本片段
    docs = [Document(page_content=c) for c in chunks]
    # 返回切好的文本片段(一般用来存入向量库，给AI检索)
    return docs

# =============
# 四、向量化（固定），转成电脑能看见的形式
def build_vector_store():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    docs = split_documents()
    vs = FAISS.from_documents(docs, embeddings)
    return vs
# 五、检索（固定）
# ========================
# 实现启动时构建一次-把向量库缓存到内存或本地文件
def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = build_vector_store()
    return vector_store

def search_relevant(question, k=3):
    # vs = build_vector_store() 会每次重新构建向量库，验证影响性能，所以这里只构建一次向量库，缓存到内存中
    vs = get_vector_store() #获取缓存的向量库
    docs = vs.similarity_search(question, k=k) # 相似度检索，余弦度数越接近，检索结果越准确
    return "\n".join([d.page_content for d in docs])
# 六、RGA接口（对接前端）
# ======================
@rag_bp.route("/chat", methods=[  "POST"])
@jwt_required
def rag_chat():
    question = request.json.get("question", "")
    user_id = request.current_user_id
    # 1.从MySQL检索相关信息
    context = search_relevant(question)
    # 2.提示词（固定）
    prompt = f"""
    你是电商智能客服，请根据资料回答，不能编造内容。
    语气友好、简洁、口语化。
    
    资料：
    {context}
    
    用户问题： {question}
    回答：
    """
    # 3. 大模型配置（改成自己的）
    llm = ChatOpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-0d3924e04fd84eebaed1d226167f72ac",
        model="qwen-turbo",
    )
    answer = llm.invoke(prompt).content

    return jsonify({
        "answer": answer,
        "code": 200
    })