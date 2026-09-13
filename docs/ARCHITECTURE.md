# 《地球Online》架构文档

> 人生是一款强制登录、无法退游、不支持存档的 MMORPG。本文档描述这个"游戏服务器"的实现。

## 1. 顶层决策与备选方案对比

| 方案 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- |
| 纯 Python 终端游戏(旧版) | 零依赖 | 表现力差、测试难、玩法深度受限 | 弃 |
| Vite + React + Node 全栈 | 生态丰富 | 构建链重、迭代慢、对单机游戏过度设计 | 弃 |
| **FastAPI + 原生 ES Modules(采用)** | 无构建、迭代快、引擎可独立单测、契约清晰 | 前端无框架化组织(以模块约定弥补) | ✅ |

交叉验证要点:
- **引擎与框架解耦**:`backend/engine/` 不 import FastAPI,所有函数接收 `state + rng`,可用纯 pytest 覆盖,也方便未来换 Web 框架或移植端侧。
- **内容数据驱动**:事件/成就/文案全部在 `backend/content/*.json`,加内容不改代码。引擎只实现通用机制(条件、权重、效果、结算)。
- **服务端权威**:所有数值结算在服务端,前端只渲染。防作弊无意义(单机),但保证了数据一致性,并天然支持未来多人化。
- **内存会话**:单机本地游戏无需持久化;`session.py` 封装存储接口,替换为 Redis/DB 不影响调用方。

## 2. 数据流(一回合的生命周期)

```
前端(js/main.js)                API(api.py)               引擎(engine/)
  ▶ 活过这一年  ──POST /advance──▶ 校验状态/pending ──────▶ life.advance_year()
                                                          1. age+=1 阶段判定
                                                          2. passive_year(成长/收支/老化)
                                                          3. death_check(死亡判定)
                                                          4. pick_event(里程碑→随机池)
                                                          5. clamp + 成就扫描
  ◀ {state, logs, event} ──────── JSON ◀──────────────────┘
  事件卡渲染 → 玩家选择
  ▶ POST /choose ───────────────▶ resolve_choice → effects 应用 → 成就 → 特殊结局
```

## 3. 核心机制设计

### 3.1 条件引擎(`events.check_conditions`)
所有事件/选项共用一个 AND 组合条件 DSL:`min_age/max_age、stages、flags_any/all/none、attr_min/max、money_min/max、has_job、has_spouse、education_in、chance、graduate_reached`。新增条件类型只需扩展一处。

### 3.2 事件体系
- **里程碑事件**(`milestone: true`):确定性人生节点(中考/高考/找工作/相亲/买房/生娃/中年危机/退休),每个一生一次。
- **随机事件**:85% 年份触发,条件过滤后按 `weight` 加权抽取,默认 `once`。
- **效果 DSL**(`apply_effects`):属性增量、money、flags_add/remove、set_job/salary_mult、match_spouse、divorce、add_child、mortgage、set_education、graduate_age、set_flag_value、roll_gaokao、grant_achievement、ending(特殊结局)。

### 3.3 高考副本
选项携带 `roll_gaokao.effort`(努力系数),分数 = 智力×6×effort + 随机发挥,映射到学历档位(985/211/一本/二本/专科),决定 `graduate_age` 与后续职业选项池。

### 3.4 死亡与结算
年度死亡率 = 年龄基础率 + 体质修正 + 危险flag(996战士)。死亡触发 `rating.build_summary`:
评分 = 存活年限(≤55) + 财富对数(≤20) + 面板均值(≤30) + 成就(≤12) + 学历(≤8) + 旗标加成,映射到 SSS天选剧本→D删号重练 七档。特殊结局 `ending: awaken`(灵魂觉醒)直接进入"通关者"真结局。

### 3.5 前端结构
无框架 ES Modules:`api.js`(唯一通信层)/ `main.js`(屏幕状态机:标题→投胎→人生→结算,图鉴弹窗)。成就图鉴以 localStorage 跨局持久化(`eol_achievements`)。

## 4. 稳定性与扩展点
- 所有属性增量经 `clamp_state` 限幅(0-100),金钱可为负(负债flag)。
- 年龄硬上限 120 岁,必然死亡,流程无死锁;pending 事件未决时 advance 被拒(409),API 层有完整 400/404/409 语义。
- 扩展新内容:仅改 JSON;扩展新机制(新条件/新效果):engine 单点扩展;扩展多人:session 换 DB + WebSocket 推送。
- 测试:16 个用例覆盖引擎纯逻辑、API 契约、内容一致性(事件引用的成就必须存在等)。

## 5. 已知折中
- 会话在内存中,重启服务器即"全服停机维护"(单机可接受)。
- 随机事件每次 1 个,未做事件链(后续可加 `force_event` 字段)。
- 数值平衡以"梗感优先",非严谨模拟。
