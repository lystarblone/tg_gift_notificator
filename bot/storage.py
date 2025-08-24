import asyncio
import json
import os
from typing import Set


class JsonStateStore:
    def __init__(self, state_path: str) -> None:
        self._state_path = state_path
        self._lock = asyncio.Lock()
        self._subscribers: Set[int] = set()
        self._last_seen_id: int = 0

    async def load(self) -> None:
        os.makedirs(os.path.dirname(self._state_path) or ".", exist_ok=True)
        if not os.path.exists(self._state_path):
            await self._persist()
            return
        try:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, self._read_file_sync)
            self._subscribers = set(int(x) for x in data.get("subscribers", []))
            self._last_seen_id = int(data.get("last_seen_gift_id", 0))
        except Exception:
            self._subscribers = set()
            self._last_seen_id = 0

    def _read_file_sync(self):
        with open(self._state_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_file_sync(self, payload):
        with open(self._state_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    async def _persist(self) -> None:
        loop = asyncio.get_running_loop()
        payload = {
            "subscribers": sorted(self._subscribers),
            "last_seen_gift_id": self._last_seen_id,
        }
        await loop.run_in_executor(None, self._write_file_sync, payload)

    async def add_subscriber(self, user_id: int) -> bool:
        async with self._lock:
            before = len(self._subscribers)
            self._subscribers.add(int(user_id))
            if len(self._subscribers) != before:
                await self._persist()
                return True
            return False

    async def remove_subscriber(self, user_id: int) -> bool:
        async with self._lock:
            removed = int(user_id) in self._subscribers
            self._subscribers.discard(int(user_id))
            if removed:
                await self._persist()
            return removed

    async def get_subscribers(self) -> Set[int]:
        async with self._lock:
            return set(self._subscribers)

    async def get_last_seen_id(self) -> int:
        async with self._lock:
            return int(self._last_seen_id)

    async def set_last_seen_id(self, gift_id: int) -> None:
        async with self._lock:
            if gift_id > self._last_seen_id:
                self._last_seen_id = int(gift_id)
                await self._persist()