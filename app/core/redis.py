import redis.asyncio as redis

redis_async = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)