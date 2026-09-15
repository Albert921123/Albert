# generate-daily-industry-brief · 知讯日报 Skill

## v1.42 单一总控、检索原始回执与确定性渲染

正式实时版与补发版统一从 `scripts/run_pipeline.py` 进入。总控程序依次绑定完整读取回执、不可变运行计划、板块画像、检索工作状态、候选台账、来源注册表、编辑模型、锁定模板和最终 HTML；任一文件变化都会使后续授权或交付失败，不能跳过中间环节直接生成页面。

每次宿主搜索都必须先保存版本化的原始结果 JSON，再用 `record-query --raw-results` 入账。程序从原始结果计算候选数并保存 SHA-256、实际工具名、调用时间与宿主调用标识；宿主不暴露调用标识时必须明确记录原因。候选的来源类别和域名还会通过 `references/source-registry.json` 核验，Agent 自己写“官方来源”不能替代域名证据。

内容写作先进入结构化编辑模型：每张卡必须有主体、带日期动作、影响对象、至少两项决策事实，以及“发生了什么、为何值得关注、行动/风险点、研判”四段实质内容。`scripts/render_brief.py` 只从通过校验的模型确定性生成既有 HTML 版式；今日重点与三段式“今日推荐关注”只能引用已核验主窗口事件，三段为并列事实，不得强写因果。最终只有 `finalize` 重新通过全部硬门后才签发正式交付回执。

## v1.41 全板块“海外同深度”检索硬约束

海外板块经过多轮推敲形成的检索方式现在成为所有标准、自定义和新增板块的统一底线。每个板块先绑定经校验的板块画像，再分别记录主体类型、来源类型和事件类型；不能因为用户没有逐板块追问、已找到第一条官方信息或组合搜索返回少量结果，就提前停止。

执行程序会拒绝以下情况：未绑定板块画像、来源族未达计划地板、主体或事件覆盖不足、低于目标时没有更换词组和来源族补检、候选仍未逐条决定、工作状态与台账不一致。普通日期版 HTML 的结构校验会自动再运行严格台账校验，只有收录项的简化台账不能再绕过正式交付门。真实只有一条合格资讯时仍保留一条；新增规则约束的是检索深度，不是强行凑数。

## v1.40 检索执行引擎与正式交付门

正式实时版和补发版现在必须由 `scripts/run_pipeline.py authorize-render` 取得授权，由 `scripts/run_pipeline.py render` 生成页面，再由 `scripts/run_pipeline.py finalize` 完成交付。底层 `run_brief.py` 不再作为 Agent 可自由拼接的主入口。程序拒绝未完成的检索循环，并用 SHA-256 绑定运行状态、运行计划、检索台账、来源注册表、编辑模型、模板和 HTML；只通过 HTML 结构检查不再等于完成。

定时或手动运行必须通过 `init → next → record-query/record-decision → close-section → seal-retrieval → authorize-render → render → finalize` 循环。代码按广度优先顺序返回下一个板块和检索通道；只要仍有未检索通道、未决定候选或未关闭板块，就会拒绝封存和渲染。

每板块2/3条是检索比较目标，不是输出配额。真实只有1条时正常保留，但台账必须证明四条检索通道、补充检索、候选池耗尽以及其他候选未入选的具体原因；不得为了凑数加入旧闻、弱相关或重复资讯。

> 一个可以安装到多种 AI Agent 的中文行业资讯技能：先按经营岗、生产岗或研究岗生成不同的选择场景与 1–10 板块相关度，再按用户选择的板块检索近 24 小时信息；空板块可回补 24—48 小时，联网模式仍无合格事件时呈现透明原因卡，只有完全离线的 Mode D 才使用非新闻基线追踪卡。最终生成带来源链接、导航和关键词搜索的独立 HTML 日报。宽口径板块采用“字段优先、建筑关联加权”；同一事件只归入相关度最高的一个板块，避免重复。

**它不是一份固定新闻模板，也不是模型凭记忆拼出的摘要，而是一套“订阅配置 + 分板块检索 + 来源核验 + HTML 交付 + 定时校验”工作流。**

