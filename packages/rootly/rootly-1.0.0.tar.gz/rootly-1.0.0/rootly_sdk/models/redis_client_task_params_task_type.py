from enum import Enum


class RedisClientTaskParamsTaskType(str, Enum):
    REDIS_CLIENT = "redis_client"

    def __str__(self) -> str:
        return str(self.value)
