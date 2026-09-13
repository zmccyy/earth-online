"""引擎单元测试:投胎、推进、事件、成就、结算。"""
import random

import pytest

from backend.engine import achievements as ach_mod
from backend.engine import character, events as ev_mod, life as life_mod
from backend.engine.content import ACHIEVEMENTS, EVENTS, FLAVOR
from backend.engine.rating import build_summary


def make_state(rng: random.Random) -> dict:
    draft = character.roll_character(rng)
    return {
        "life_id": "TEST", "status": "draft", "stage": "投胎中", **draft,
        "money": 0, "flags": {}, "education": "无", "graduate_age": None,
        "job": None, "spouse": None, "children": [], "mortgage": None,
        "flag_values": {}, "log": [], "achievements": [],
        "milestones_done": [], "event_history": [], "pending_event": None,
        "death": None, "summary": None,
    }


def test_roll_character_bounded():
    rng = random.Random(42)
    for _ in range(200):
        c = character.roll_character(rng)
        assert c["gender"] in ("男", "女")
        assert 5 <= c["attrs"]["health"] <= 95
        assert c["family"]["money"] >= 0
        assert c["rerolls_left"] == FLAVOR["reroll_limit"]


def test_reroll_consumes_chance():
    rng = random.Random(7)
    state = make_state(rng)
    before = state["rerolls_left"]
    character.reroll(state, rng)
    assert state["rerolls_left"] == before - 1


def test_stage_progression():
    rng = random.Random(1)
    s = make_state(rng)
    life_mod.start_life(s, rng)
    stages = []
    for age in range(0, 66):
        s["age"] = age
        stages.append(life_mod.get_stage(s))
    assert stages[0] == "婴幼儿"
    assert stages[8] == "小学"
    assert stages[17] == "高中"
    assert "中年" in stages
    assert stages[65] == "退休生活"


def test_full_life_terminates():
    """推进到死:人生必然以死亡结算,年龄在合理区间。"""
    rng = random.Random(123)
    s = make_state(rng)
    life_mod.start_life(s, rng)
    for _ in range(200):
        if s["status"] == "dead":
            break
        if s["pending_event"]:
            ev_mod.resolve_choice(s, 0, rng)
        else:
            life_mod.advance_year(s, rng)
    assert s["status"] == "dead"
    assert s["death"] and 0 < s["death"]["age"] <= 121
    assert s["summary"] and s["summary"]["grade"]


def test_conditions_gate():
    s = make_state(random.Random(5))
    s["age"] = 30
    s["money"] = 100
    assert ev_mod.check_conditions(s, {"money_min": 50, "min_age": 18})
    assert not ev_mod.check_conditions(s, {"money_min": 500})
    s["flags"]["已婚"] = True
    assert ev_mod.check_conditions(s, {"flags_any": ["已婚", "失恋"]})
    assert not ev_mod.check_conditions(s, {"flags_none": ["已婚"]})


def test_event_choice_effects_applied():
    s = make_state(random.Random(9))
    life_mod.start_life(s, random.Random(9))
    s["age"] = 30
    s["pending_event"] = {
        "id": "t", "name": "测试事件", "text": "", "tag": "normal",
        "milestone": False,
        "choices": [{"text": "加钱", "effects": {"money": 1000, "happiness": -5},
                     "log": "干了"}],
    }
    ev_mod.resolve_choice(s, 0, random.Random())
    assert s["money"] >= 1000
    assert s["pending_event"] is None
    assert s["event_history"] == ["t"]


def test_achievements_trigger():
    s = make_state(random.Random(11))
    life_mod.start_life(s, random.Random(11))
    s["flags"]["编制内"] = True
    ach_mod.check_all(s)
    assert "ach_bianzhi" in s["achievements"]
    assert ach_mod.grant(s, "ach_bianzhi") is False  # 不重复授予


def test_content_consistency():
    """内容一致性:事件引用的成就必须存在;里程碑结构合法;JSON可加载。"""
    for ev in EVENTS.values():
        for c in ev.get("choices", []):
            for a in c.get("effects", {}).get("grant_achievement", []):
                assert a in ACHIEVEMENTS, f"事件 {ev['id']} 引用了不存在的成就 {a}"
        for a in ev.get("effects", {}).get("grant_achievement", []):
            assert a in ACHIEVEMENTS, f"事件 {ev['id']} 引用了不存在的成就 {a}"
        if ev.get("milestone") and ev.get("milestone_age") is None:
            assert ev.get("conditions"), "条件触发型里程碑必须带 conditions"
    for a in ACHIEVEMENTS.values():
        assert a["condition"]["type"], f"成就 {a['id']} 缺少条件"


def test_summary_tiers():
    s = make_state(random.Random(13))
    life_mod.start_life(s, random.Random(13))
    s["death"] = {"age": 75, "cause": "测试"}
    s["money"] = 500000
    s["achievements"] = ["ach_985", "ach_bianzhi"]
    summary = build_summary(s)
    assert summary["grade"] in {"SSS", "SSR", "SR", "A", "B", "C", "D"}
    assert "comment" in summary and "review" in summary