从 v1.38.4 起，选择器提交与定时任务部署也形成不可跳过的闭环：提交会写入待部署文件，但只有宿主已原地更新任务、回读并核验排期后，`pending_deployment.py` 才能将该文件确认完成；否则始终保留为“已保存，尚未部署”，下一次调用从该文件续跑，不会遗失用户修改的时间或板块。订阅的唯一时间基准是北京时间（Asia/Shanghai）：用户填写 13:40，配置、任务列表、任务提示、补发边界、日报日期和交付回执都必须写作并理解为北京时间 13:40；没有可读取的带时区 `nextRunAt` 时，不能依据相对倒计时擅自换算成 UTC 或挪动开始日期。Codex 原生即时创建若拒绝带 `DTSTART` 的规则，技能会用同一北京时间小时和分钟创建唯一任务，而不是改写成 UTC 小时。每次生成仍先创建一份可恢复的全板块运行计划，再进入持久化状态：完整读取、能力预检、候选发现、原页核验、全板块台账、HTML 渲染、校验和交付必须依次完成。计划为每个板块固定字段、主体、官方记录和业务交集四条检索通道，并记录候选审查深度；不能只查到一条就跳到 HTML。每个板块关闭时必须写入唯一的最终结果（完整、观察、扩展、业务观察、已核查为空或受限）。当一个板块已完成四条检索通道、两类独立来源和三条已打开候选，且没有可入选的独立资讯时，必须关闭为“已核查为空”或“受限”，在 HTML 中呈现简洁原因卡；不得因达不到展示候选数而无限停在候选阶段。脚本会逐板块核对四路查询证据，拒绝用组合搜索代替 25 个板块的独立检索；全板块台账与精确时窗未通过前不能进入 HTML，日期版文件也不能使用 `--allow-placeholders`。交付命令会自行重跑台账、时窗、HTML、编辑质量和版式基线校验，不能用手填通过状态绕开。仅登录、授权或用户控制能力缺失才显示“需人工处理”；普通中断和未完成检索明确显示“待续跑”，并显示保存的精确恢复动作。下一次调用必须从同一计划和同一状态恢复，不能新建状态绕过。没有真实、可观察的宿主任务时，Skill 不会把它描述为“后台仍在生成”。

---

## 解决什么问题

领导每日获取行业信息时，常见的几个问题是：

- **内容不聚焦**：日报包含很多板块，但每个人真正关心的方向不同
- **信息不够新**：把近一周旧闻混进“今日资讯”，无法反映最新变化
- **来源不可核验**：只有摘要，没有原始来源、发布时间或可点击链接
- **换一个 Agent 就失效**：交互界面、搜索、定时和检索能力依赖某个平台
- **定时设置看似成功**：显示了时间，却没有核对真实 `nextRunAt` 和后台循环规则

这个 Skill 会先让用户选择岗位画像，再选择标准板块、添加自定义关注方向、设置频率和上海时间，并按同一份配置持续生成日报。每个自定义兴趣都会成为独立板块，不会被合并或丢弃。

---

## 快速开始

### 安装

这是一个标准的 Agent Skill 目录。**必须保留整个 `generate-daily-industry-brief` 文件夹及其内部结构**，不能只复制 `SKILL.md`。

常见安装位置：

| Agent / 运行方式 | 建议目录 |
|---|---|
| 通用 Agent Skills | `~/.agents/skills/generate-daily-industry-brief` |
| OpenAI Codex | `~/.codex/skills/generate-daily-industry-brief` |
| Claude Code | `~/.claude/skills/generate-daily-industry-brief` |
| OpenClaw | `~/.openclaw/skills/generate-daily-industry-brief` |
| Gemini CLI | `~/.gemini/skills/generate-daily-industry-brief` |
| WorkBuddy、Kimi Code 等 | 放入该 Agent 实际使用的持久化 skills 目录 |

收到 ZIP 后，应先完整解压，再把整个目录放入对应位置。聊天附件缓存或临时解压目录不等于安装完成。

安装后在 Skill 目录中运行：

```bash
python scripts/verify_install.py --json
```

出现 `"ok": true` 才表示核心文件完整。脚本兼容 Python 3.6 及以上版本，无第三方 Python 包依赖。

