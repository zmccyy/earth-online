"""事件引擎:条件判定、加权抽取、选择结算。

事件全部来自 data-driven 的 events.json,引擎只负责通用机制:
条件过滤 → 权重抽取 → 实例化 pending_event → 按玩家选择应用 effects。
"""
import random

from . import achievements as ach_mod
from .content import EVENTS, FLAVOR, MILESTONES, RANDOM_EVENTS

MAX_ATTR = 100


def _flags(state: dict) -> dict:
    return state.setdefault("flags", {})


def check_conditions(state: dict, cond: dict | None) -> bool:
    """所有条件 AND 组合;未写的条件视为通过。"""
    if not cond:
        return True
    flags = _flags(state)
    if not (cond.get("min_age", state["age"]) <= state["age"] <= cond.get("max_age", 999)):
        return False
    if "stages" in cond and state.get("stage") not in cond["stages"]:
        return False
    if "flags_any" in cond and not any(flags.get(f) for f in cond["flags_any"]):
        return False
    if "flags_all" in cond and not all(flags.get(f) for f in cond["flags_all"]):
        return False
    if "flags_none" in cond and any(flags.get(f) for f in cond["flags_none"]):
        return False
    for k, v in cond.get("attr_min", {}).items():
        if state["attrs"].get(k, 0) < v:
            return False
    for k, v in cond.get("attr_max", {}).items():
        if state["attrs"].get(k, 999) > v:
            return False
    if "money_min" in cond and state["money"] < cond["money_min"]:
        return False
    if "money_max" in cond and state["money"] > cond["money_max"]:
        return False
    if "has_job" in cond and bool(state.get("job")) != cond["has_job"]:
        return False
    if "has_spouse" in cond and bool(state.get("spouse")) != cond["has_spouse"]:
        return False
    if "education_in" in cond and state.get("education") not in cond["education_in"]:
        return False
    if "chance" in cond and random.random() > cond["chance"]:
        return False
    if cond.get("graduate_reached"):
        grad = state.get("graduate_age") or 18
        if state["age"] < grad:
            return False
    return True


def choice_available(state: dict, choice: dict) -> bool:
    return check_conditions(state, choice.get("conditions"))


def pick_event(state: dict, rng: random.Random) -> dict | None:
    """为本年抽取事件:先里程碑(确定),再随机池(加权)。"""
    # 1) 里程碑事件:固定年龄触发或条件触发,每个一生最多一次
    for ev in MILESTONES:
        key = ev["id"]
        if key in state["milestones_done"]:
            continue
        when = ev.get("milestone_age")
        if when is not None and when != state["age"]:
            continue
        if check_conditions(state, ev.get("conditions")):
            return ev
    # 2) 随机事件:85% 年份出事件
    if rng.random() > 0.85:
        return None
    pool = []
    for ev in RANDOM_EVENTS:
        if ev.get("once", True) and ev["id"] in state["event_history"]:
            continue
        if not check_conditions(state, ev.get("conditions")):
            continue
        pool.append((ev, ev.get("weight", 10)))
    if not pool:
        return None
    total = sum(w for _, w in pool)
    pick = rng.uniform(0, total)
    acc = 0
    for ev, w in pool:
        acc += w
        if pick <= acc:
            return ev
    return None


def instantiate(ev: dict) -> dict:
    """把事件定义实例化为可存储的 pending_event(拷贝可变部分)。"""
    return {
        "id": ev["id"],
        "name": ev["name"],
        "text": ev["text"],
        "tag": ev.get("tag", "normal"),
        "milestone": bool(ev.get("milestone")),
        "choices": [dict(c) for c in ev.get("choices", [])],
    }


