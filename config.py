import redis
from pymongo import MongoClient

REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_DB = 0


def get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )


MONGO_URI = "mongodb://localhost:27018"
MONGO_DB = "delivery_system"


def get_mongo_db():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]
