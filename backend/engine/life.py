"""人生推进:年度结算、阶段判定、生存与死亡。"""
import random

from . import achievements as ach_mod
from . import events as ev_mod
from .character import ATTR_KEYS
from .content import FLAVOR

LIVING_COST = 30000          # 成年后年度基础生活开销(元)
CHILD_COST = 20000           # 养小号的氪金深渊(元/年)
PENSION = 24000              # 养老金(元/年)

STAGES = [
    ("婴幼儿", 0, 3), ("幼儿园", 4, 6), ("小学", 7, 12), ("初中", 13, 15),
    ("高中", 16, 18), ("大学", 19, 29), ("职场新人", 23, 30),
    ("中年", 31, 45), ("中年后期", 46, 59), ("退休生活", 60, 79), ("长寿区", 80, 200),
]


def get_stage(state: dict) -> str:
    age = state["age"]
    flags = state["flags"]
    if age <= 18:
        for name, lo, hi in STAGES[:5]:
            if lo <= age <= hi:
                return name
    if flags.get("大学生") and age <= 29:
        return "大学"
    if age <= 30:
        return "职场新人"
    if age <= 45:
        return "中年"
    if age <= 59:
        return "中年后期"
    if age <= 79:
        return "退休生活"
    return "长寿区"


def passive_year(state: dict, rng: random.Random) -> list[dict]:
    """被动年度结算:成长、收支、老化。"""
    logs = []
    age = state["age"]
    attrs = state["attrs"]
    flags = state["flags"]

    # 阶段成长与老化(衰减放缓:中年隔年掉血,规律养生可对冲)
    if age <= 3:
        attrs["health"] += 3
    elif age <= 12:
        attrs["intellect"] += 3
    elif age <= 15:
        attrs["intellect"] += 2
        attrs["happiness"] -= 1
    elif age <= 18:
        attrs["intellect"] += 2
        attrs["happiness"] -= 2  # 高中内卷天梯
    elif age <= 29:
        attrs["appearance"] += 1
        attrs["happiness"] += 1 if flags.get("大学生") else 0
    elif age <= 45:
        if age % 2 == 0:
            attrs["health"] -= 1
        attrs["happiness"] -= 1 if flags.get("996战士") else 0
    elif age <= 59:
        if age % 2 == 0:
            attrs["health"] -= 1
    elif age <= 75:
        attrs["health"] -= 1
        attrs["happiness"] += 1  # 广场舞与钓鱼佬的快乐
    else:
        attrs["health"] -= 2
        attrs["happiness"] += 1

    # 收支
    money_delta = 0
    if state.get("job"):
        money_delta += state["job"]["salary"]
    if state.get("mortgage"):
        money_delta -= state["mortgage"]["annual"]
        state["mortgage"]["years_left"] -= 1
        if state["mortgage"]["years_left"] <= 0:
            state["mortgage"] = None
            flags.pop("房奴", None)
            flags["全款勇士"] = True
            logs.append({"age": age, "kind": "good",
                         "text": "【毕业装备】房贷三十年订阅终于到期,这套毕业装备正式归你所有!"})
    if age >= 18:
        money_delta -= LIVING_COST
    if flags.get("有娃"):
        money_delta -= CHILD_COST
    if age >= 60 and not state.get("job"):
        money_delta += PENSION
    if money_delta:
        state["money"] += money_delta

    # 大学毕业检查:到达 graduate_age 退出学生身份(找工作事件由里程碑负责)
    if flags.get("大学生") and state.get("graduate_age") is not None and age >= state["graduate_age"]:
        flags.pop("大学生", None)
    # 负债状态
    if state["money"] < 0:
        flags["负债"] = True
        attrs["happiness"] -= 1
    else:
        flags.pop("负债", None)
    return logs