def apply_effects(state: dict, effects: dict, rng: random.Random) -> None:
    """应用效果字典:属性/金钱/flag/身份变更/成就/特殊结局。"""
    for k, v in effects.items():
        if k in state["attrs"]:
            state["attrs"][k] += int(v)
    if "money" in effects:
        state["money"] += int(effects["money"])
    for f in effects.get("flags_add", []):
        _flags(state)[f] = True
    for f in effects.get("flags_remove", []):
        _flags(state).pop(f, None)
    if "set_education" in effects:
        state["education"] = effects["set_education"]
    if "set_job" in effects:
        state["job"] = dict(effects["set_job"])
        _flags(state)["在职"] = True
        _flags(state).pop("失业", None)
    if "salary_mult" in effects and state.get("job"):
        state["job"]["salary"] = max(10000, int(state["job"]["salary"] * effects["salary_mult"]))
    if effects.get("lose_job"):
        state["job"] = None
        _flags(state)["失业"] = True
        _flags(state).pop("在职", None)
        _flags(state).pop("996战士", None)
    if effects.get("match_spouse"):
        pool = FLAVOR.get("spouses", [{"name": "盲盒队友", "traits": "未知参数"}])
        s = rng.choice(pool)
        state["spouse"] = dict(s)
        _flags(state)["已婚"] = True
        _flags(state).pop("单身狗", None)
    if "set_spouse" in effects:
        state["spouse"] = dict(effects["set_spouse"])
        _flags(state)["已婚"] = True
        _flags(state).pop("单身狗", None)
    if effects.get("divorce"):
        state["spouse"] = None
        _flags(state).pop("已婚", None)
        _flags(state)["单身狗"] = True
    if effects.get("add_child"):
        state["children"].append({"name": "小号" + str(len(state["children"]) + 1)})
        _flags(state)["有娃"] = True
    if "mortgage" in effects:
        state["mortgage"] = dict(effects["mortgage"])
        _flags(state)["房奴"] = True
    if "graduate_age" in effects:
        state["graduate_age"] = effects["graduate_age"]
    for k, v in effects.get("set_flag_value", {}).items():
        state.setdefault("flag_values", {})[k] = v
    for a in effects.get("grant_achievement", []):
        ach_mod.grant(state, a)
    if "ending" in effects:
        state["_ending"] = {"type": effects["ending"],
                            "cause": effects.get("ending_cause", "人生落幕")}
    if "roll_gaokao" in effects:
        _roll_gaokao(state, effects["roll_gaokao"], rng)


def _roll_gaokao(state: dict, cfg: dict, rng: random.Random) -> None:
    """高考副本结算:分数 = 智力*6*努力系数 + 随机发挥。"""
    effort = cfg.get("effort", 1.0)
    score = int(state["attrs"]["intellect"] * 6 * effort + rng.randint(-50, 60))
    score = max(100, min(750, score))
    state.setdefault("flag_values", {})["gaokao_score"] = score
    if score >= 670:
        state["education"] = "本科·985"
        state["log"].append({"age": state["age"], "kind": "big",
                             "text": f"高考副本结算:{score}分!服务器公告:恭喜通关『985』隐藏副本!"})
        ach_mod.grant(state, "ach_gaokao700" if score >= 700 else "ach_985")
    elif score >= 600:
        state["education"] = "本科·211"
        state["log"].append({"age": state["age"], "kind": "big",
                             "text": f"高考副本结算:{score}分,成功接取『211』主线!亲戚NPC集体刷屏祝贺。"})
        ach_mod.grant(state, "ach_211")
    elif score >= 520:
        state["education"] = "本科·一本"
        state["log"].append({"age": state["age"], "kind": "big",
                             "text": f"高考副本结算:{score}分,普通本科主线已接取。"})
    elif score >= 440:
        state["education"] = "本科·二本"
        state["log"].append({"age": state["age"], "kind": "normal",
                             "text": f"高考副本结算:{score}分,二本线低空飞过,队友说『本科就行』。"})
    else:
        state["education"] = "专科"
        state["log"].append({"age": state["age"], "kind": "bad",
                             "text": f"高考副本结算:{score}分。系统提示:副本失败,已为你匹配『专科』支线。"})
    if score >= 440:
        state["graduate_age"] = state["age"] + (4 if state["education"] != "专科" else 3)
        _flags(state)["大学生"] = True
    else:
        state["graduate_age"] = state["age"]  # 直接进入社会服


def resolve_choice(state: dict, index: int, rng: random.Random) -> list[dict]:
    """结算玩家选择:应用效果并生成年度日志。返回本年日志条目。"""
    ev = state["pending_event"]
    if ev is None:
        raise ValueError("没有待决策的事件")
    if index < 0 or index >= len(ev["choices"]):
        raise IndexError("无效的选项编号")
    c = ev["choices"][index]
    apply_effects(state, c.get("effects", {}), rng)
    entry = {"age": state["age"],
             "kind": ev.get("tag", "normal"),
             "text": f"【{ev['name']}】{c.get('log', '')}"}
    state["log"].append(entry)
    state["event_history"].append(ev["id"])
    if ev.get("milestone"):
        state["milestones_done"].append(ev["id"])
    state["pending_event"] = None
    return [entry]


def resolve_auto(state: dict, ev: dict, rng: random.Random) -> list[dict]:
    """结算无选项的自动事件。"""
    apply_effects(state, ev.get("effects", {}), rng)
    entry = {"age": state["age"], "kind": ev.get("tag", "normal"),
             "text": f"【{ev['name']}】{ev.get('log', '')}"}
    state["log"].append(entry)
    state["event_history"].append(ev["id"])
    if ev.get("milestone"):
        state["milestones_done"].append(ev["id"])
    return [entry]


def clamp_state(state: dict) -> None:
    for k in state["attrs"]:
        state["attrs"][k] = max(0, min(MAX_ATTR, state["attrs"][k]))
