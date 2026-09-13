"""API 集成测试:最小闭环 走完整人生。"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def play_until_dead(life_id: str, max_years: int = 200):
    for _ in range(max_years):
        state = client.get(f"/api/life/{life_id}").json()
        if state["status"] == "dead":
            return state
        if state["pending_event"]:
            n = len(state["pending_event"]["choices"])
            r = client.post(f"/api/life/{life_id}/choose", json={"index": n - 1})
            assert r.status_code == 200, r.text
        else:
            r = client.post(f"/api/life/{life_id}/advance")
            assert r.status_code == 200, r.text
    return state


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_achievements_gallery():
    r = client.get("/api/achievements")
    assert r.status_code == 200
    assert len(r.json()["achievements"]) >= 10


def test_full_life_loop():
    """最小闭环:投胎→重抽→开局→活到死→结算。"""
    r = client.post("/api/reincarnate", json={"name": "测试玩家"})
    assert r.status_code == 200, r.text
    state = r.json()
    lid = state["life_id"]
    assert state["status"] == "draft"
    assert state["rerolls_left"] >= 1

    # 重抽一次
    r = client.post(f"/api/life/{lid}/reroll")
    assert r.status_code == 200
    assert r.json()["rerolls_left"] == state["rerolls_left"] - 1

    # 开局
    r = client.post(f"/api/life/{lid}/start")
    assert r.status_code == 200
    assert r.json()["status"] == "living"

    # 推进若干年:每一年要么推进要么决策
    r = client.post(f"/api/life/{lid}/advance")
    assert r.status_code == 200
    body = r.json()
    assert body["state"]["age"] == 1

    # 死亡前 advance 正常;完整打完一局
    final = play_until_dead(lid)
    assert final["status"] == "dead"
    assert final["summary"]["grade"]
    assert final["death"]["age"] >= 1


def test_advance_blocked_when_pending():
    r = client.post("/api/reincarnate")
    lid = r.json()["life_id"]
    client.post(f"/api/life/{lid}/start")
    # 快速推进到出现 pending 事件为止
    blocked = False
    for _ in range(40):
        state = client.get(f"/api/life/{lid}").json()
        if state["status"] == "dead":
            break
        if state["pending_event"]:
            blocked = True
            r = client.post(f"/api/life/{lid}/advance")
            assert r.status_code == 409
            break
        client.post(f"/api/life/{lid}/advance")
    # 事件决策后可继续
    if blocked:
        r = client.post(f"/api/life/{lid}/choose", json={"index": 0})
        assert r.status_code == 200
        assert client.get(f"/api/life/{lid}").json()["pending_event"] is None


def test_unknown_life_404():
    r = client.get("/api/life/NOPE")
    assert r.status_code == 404


def test_choose_invalid_index():
    r = client.post("/api/reincarnate")
    lid = r.json()["life_id"]
    client.post(f"/api/life/{lid}/start")
    r = client.post(f"/api/life/{lid}/choose", json={"index": 0})
    assert r.status_code == 409  # 没有事件时不能选择


def test_static_frontend():
    r = client.get("/")
    assert r.status_code == 200
    assert "地球" in r.text
