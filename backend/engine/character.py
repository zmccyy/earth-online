"""投胎系统:角色创建、天赋抽卡、重抽玄学。"""
import random

from .content import FLAVOR

ATTR_KEYS = ("health", "intellect", "appearance", "happiness")

ATTR_NAMES = {
    "health": "体质",
    "intellect": "智力",
    "appearance": "颜值",
    "happiness": "快乐",
}

# 家境 = 开局难度(权重抽取)
FAMILY_TIERS = [
    {"id": "penniless", "name": "牛马家庭", "tier": "N", "weight": 38, "money": 0,
     "desc": "开局难度:地狱。父母是零氪玩家,毕业装备全靠自己爆肝。"},
    {"id": "ordinary", "name": "普通家庭", "tier": "R", "weight": 34, "money": 20000,
     "desc": "服务器人数最多的一档,人生任务全部走标准模板。"},
    {"id": "welloff", "name": "小康家庭", "tier": "SR", "weight": 19, "money": 200000,
     "desc": "新手村体验良好,氪金能力有限,买毕业装备还得贷款。"},
    {"id": "whale", "name": "氪金玩家", "tier": "SSR", "weight": 8, "money": 2000000,
     "desc": "开局自带毕业装备,主线一路畅行,评论区一片『慕了』。"},
    {"id": "demolition", "name": "拆迁户", "tier": "UR", "weight": 1, "money": 8000000,
     "desc": "UR级开局!一夜之间完成了其他玩家肝一辈子的毕业任务。"},
]

# 出生地 = 服务器分区
HOMETOWNS = [
    {"id": "village", "name": "乡下农村", "weight": 26,
     "desc": "空气清新,网络延迟高,顶级装备『学历』掉率全靠天赋。",
     "effects": {"health": 6, "happiness": 3}},
    {"id": "county", "name": "十八线小县城", "weight": 28,
     "desc": "节奏慢,加载快,大副本都要坐车去。",
     "effects": {"health": 3, "intellect": 2}},
    {"id": "city2", "name": "二线城市", "weight": 24,
     "desc": "资源尚可,房价副本难度中等,生活副本能刷出小确幸。",
     "effects": {"intellect": 3, "appearance": 2}},
    {"id": "city1", "name": "一线城市", "weight": 16,
     "desc": "资源丰富,房价副本地狱级,地铁跑图每日两小时。",
     "effects": {"intellect": 5, "happiness": -4, "money": 50000}},
    {"id": "megacity", "name": "超一线卷都", "weight": 6,
     "desc": "内卷主服!天梯排位从幼儿园开始,快乐值持续掉血。",
     "effects": {"intellect": 8, "happiness": -8, "money": 100000}},
]

SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "马", "朱", "胡", "郭", "何", "林", "罗", "郑"]
GIVEN_M = ["伟", "强", "磊", "军", "洋", "勇", "杰", "涛", "宇", "浩", "子轩", "浩然", "一鸣", "梓豪", "思远"]
GIVEN_F = ["芳", "娜", "敏", "静", "丽", "婷", "雪", "倩", "雨桐", "欣怡", "梓涵", "梦琪", "语嫣"]

# 天赋称号 = 初始属性的“策划点评”
def _talent_title(attrs: dict) -> str:
    total = sum(attrs.values())
    if attrs["appearance"] >= 85:
        return "天赋异禀·颜值挂(策划私人恩怨)"
    if attrs["intellect"] >= 85:
        return "天生慧根·学神胚子(主线任务加速包)"
    if attrs["health"] >= 85:
        return "钢筋铁骨·牛马圣体(团本强度拉满)"
    if total >= 300:
        return "天选之人·六边形战士"
    if total <= 160:
        return "开局困难模式·策划没有心"
    return "普通玩家·属性随机分配"


def roll_family(rng: random.Random) -> dict:
    tiers = FAMILY_TIERS
    total = sum(t["weight"] for t in tiers)
    pick = rng.uniform(0, total)
    acc = 0
    for t in tiers:
        acc += t["weight"]
        if pick <= acc:
            return dict(t)
    return dict(tiers[0])


def roll_hometown(rng: random.Random) -> dict:
    total = sum(t["weight"] for t in HOMETOWNS)
    pick = rng.uniform(0, total)
    acc = 0
    for t in HOMETOWNS:
        acc += t["weight"]
        if pick <= acc:
            return dict(t)
    return dict(HOMETOWNS[0])


def roll_character(rng: random.Random, name: str | None = None) -> dict:
    """投胎一次:生成姓名、性别、家境、出生地、初始属性。返回草稿状态。"""
    gender = rng.choice(["男", "女"])
    if name is None:
        given = rng.choice(GIVEN_M if gender == "男" else GIVEN_F)
        name = rng.choice(SURNAMES) + given
    attrs = {k: rng.randint(20, 80) for k in ATTR_KEYS}
    family = roll_family(rng)
    hometown = roll_hometown(rng)
    # 出生地与家境修正
    for k, v in hometown["effects"].items():
        if k in attrs:
            attrs[k] += v
        elif k == "money":
            family["money"] += v
    attrs = {k: max(5, min(95, v)) for k, v in attrs.items()}
    return {
        "name": name,
        "gender": gender,
        "attrs": attrs,
        "family": family,
        "hometown": hometown,
        "talent": _talent_title(attrs),
        "rerolls_left": FLAVOR.get("reroll_limit", 2),
    }


def reroll(state: dict, rng: random.Random) -> dict:
    """重抽天赋(消耗玄学次数):保留姓名与家境,重摇属性与出生地。"""
    old = state
    attrs = {k: rng.randint(20, 80) for k in ATTR_KEYS}
    hometown = roll_hometown(rng)
    for k, v in hometown["effects"].items():
        if k in attrs:
            attrs[k] += v
    old["attrs"] = {k: max(5, min(95, v)) for k, v in attrs.items()}
    old["hometown"] = hometown
    old["talent"] = _talent_title(old["attrs"])
    old["rerolls_left"] -= 1
    return old