### 触发

让用户直接说（任意一句）：

```text
调用知讯日报
打开知讯日报设置
修改日报板块
把日报时间改到每天 08:30
补发今天的知讯日报
生成今天的知讯日报
```

在支持显式 Skill 名称的 Agent 中，也可以使用：

```text
$generate-daily-industry-brief
```

裸调用时，Skill 会优先打开完整交互选择器；没有可访问图形界面的云服务器、SSH、容器或无头 Agent 会自动改用完整编号文字选择器。

---

## 可选板块

内置 16 个标准板块，全部可以独立选择或取消：

| 编号 | 板块 | 主要关注方向 |
|---|---|---|
| 01 | 数科 | 金融服务及其数据科技平台、供应链金融、保理、融资、结算、信用与风控 |
| 02 | 寻源 | 招标、采购需求、供应商征集、集采与框架协议 |
| 03 | 撮合 | 产业合作、供需对接、联合项目、签约与资源互补 |
| 04 | 用工 | 建筑人才政策、招聘、劳务市场、紧缺岗位与薪酬趋势 |
| 05 | 海外 | 出海订单、国际工程、市场准入、地区政策与风险 |
| 06 | 高管观点 | 主管部门领导、专家、院士、企业高管及建筑软件生态管理者观点 |
| 07 | 企业经营 | 建筑央国企、施工企业、设计院和产业链公司的订单、业绩与战略 |
| 08 | 投融资 | 上市公司公告、并购重组、股权融资、产业基金与重大投资 |
| 09 | AI | 模型、智能体、算法、算力、AI 治理与产业落地 |
| 10 | 建筑软件 | BIM、造价、项目管理、协同设计、企业管理与软件生态 |
| 11 | 建筑科技 | 智能建造、建筑机器人、装配式、新材料与工程工法 |
| 12 | 政府宏观 | 国务院、中央部委及地方政府的政策和公共项目动态 |
| 13 | 行业数据 | 投资、开工、订单、产值、价格、PMI 与景气指标 |
| 14 | 标准规范 | 国家、行业、地方和团体标准及计价、审查、验收规则 |
| 15 | 绿色低碳 | 绿色建筑、节能改造、双碳、绿色建材与建筑碳排放 |
| 16 | 拓展阅读 | 权威研究、白皮书、深度报告与趋势分析 |

用户还可以输入最多 20 个自定义关注方向，例如“城市更新”“专项债”“半导体”“游戏”或“外贸”。每个自定义方向都会被单独检索，并作为每日 HTML 中的独立板块输出。

## 岗位画像与相关度

首次配置或后续修改时可选三种预设；用户仍可勾选任意板块、手工调整任一分值，或选“自定义”。分值只决定检索深度、来源优先级和排版顺序，不会排除用户已选板块。

| 画像 | 默认重点 | 高分来源方向 |
|---|---|---|
| 经营岗 | 企业经营、投融资、高管观点 | 公司 IR、交易所披露、业绩会、产业基金、监管与招采平台 |
| 生产岗 | 寻源、用工、撮合、建筑科技 | 公共资源/采购平台、业主与央国企采购、人社与项目公告 |
| 研究岗 | 政府宏观、标准规范、行业数据 | 国务院和部委、地方政府、标准化机构、统计部门与行业协会 |

`9–10` 分执行四条检索路径并优先争取 2–3 条独立卡；`7–8` 分执行三条路径；`4–6` 分至少执行字段和官方记录两条路径；低分但已选择的板块仍会独立检索。完整评分与具体来源在 [`references/role-profiles.md`](references/role-profiles.md)。

---

## 工作原理

### 1. 选择并保存订阅

```text
选择标准板块
    ↓
添加自定义关注方向
    ↓
设置每天/工作日、上海时间和接收位置
    ↓
保存配置并创建或更新原任务
```

- 支持首次创建，也支持后续重新打开同一界面修改板块、兴趣、频率和时间
- 使用稳定的 `subscription_id` 原地更新自动化，不重复创建任务
- 交互界面不可用时，完整列出 01—16 的文字选项，不用用户凭记忆输入板块名称

### 2. 检索与核验

每次运行以真实运行时刻为截止点：

