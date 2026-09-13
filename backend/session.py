"""游戏会话存储:内存版(单机本地游戏)。

生产化提示:多进程/分布式部署时应替换为 DB/Redis 后端,接口保持不变。
"""
import threading


class LifeStore:
    def __init__(self):
        self._data: dict[str, dict] = {}
        self._lock = threading.Lock()

    def put(self, state: dict) -> None:
        with self._lock:
            self._data[state["life_id"]] = state

    def get(self, life_id: str) -> dict | None:
        with self._lock:
            return self._data.get(life_id)

    def delete(self, life_id: str) -> None:
        with self._lock:
            self._data.pop(life_id, None)

    def count(self) -> int:
        with self._lock:
            return len(self._data)


store = LifeStore()
