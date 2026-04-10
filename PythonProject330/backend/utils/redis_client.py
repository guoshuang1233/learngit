import  redis

# 创建Redis 客户端
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True # 自动转字符串
)