def death_check(state: dict, rng: random.Random) -> bool:
    """年度死亡判定:年龄基础死亡率 + 体质修正 + 意外。"""
    if state["attrs"]["health"] <= 0:
        die(state, "体质归零,身体被掏空,被服务器强制下线")
        return True
    age = state["age"]
    health = state["attrs"]["health"]
    rate = 0.0
    if age < 10:
        rate = 0.001
    elif age < 40:
        rate = 0.002
    elif age < 60:
        rate = 0.004
    elif age < 70:
        rate = 0.012
    elif age < 80:
        rate = 0.03
    elif age < 90:
        rate = 0.08
    elif age < 100:
        rate = 0.2
    else:
        rate = 0.4
    if age >= 10 and health < 30:
        rate += 0.03
    if state["flags"].get("996战士") and age < 45:
        rate += 0.01
    if rng.random() < rate:
        causes = ["年纪到了,服务器自动回收账号", "睡梦中静悄悄掉线,这是最优雅的注销方式"]
        die(state, causes[0] if age >= 70 else causes[1])
        return True
    if age >= 20 and rng.random() < 0.0025:
        die(state, "随机意外事件:现实副本的物理引擎太真实了")
        return True
    return False


def die(state: dict, cause: str) -> None:
    """注销账号:状态转为 dead 并生成结算。"""
    state["status"] = "dead"
    state["death"] = {"age": state["age"], "cause": cause}
    state["log"].append({"age": state["age"], "kind": "big",
                         "text": f"账号已注销(享年{state['age']}岁):{cause}"})
    from .rating import build_summary
    state["summary"] = build_summary(state)


def start_life(state: dict, rng: random.Random) -> None:
    """确认投胎:从草稿进入正式人生。"""
    state["status"] = "living"
    state["age"] = 0
    fam = state["family"]
    state["money"] = fam["money"]
    state["education"] = "无"
    state["graduate_age"] = None
    state["job"] = None
    state["spouse"] = None
    state["children"] = []
    state["mortgage"] = None
    state["flag_values"] = {}
    if fam["id"] in ("whale", "demolition"):
        state["flags"]["氪金开局"] = True
    if fam["id"] == "demolition":
        state["flags"]["拆迁开局"] = True
    state["log"] = [{
        "age": 0, "kind": "big",
        "text": (f"出生在{state['hometown']['name']}的{fam['name']}(开局难度:{fam['tier']})。"
                 f"{fam['desc']}两位老玩家组队带新,新手村生涯开始。"),
    }]


def _handle_ending(state: dict) -> None:
    """处理事件效果标记的特殊结局(如灵魂觉醒通关)。"""
    e = state.pop("_ending", None)
    if e and state["status"] == "living":
        die(state, e["cause"])
        state["death"]["ending"] = e["type"]


def resolve_pending(state: dict, index: int, rng: random.Random) -> list[dict]:
    """API 层调用:结算玩家对 pending_event 的选择。"""
    logs = ev_mod.resolve_choice(state, index, rng)
    _handle_ending(state)
    ev_mod.clamp_state(state)
    ach_mod.check_all(state)
    return logs


def advance_year(state: dict, rng: random.Random) -> dict:
    """活过这一年。返回 {logs, event}。若 pending_event 未决则拒绝。"""
    if state["status"] != "living":
        raise ValueError("该账号未在游戏中")
    if state["pending_event"]:
        raise RuntimeError("存在未决策的事件")
    state["age"] += 1
    state["stage"] = get_stage(state)
    logs: list[dict] = []
    logs.extend(passive_year(state, rng))
    if not death_check(state, rng):
        ev = ev_mod.pick_event(state, rng)
        if ev:
            if ev.get("choices"):
                pending = ev_mod.instantiate(ev)
                # 过滤掉当前不满足条件的选项
                pending["choices"] = [c for c in pending["choices"]
                                      if ev_mod.choice_available(state, c)]
                if not pending["choices"]:
                    logs.extend(ev_mod.resolve_auto(state, {**ev, "choices": None}, rng))
                else:
                    state["pending_event"] = pending
            else:
                logs.extend(ev_mod.resolve_auto(state, ev, rng))
        else:
            calm = FLAVOR.get("calm_years", ["岁月静好,服务器运行正常。"])
            entry = {"age": state["age"], "kind": "calm",
                     "text": f"【日常】{rng.choice(calm)}"}
            state["log"].append(entry)
            logs.append(entry)
    ev_mod.clamp_state(state)
    _handle_ending(state)
    ach_mod.check_all(state)
    if state["status"] == "living" and state["age"] >= 120:
        die(state, "120岁,服务器认证的活化石,天道亲自为你颁发长寿勋章")
    return {"logs": logs, "event": state["pending_event"]}
