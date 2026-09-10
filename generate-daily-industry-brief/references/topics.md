# Topic reference

Use only the rows matching the selected topic IDs. Every topic uses the rolling 24-hour primary window first. A topic confirmed empty in that window may use the separate 24-to-48-hour fallback segment, with every fallback item visibly labeled.

`custom_interests` are additional dynamic topics outside this table. Use each exact user-entered phrase as a separate section title, derive broad field cues plus business-intersection cues, and apply the same 24-hour-primary/48-hour-fallback and source-quality rules. Do not merge custom interests into standard topics or drop them because they are not listed below. The exact custom field is the primary scope; `industry_scope` improves ranking but is not a mandatory admission filter unless the user explicitly requests a narrower interpretation.

## Three-level admission policy

Classify every fresh verified candidate from the perspective of each selected section:

- **A / 直接相关**: the event's core subject belongs to the section. Render a full section story.
- **B / 产业链相关**: the event concerns a regulator, customer, supplier, infrastructure, capital or adoption path with a clear section-level business implication. Render a full section story with the visible label `产业链关联`.
- **C / 行业影响**: the event is outside the core field but has a direct, decision-useful macro impact on the section. Use at most one C-level full card when the row has no A/B story, and label it `行业影响`.
- **D / 弱关联**: relevance requires speculative or multi-hop inference. Exclude it.

For broad sections (`fintech`, `overseas`, `leadership`, `enterprise`, `capital`, `digital`, `government`, `industry-data`, `green`, `extended`) and every broad custom interest, field relevance is sufficient for A-level admission. Do not require construction words or an AEC customer. Keep construction-only admission for inherently AEC rows such as `sourcing`, `employment`, `informatization` and `construction-tech`.

| ID | 中文名 | Include | Query cues | Lookback |
|---|---|---|---|---|
| `fintech` | 数科 | 支撑金融服务、企业金融和产业金融的数据科技平台，包括供应链金融、保理、融资、结算、租赁、信用、可信数据与风控，以及客户落地、合作、经营和监管动态；建筑及产业链案例优先，但不是唯一合格范围 | 供应链金融；产业金融；数字金融；保理；应收账款；电子债权；确权；可信数据；融资平台；金融科技；企业金融；数据科技 | strict 24h |
| `sourcing` | 寻源 | 建筑工程招标、采购需求、供应商征集、品类与价格线索 | 招标公告；采购需求；供应商征集；集采；框架协议 | strict 24h |
| `matching` | 撮合 | 产业合作、供需对接、联合项目、签约与资源互补 | 战略合作；项目对接；供需撮合；联合解决方案；签约 | strict 24h |
| `employment` | 用工 | 建筑人才政策、招聘与劳务需求、工程和数字化岗位、紧缺技能、工资社保、安全、裁员与职业资格 | 建筑人才；招聘需求；用工；劳务市场；项目经理；工程师；BIM；数字人才；薪酬；裁员；职业资格 | strict 24h |
| `overseas` | 海外 | 国际工程与地产、建筑材料和工程设备出口、海外设厂/园区、跨境并购、市场准入、贸易与合规风险 | 海外项目；中标；出海；出口；海外设厂；市场准入；国际工程；属地化；贸易政策；跨境并购 | strict 24h |
| `leadership` | 高管观点 | 主管部门、协会、院士，以及建筑、地产、工程科技、数科、能源、基础设施和建筑软件生态管理者的公开观点 | 演讲；致辞；访谈；业绩会；论坛；董事长；总裁；CEO；总工程师；首席科学家 | strict 24h |
| `enterprise` | 企业经营 | 建筑央国企、地产、施工、设计院、建材、工程机械、建筑软件、产业金融及其他产业链公司的订单、业绩、组织与战略 | 新签合同；经营业绩；组织调整；战略发布；业绩说明会；现金流；回款；在手订单 | strict 24h |
| `capital` | 投融资 | 上市公司公告、并购重组、股权与债务融资、产业基金、项目融资、REITs、重大投资与资本开支 | 并购；重组；融资；债券；产业基金；REITs；定增；股权投资；资本开支；上市公司公告 | strict 24h |
| `digital` | AI | AI模型、智能体、算法产品、算力与数据基础设施、AI治理及产业落地；建筑AI优先，但选中本板块时通用AI重大动态也可收录 | AI模型；智能体；生成式AI；AIDC；AI治理；工业AI；具身智能；建筑AI；工程大模型；AI设计；AI审图；AI造价；施工AI | strict 24h |
| `informatization` | 建筑软件 | BIM、造价、项目管理、协同设计、CDE、数字孪生、GIS、ERP、资产/设施管理、工业软件、数据平台、信创与工程数字化生态动态 | BIM；造价软件；项目管理；协同设计；CDE；数字孪生；GIS；ERP；工业软件；数据平台；AI Agent；信创；智慧工地软件 | strict 24h + expanded |
| `construction-tech` | 建筑科技 | 智能建造、建筑机器人、装配式、工业化、新材料与工程工法 | 智能建造；建筑机器人；装配式；模块化建筑；新材料；工程技术 | strict 24h |
| `government` | 政府宏观 | 国务院、中央部委及地方政府发布的宏观、财政、金融、投资、产业、科技、土地、能源、交通、监管与公共项目政策；住建只是来源之一 | 国务院；政策发布；发改；财政；央行；金融监管；工信；自然资源；交通；商务；市场监管；统计；能源；国资；省政府；市政府；住建；基础设施 | strict 24h |
| `industry-data` | 行业数据 | 建筑及相关产业的投资、开工、销售、订单、产值、融资、价格、PMI、产能与景气指标，包括地产、基建、建材和工程机械 | 建筑业产值；固定资产投资；房地产；基建；新开工；订单；PMI；钢铁；水泥；玻璃；工程机械；融资；景气指数 | strict 24h |
| `standards` | 标准规范 | 国家、行业、地方和团体标准，以及立项、征求意见、实施通知、技术导则、认证规则、工程计价/审查/验收执行细则 | 标准发布；规范修订；征求意见；立项；实施通知；技术导则；认证规则；工程计价；施工验收；审图 | strict 24h + expanded |
| `green` | 绿色低碳 | 绿色建筑、节能改造、绿色建材、碳市场和核算、绿电交易、光伏储能、能效管理、零碳园区、循环经济与ESG经营披露 | 绿色建筑；近零能耗；节能改造；双碳；绿色建材；碳市场；绿电；光伏；储能；能效；ESG；零碳园区；循环经济 | strict 24h + expanded |
| `extended` | 拓展阅读 | 新发布的权威研究、白皮书、深度报告、官方统计解读、协会洞察、公开券商研究和趋势分析 | 研究报告；白皮书；行业展望；专题研究；官方统计；协会报告；券商研报；案例复盘 | strict 24h + business-observation |