运行前必须先校验并完整读取技能包，生成本次独立的读取回执；未完成读取不得开始检索或生成 HTML。

1. 先检索此前滚动 24 小时的信息
2. 只有某个板块确认 24 小时内没有合格内容时，才检索此前 24—48 小时区段
3. 48 小时补充必须明确标记，不能扩展到 72 小时或近一周
4. 优先政府、监管、交易所、招采平台、公司官网、投资者关系和官方活动实录等一手来源
5. 先广度覆盖全部板块，再核验候选，避免一个板块耗尽全部检索预算
6. 每板块最多 20 条；每板块以 2 条（高相关板块 3 条）作为**候选筛选深度目标**，而非输出配额。普通板块的台账至少要有 4 个真实候选、2 个独立来源族；高相关、7–10 分或宽泛自定义板块至少要有 6 个真实候选、3 个独立来源族。必须先初筛完必经来源路径中发现的全部候选，再逐条打开核验所有通过初筛的候选；后续候选只有通过时效、来源、相关性与去重核验时才加入。高相关板块还必须比较宏观/行业来源与企业/项目来源，不能以一条项目公告替代整个板块。仅在候选池耗尽、其余候选均有具体排除原因，或达到该板块条数上限时才能结束，不能在首条或第 3 条结果后停止；若只有 1 条合格，允许只输出 1 条，但必须完成上述候选深度并记录低于目标的原因。台账数字、HTML 卡片数与排除记录不一致时，校验将失败，不能交付为正式日报。
7. 正文开头将已核验卡组织为 2–3 条“今日推荐关注”：政策/制度、行业/资本或应用、企业/项目事实以并列卡呈现，只用于帮助理解同一经营议题，不表示因果、时间推进或必然传导。缺少某层时不补造、不写“待补”；不额外生成管理层动作清单。
8. 每个已选板块都不留视觉空白：实时正式资讯 → 48 小时补充 → 有明确业务关联的扩展相关资讯 → 业务观察。只有 Mode D（无可用实时网络及验证输入）可使用明确标注为“非当日新闻”的基线追踪卡；联网检索未完成时不得用基线卡替代检索，也不得交付半成品日报。

Skill 会根据 Agent 的真实能力选择检索模式：

| 模式 | 可用能力 | 处理方式 |
|---|---|---|
| A | 搜索 + 网页读取 | 搜索负责发现，原始网页负责核验 |
| B1 | 可操作的个人云电脑自动化 | 在云端浏览器检索、打开原文并核验；yz claw 暴露 `yunzhu-browser-automation` 时必须先探测 |
| B2 | 无 B1，但可直接访问网页、RSS、站内检索或普通浏览器 | 从官方来源列表和站内入口逐一发现 |
| C | 无网页能力，但可读取已验证结构化数据 | 校验外部 JSON 数据源后生成 |
| D | 只有离线或缓存材料 | 明确标注“非实时/检索受限”，不冒充完整日报 |

`WebSearch` 和 `WebFetch` 不是联网检索的前提。Skill 会先读取宿主实际暴露的工具和连接器：若有搜索 API（名称可能是 `webSearch`、`search_web`、`internet_search`、`browser.search`、知识/新闻搜索，或已配置的 Bing/Google/SerpAPI 类连接器），优先用其中已验证可用的一项做广度发现；不猜测未暴露的接口、密钥或工具名。若没有可用搜索 API，只要 Agent 能通过浏览器、命令行 HTTP（例如 `curl`、PowerShell、Node 或 Python 标准库）、RSS/站点地图、官网栏目页、公开 API、站内搜索或浏览器中的搜索页访问公共网页，Skill 就必须走 Mode A/B 自主检索；不会因为“没有现成 API 或 RSS 聚合器”要求用户先制作 JSON feed。JSON feed 仅用于增强覆盖或在所有直接联网路径均不可用时兜底。只有这些路径均经预检不可用且没有 API Key 时，才会解释原因、打开 Tavily 登录页、指导创建 Key，并以本地遮蔽输入框完成一次性备用启用。完整规则见 [`references/network-retrieval-playbook.md`](references/network-retrieval-playbook.md)。

