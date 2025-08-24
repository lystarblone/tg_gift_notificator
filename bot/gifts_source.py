import asyncio
import json
import os
from typing import Any, Dict, List


def _read_json_sync(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def load_gifts(feed_path: str) -> List[Dict[str, Any]]:
    loop = asyncio.get_running_loop()
    if not os.path.exists(feed_path):
        return []
    data = await loop.run_in_executor(None, _read_json_sync, feed_path)
    gifts = []
    for item in data:
        try:
            gifts.append(
                {
                    "id": int(item["id"]),
                    "title": str(item.get("title", f"Gift {item['id']}")),
                    "published_at": str(item.get("published_at", "")),
                }
            )
        except Exception:
            continue
    gifts.sort(key=lambda x: x["id"])
    return gifts


async def get_new_gifts(feed_path: str, last_seen_id: int) -> List[Dict[str, Any]]:
    all_gifts = await load_gifts(feed_path)
    return [g for g in all_gifts if g["id"] > last_seen_id]