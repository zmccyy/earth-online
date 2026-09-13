"""成就系统:数据驱动的触发条件判定。"""
from .content import ACHIEVEMENTS


def grant(state: dict, ach_id: str) -> bool:
    """直接授予成就(事件效果可指定)。"""
    if ach_id in state["achievements"]:
        return False
    state["achievements"].append(ach_id)
    info = ACHIEVEMENTS.get(ach_id, {})
    state["log"].append({"age": state["age"], "kind": "achieve",
                         "text": f"🏅 解锁成就 [{info.get('rarity', 'R')}] {info.get('name', ach_id)}:{info.get('desc', '')}"})
    return True


def _meet(state: dict, cond: dict) -> bool:
    t = cond["type"]
    if t == "flag_value":
        val = state.get("flag_values", {}).get(cond["flag"])
        if val is None:
            return False
        if "gte" in cond:
            return val >= cond["gte"]
        if "lte" in cond:
            return val <= cond["lte"]
        if "eq" in cond:
            return val == cond["eq"]
        return False
    if t == "has_flag":
        return bool(state["flags"].get(cond["flag"]))
    if t == "attr":
        v = state["attrs"].get(cond["attr"], 0)
        if "gte" in cond:
            return v >= cond["gte"]
        if "lte" in cond:
            return v <= cond["lte"]
        return False
    if t == "money_min":
        return state["money"] >= cond["value"]
    if t == "age_min":
        return state["age"] >= cond["value"]
    if t == "has_children":
        return len(state.get("children", [])) >= cond.get("count", 1)
    if t == "has_spouse":
        return bool(state.get("spouse"))
    if t == "education_in":
        return state.get("education") in cond["values"]
    return False


def check_all(state: dict) -> None:
    """扫描全部成就定义,触发满足条件者。"""
    for ach_id, a in ACHIEVEMENTS.items():
        if ach_id in state["achievements"]:
            continue
        cond = a.get("condition")
        if cond and _meet(state, cond):
            grant(state, ach_id)


def definitions() -> list[dict]:
    """成就全图鉴(供前端渲染)。"""
    return [
        {"id": a["id"], "name": a["name"], "desc": a["desc"],
         "icon": a.get("icon", "🏅"), "rarity": a.get("rarity", "R")}
        for a in ACHIEVEMENTS.values()
    ]