个人云电脑分为 **B1**，普通浏览器和直连网页分为 **B2**。若 yz claw 的工具列表实际暴露 `yunzhu-browser-automation`，Skill 必须先用它打开一个板块相关官方页面和搜索/站内搜索页面，再记录 `working`、`needs-auth`、`view-only`、`disconnected`、`denied`、`failed` 或 `skipped-unavailable`；不能等用户提醒才发现云电脑。B1 可用时由 Agent 直接在云端浏览器完成关键词搜索、打开原文、核验日期和保存来源链接；仅当 B1 不可用或某页面操作失败时才转 B2。不会仅凭 yz claw 名称假设该能力存在，也不应要求用户截图或复制搜索结果。

没有实时搜索、网页读取或当期已验证数据源时，Skill 不会用模型记忆编造今日新闻；会改为可读的连续追踪版，逐板块说明能力限制与权威入口。Python 也是可选项：没有 Python 时可照常配置、生成 HTML，并在审计中标记为人工校验。

### 3. 生成可独立打开的 HTML

日报使用 `assets/daily-brief-template.html` 生成，包含：

- 桌面端左侧板块导航
- 手机端横向板块标签
- 固定顶部信息区和独立内容滚动区
- 标题、正文、来源和业务关键词搜索及高亮；加大搜索说明文字并保留舒适的顶部间距
- 点击来源后在新窗口打开原始网页
- 重要信息摘要、业务类型提示与由并列来源事实构成的今日推荐关注
- 响应式排版，兼容桌面与手机浏览
- 跨板块完整内容卡，避免自定义板块“拿走”标准板块内容
- 逐候选检索台账，记录收录与排除原因

最终文件名为：

```text
daily-industry-brief-YYYY-MM-DD.html
retrieval-ledger-YYYY-MM-DD.json
```

正式渲染和交付必须通过：

```bash
python scripts/run_pipeline.py authorize-render --state pipeline-state.json --work-state retrieval-work-state.json --ledger retrieval-ledger-YYYY-MM-DD.json --model brief-model-YYYY-MM-DD.json --registry references/source-registry.json --output render-authorization.json
# 使用锁定模板生成 daily-industry-brief-YYYY-MM-DD.html
python scripts/run_pipeline.py render --state pipeline-state.json --work-state retrieval-work-state.json --authorization render-authorization.json --ledger retrieval-ledger-YYYY-MM-DD.json --model brief-model-YYYY-MM-DD.json --registry references/source-registry.json --template assets/daily-brief-template.html --output daily-industry-brief-YYYY-MM-DD.html

python scripts/run_pipeline.py finalize --state pipeline-state.json --work-state retrieval-work-state.json --authorization render-authorization.json --ledger retrieval-ledger-YYYY-MM-DD.json --artifact daily-industry-brief-YYYY-MM-DD.html --template assets/daily-brief-template.html --output delivery-receipt.json
python scripts/mark_success.py --subscription-id primary --timezone Asia/Shanghai --state-dir .zhixun-state --html-file daily-industry-brief-YYYY-MM-DD.html --ledger-file retrieval-ledger-YYYY-MM-DD.json
```

只有 `finalize` 生成 `all_gates_passed: true` 的正式交付回执后才能运行成功标记；任一验证失败时不能把该次运行标记为成功。

### 4. 定时和补发

Skill 可以帮助 Agent 创建、更新和校验定时任务，但 **Skill 文件本身不是云端调度器**。

- 所选时间固定按 `Asia/Shanghai` 解释
- 创建或改时后同时校验真实 `nextRunAt`、后台最终持久化循环规则及其时区证据；仅有 `Active`、任务名称或裸 RRULE 不能视为定时成功。若宿主无法返回时区和下一次执行时间，任务只能标记为“调度未核验”，每次唤醒仍须优先执行“最新到期一期”补发检查。
- 电脑关机时，本地 Agent 不能按时运行
- 要保证关机后仍准时生成，需要 WorkBuddy Cloud、常驻云服务器、系统任务计划或 cron 等真正持续运行的调度器
- 支持恢复/启动触发的宿主，会按订阅 ID、最新到期上海周期和配置指纹去重补发：未到当天推送时间时补上一期，已过当天推送时间时补当期；即使停了多天也只补最新一期，不逐期回补
- 宿主没有恢复触发能力时，用户仍可说“补发知讯日报”手动执行同一检查