## Classification rules

- Put an item in the section where its primary business value lies.
- Use `leadership` only when the value comes from a named person's argument, forecast, decision, or management signal. Put ordinary company news in `enterprise`.
- Classify a government procurement notice as `sourcing` when the opportunity is the main value; use `government` when the policy signal is the main value.
- Put B2B financial-service, industrial-finance and supporting data-tech platform news in `fintech`. Prefer construction, engineering, infrastructure and industrial-supply-chain cases, but accept a fresh sector-level product, regulatory, operating or partnership event without an AEC customer when it materially informs the financial/data-tech ecosystem. Exclude consumer promotions and lifestyle finance.
- Put software products, vendor ecosystems, digital twins, data platforms, implementation, and customer-practice news in `informatization`; use `digital` only when AI is the key novelty.
- Put physical construction innovation, robotics, industrialized construction, materials, and engineering methods in `construction-tech`.
- Put cross-border contract wins and market-entry changes in `overseas`, even when they also involve sourcing or matching.
- Use `industry-data` for fresh statistics and indicators; use `extended` for substantial interpretation or research.
- Use `standards` for enforceable or proposed rules, not general policy direction.
- Treat `government` as a cross-ministry and cross-region macro-policy section. Search State Council, central ministries/commissions and provincial/municipal governments; never equate it with MOHURD alone.
- For custom interests, exact-field relevance is sufficient. For example, `半导体` includes chip, fab, equipment, materials, EDA, packaging/testing, capital expenditure, trade policy and company events; factory construction is only one subdirection.
- Assign each verified event to one selected section only. Choose its primary home by exact field match, then decision impact, then the user's relevance score; preserve other section matches only as excluded ledger leads (`assigned-to-<section-id>`), never as rendered duplicate cards.
- Do not render `跨板块复用` or `关联资讯`. A section with no independent full card remains `checked-empty` or `limited`; do not use another row's event to make it appear complete.
