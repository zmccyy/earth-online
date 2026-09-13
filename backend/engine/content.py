"""内容加载器:读取 backend/content/ 下的数据驱动配置。

引擎只从内存中的 JSON 结构读取内容,添加新内容不需要改引擎代码。
"""
import json
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"


def _load(filename: str) -> dict:
    with open(CONTENT_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


EVENTS_DATA: dict = _load("events.json")
ACHIEVEMENTS_DATA: dict = _load("achievements.json")
FLAVOR: dict = _load("flavor.json")

# 事件按 id 索引
EVENTS: dict[str, dict] = {ev["id"]: ev for ev in EVENTS_DATA["events"]}
MILESTONES: list[dict] = [ev for ev in EVENTS_DATA["events"] if ev.get("milestone")]
RANDOM_EVENTS: list[dict] = [ev for ev in EVENTS_DATA["events"] if not ev.get("milestone")]
ACHIEVEMENTS: dict[str, dict] = {a["id"]: a for a in ACHIEVEMENTS_DATA["achievements"]}
