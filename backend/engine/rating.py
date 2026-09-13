"""人生结算:评分、评级称号与走马灯文案。"""
import math

from .content import FLAVOR

TIERS = [
    {"min": 112, "grade": "SSS", "name": "天选剧本", "comment": "策划看了你的账号都要怀疑你有内部数据。"},
    {"min": 100, "grade": "SSR", "name": "人上人", "comment": "你的开局是别人肝三辈子的终点,评论已刷屏『慕了慕了』。"},
    {"min": 82, "grade": "SR", "name": "人生赢家", "comment": "主线支线双开花,服务器认证的优质玩家。"},
    {"min": 60, "grade": "A", "name": "优质玩家", "comment": "虽没毕业全身神装,但你也算把副本打得有模有样。"},
    {"min": 42, "grade": "B", "name": "普通玩家", "comment": "标准模板人生:上学、上班、组队、养小号。服务器因你而卡。"},
    {"min": 26, "grade": "C", "name": "资深牛马", "comment": "每日任务做满了,毕业装备却一直没爆。辛苦了,牛马。"},
    {"min": 0, "grade": "D", "name": "删号重练", "comment": "这号练废了。别灰心,反正这游戏本来就强制重开。"},
]


def build_summary(state: dict) -> dict:
    """死亡后生成人生总结。"""
    if state.get("death", {}).get("cause", "").find("看破红尘") >= 0 or \
       state.get("death", {}).get("ending") == "awaken":
        grade, name, comment = "SSS+", "通关者·看破红尘", \
            "你居然看穿了这只是一个游戏……恭喜通关地球OL,高维世界见。"
    else:
        score = _score(state)
        tier = next(t for t in TIERS if score >= t["min"])
        grade, name, comment = tier["grade"], tier["name"], tier["comment"]
    summary = {
        "grade": grade,
        "grade_name": name,
        "comment": comment,
        "age": state["death"]["age"],
        "cause": state["death"]["cause"],
        "final_money": state["money"],
        "achievements": state["achievements"],
        "education": state.get("education", "无"),
        "flags": [k for k, v in state["flags"].items() if v],
        "highlights": _highlights(state),
        "review": "好评👍 意犹未尽,马上重开!" if state["attrs"]["happiness"] >= 50 else "差评👎 策划出来挨打!这游戏根本没法玩!",
    }
    return summary


def _score(state: dict) -> int:
    score = 0.0
    score += min(50, state["death"]["age"] * 0.5)          # 存活年限(长寿是硬通货)
    score += min(18, math.log10(max(state["money"], 1) + 1) * 3)  # 财富(对数)
    score += (sum(state["attrs"].values()) / 4) * 0.30     # 面板均值(满分30)
    score += min(10, len(state["achievements"]) * 1.8)     # 成就
    edu_bonus = {"博士": 8, "硕士": 7, "本科·985": 7, "本科·211": 5,
                 "本科·一本": 4, "本科·二本": 2, "专科": 1}
    score += edu_bonus.get(state.get("education", "无"), 0)
    flags = state["flags"]
    if flags.get("编制内"):
        score += 4  # 宇宙的尽头
    if flags.get("全款勇士"):
        score += 4
    if flags.get("已婚"):
        score += 2
    if flags.get("有娃"):
        score += 2
    return round(score)


def _highlights(state: dict) -> list[str]:
    """人生走马灯:挑出大事件。"""
    big = [l["text"] for l in state["log"] if l.get("kind") in ("big", "achieve")]
    return big[-8:] if len(big) > 8 else big
