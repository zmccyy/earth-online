"""REST API:前端与引擎之间的唯一通信契约。"""
import random
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .engine import achievements as ach_mod
from .engine import character, events as ev_mod, life as life_mod
from .engine.content import FLAVOR
from .session import store

router = APIRouter(prefix="/api")


class ReincarnateBody(BaseModel):
    name: str | None = Field(default=None, max_length=12)


class ChooseBody(BaseModel):
    index: int = Field(ge=0, le=9)


def _new_state(name: str | None) -> dict:
    rng = random.Random()
    draft = character.roll_character(rng, name)
    return {
        "life_id": f"L{uuid.uuid4().hex[:8].upper()}",
        "status": "draft",
        "stage": "投胎中",
        **draft,
        "money": 0,
        "flags": {},
        "education": "无",
        "graduate_age": None,
        "job": None,
        "spouse": None,
        "children": [],
        "mortgage": None,
        "flag_values": {},
        "log": [],
        "achievements": [],
        "milestones_done": [],
        "event_history": [],
        "pending_event": None,
        "death": None,
        "summary": None,
    }


def _get(life_id: str) -> dict:
    state = store.get(life_id)
    if state is None:
        raise HTTPException(404, detail="账号不存在:该玩家从未登录过本服务器")
    return state


@router.get("/health")
def health():
    return {
        "status": "ok",
        "game": "地球Online",
        "online_players": "8,086,000,000",
        "active_lifes": store.count(),
        "notice": "本游戏强制登录、无法退游、不支持存档。祝你好运,玩家。",
    }


@router.get("/achievements")
def achievement_gallery():
    """成就全图鉴(含未解锁),供前端渲染。"""
    return {"achievements": ach_mod.definitions()}


@router.post("/reincarnate")
def reincarnate(body: ReincarnateBody | None = None):
    """投胎:创建一个草稿角色(可重抽,确认后生效)。"""
    state = _new_state(body.name if body else None)
    state["log"] = [{"age": 0, "kind": "calm", "text": "孟婆汤已免费续杯,你的新账号正在排队登录地球OL……"}]
    store.put(state)
    return state


@router.post("/life/{life_id}/reroll")
def reroll(life_id: str):
    """重抽天赋(玄学次数有限)。"""
    state = _get(life_id)
    if state["status"] != "draft":
        raise HTTPException(400, detail="已确认投胎,不能再改面板了")
    if state["rerolls_left"] <= 0:
        raise HTTPException(400, detail="玄学次数已用完,孟婆不愿意再续杯了")
    rng = random.Random()
    character.reroll(state, rng)
    state["log"].append({"age": 0, "kind": "calm",
                         "text": f"你再次喝了孟婆汤重新投胎(剩余机会:{state['rerolls_left']})。"})
    return state


@router.post("/life/{life_id}/start")
def start(life_id: str):
    """确认投胎,正式开始人生。"""
    state = _get(life_id)
    if state["status"] != "draft":
        raise HTTPException(400, detail="该账号已经在游戏中了")
    rng = random.Random()
    life_mod.start_life(state, rng)
    state["stage"] = life_mod.get_stage(state)
    return state


@router.get("/life/{life_id}")
def get_life(life_id: str):
    return _get(life_id)


@router.post("/life/{life_id}/advance")
def advance(life_id: str):
    """活过一年。"""
    state = _get(life_id)
    if state["status"] == "draft":
        raise HTTPException(400, detail="请先确认投胎")
    if state["status"] == "dead":
        raise HTTPException(400, detail="账号已注销。想再玩?请重新投胎。")
    if state["pending_event"]:
        raise HTTPException(409, detail="有未决策的事件,先做完选择再推进")
    rng = random.Random()
    result = life_mod.advance_year(state, rng)
    return {"state": state, "logs": result["logs"], "event": result["event"],
            "dead": state["status"] == "dead"}


@router.post("/life/{life_id}/choose")
def choose(life_id: str, body: ChooseBody):
    """对 pending_event 做出选择。"""
    state = _get(life_id)
    if state["status"] != "living":
        raise HTTPException(400, detail="该账号不在游戏中")
    if not state["pending_event"]:
        raise HTTPException(409, detail="当前没有待决策的事件")
    try:
        logs = life_mod.resolve_pending(state, body.index, random.Random())
    except IndexError:
        raise HTTPException(400, detail="无效的选项编号")
    return {"state": state, "logs": logs, "event": state["pending_event"],
            "dead": state["status"] == "dead"}