---

## 实际效果

一套安装包可以服务不同领导的不同关注组合：

- **工程与采购负责人**：寻源、撮合、用工、标准规范
- **企业经营负责人**：企业经营、投融资、高管观点、行业数据
- **数字化负责人**：数科、AI、建筑软件、建筑科技
- **综合管理负责人**：政府宏观、海外、绿色低碳、拓展阅读
- **个性化订阅**：在上述任意组合之外，加入房地产、城市更新、储能、半导体、游戏、外贸等独立板块

设置修改后仍使用同一个 `subscription_id` 更新原任务，避免出现多个时间不同、内容重复的日报自动化。

---

## 文件结构

```text
generate-daily-industry-brief/
├── README.md                         # 安装、调用、工作原理和边界说明
├── SKILL.md                          # 主入口：交互、检索、生成、调度和补发规则
├── manifest.json                     # 版本、兼容性、安装目标和必需文件
├── agents/
│   └── openai.yaml                   # OpenAI/Codex 展示元数据
├── assets/
│   ├── browser-subscription-selector.html
│   ├── codex-subscription-selector.html
│   └── daily-brief-template.html
├── entrypoints/
│   └── 通用调用提示词.txt
├── references/
│   ├── topics.md                     # 标准板块定义和分类规则
│   ├── section-source-catalog.md     # 分板块来源目录
│   ├── discovery-source-ladder.md    # 来源发现梯级
│   ├── retrieval-routing.md          # 检索路由
│   ├── retrieval-audit.md            # 覆盖、核验和排除审计
│   ├── runtime-compatibility.md       # 多 Agent 能力检测与降级策略
│   ├── network-retrieval-playbook.md  # 无 WebSearch 时的联网检索与补检规则
│   └── news-input-schema.json        # 外部结构化新闻数据格式
└── scripts/
    ├── launch_selector.py            # 本地交互选择器桥接
    ├── verify_install.py             # 安装完整性检查
    ├── verify_schedule.py            # 时区、首跑和循环规则检查
    ├── validate_html.py              # HTML 功能检查
    ├── validate_news_input.py        # 外部新闻输入检查
    ├── validate_retrieval_ledger.py  # 逐候选检索台账检查
    ├── probe_network.py               # 可选的只读联网能力探测
    ├── check_catchup.py              # 最新到期一期漏跑判断
    └── mark_success.py               # 成功标记与去重
```

Reference 文件按任务阶段加载：选择板块时不需要一次性读取全部检索资料；开始生成日报后，再按所选板块和运行环境读取相关来源、路由与审计规则。

---

## 能力边界

- **不保证所有 Agent 都自带网页搜索**：Skill 会探测真实能力，不能通过安装包凭空增加宿主没有的搜索工具
- **不使用模型记忆替代实时新闻**：缺少实时来源时会降级或明确报告受限
- **不把交互界面提交等同于定时成功**：必须拿到任务标识、真实下次运行时间和持久化循环规则并完成校验
- **不保证关机状态下运行本地任务**：精确定时需要云端或常驻调度环境
- **不编造来源、日期和事件**：候选信息必须具备可核验的原始来源和时间
- **不为了凑数量放宽到近一周**：24 小时主窗口、空板块 48 小时补充是时间上限
- **不替代专业决策**：日报用于信息筛选和管理研判，重大投资、合规、政策与经营决策仍需负责人复核

---

## 版本与兼容性

- Skill 版本：`1.42.0`
- 核心规则版本：`4.88`
- Python：`3.6+`
- 输出语言：`zh-CN`
- 默认时区：`Asia/Shanghai`
- 默认输出：独立 HTML5 文件

版本以 `manifest.json` 为准。

## 说明

本 README 的结构参考了 Qrange-public-skills 中 `methodology-business-analysis` Skill 的公开说明方式；本 Skill 的业务规则、代码、模板和兼容性说明均来自当前 `generate-daily-industry-brief` 包本身。
