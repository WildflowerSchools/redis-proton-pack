import os

from redis import Redis


class BaseManager:
    __client = None

    @classmethod
    def redis_connect(cls):
        if cls.__client is None:
            redis_args = {}
            if "PROTON_PACK_REDIS_HOST" in os.environ:
                redis_args["host"] = os.environ["PROTON_PACK_REDIS_HOST"]
            if "PROTON_PACK_REDIS_PORT" in os.environ:
                redis_args["port"] = os.environ["PROTON_PACK_REDIS_PORT"]
            if "PROTON_PACK_REDIS_PASS" in os.environ:
                redis_args["password"] = os.environ["PROTON_PACK_REDIS_PASS"]
            cls.__client = Redis(**redis_args)
        return cls.__client
