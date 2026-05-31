from __future__ import annotations

from abc import ABC, abstractmethod

import redis

from packages.agent_core.config import settings


class BaseQueue(ABC):
    @abstractmethod
    def enqueue(self, task_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def dequeue(self, timeout: int = 1) -> str | None:
        raise NotImplementedError


class MemoryQueue(BaseQueue):
    def __init__(self) -> None:
        self.items: list[str] = []

    def enqueue(self, task_id: str) -> None:
        self.items.append(task_id)

    def dequeue(self, timeout: int = 1) -> str | None:
        if not self.items:
            return None
        return self.items.pop(0)


class RedisQueue(BaseQueue):
    def __init__(self) -> None:
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.key = "agent:task_queue"

    def enqueue(self, task_id: str) -> None:
        self.client.rpush(self.key, task_id)

    def dequeue(self, timeout: int = 1) -> str | None:
        item = self.client.blpop(self.key, timeout=timeout)
        if item is None:
            return None
        _, task_id = item
        return task_id


_queue: BaseQueue | None = None


def get_queue() -> BaseQueue:
    global _queue
    if _queue is not None:
        return _queue
    if settings.queue_backend == "redis":
        _queue = RedisQueue()
    else:
        _queue = MemoryQueue()
    return _queue
