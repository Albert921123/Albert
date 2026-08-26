# Topic reference

Use only the rows matching the selected topic IDs. Every topic uses the rolling 24-hour primary window first. A topic confirmed empty in that window may use the separate 24-to-48-hour fallback segment, with every fallback item visibly labeled.

`custom_interests` are additional dynamic topics outside this table. Use each exact user-entered phrase as a separate section title, derive broad field cues plus business-intersection cues, and apply the same 24-hour-primary/48-hour-fallback and source-quality rules. Do not merge custom interests into standard topics or drop them because they are not listed below. The exact custom field is the primary scope; `industry_scope` improves ranking but is not a mandatory admission filter unless the user explicitly requests a narrower interpretation.

| ID | 中文名 | Include | Query cues | Lookback |
|---|---|---|---|---|
| `fintech` | 数科 | 支撑金融服务、企业金融和产业金融的数据科技平台，包括供应链金融、保理、融资、结算、租赁、信用、可信数据与风控，以及客户落地、合作、经营和监管动态；建筑及产业链案例优先，但不是唯一合格范围 | 供应链金融；产业金融；数字金融；保理；应收账款；电子债权；确权；可信数据；融资平台；金融科技；企业金融；数据科技 | strict 24h |
| `sourcing` | 寻源 | 建筑工程招标、采购需求、供应商征集、品类与价格线索 | 招标公告；采购需求；供应商征集；集采；框架协议 | strict 24h |
| `matching` | 撮合 | 产业合作、供需对接、联合项目、签约与资源互补 | 战略合作；项目对接；供需撮合；联合解决方案；签约 | strict 24h |
| `employment` | 用工 | 建筑人才政策、招聘需求、劳务市场、紧缺岗位与薪酬趋势 | 建筑人才；招聘需求；用工；劳务市场；项目经理；数字人才 | strict 24h |
| `overseas` | 海外 | 出海订单、国际工程、市场准入、地区政策与风险 | 海外项目；中标；出海；市场准入；国际工程；属地化 | strict 24h |
| `leadership` | 高管观点 | 主管部门领导、协会专家、院士、企业高管、总工程师、设计院和建筑软件生态管理者的公开观点 | 演讲；致辞；访谈；业绩会；论坛；董事长；总裁；CEO；总工程师；首席科学家 | strict 24h |
| `enterprise` | 企业经营 | 建筑央国企、施工企业、设计院和产业链公司的订单、业绩、组织与战略 | 新签合同；经营业绩；组织调整；战略发布；业绩说明会 | strict 24h |
| `capital` | 投融资 | 上市公司公告、并购重组、股权融资、产业基金与重大投资 | 并购；重组；融资；产业基金；定增；股权投资；上市公司公告 | strict 24h |
| `digital` | AI | AI模型、智能体、算法产品、算力与数据基础设施、AI治理及产业落地；建筑AI优先，但选中本板块时通用AI重大动态也可收录 | AI模型；智能体；生成式AI；AIDC；AI治理；工业AI；具身智能；建筑AI；工程大模型；AI设计；AI审图；AI造价；施工AI | strict 24h |
| `informatization` | 建筑软件 | BIM、造价、项目管理、协同设计、企业管理和软件生态动态 | BIM；造价软件；项目管理；协同设计；平台上线；软件生态；信创 | strict 24h |
| `construction-tech` | 建筑科技 | 智能建造、建筑机器人、装配式、工业化、新材料与工程工法 | 智能建造；建筑机器人；装配式；模块化建筑；新材料；工程技术 | strict 24h |
| `government` | 政府宏观 | 国务院、中央部委及地方政府发布的宏观、财政、金融、投资、产业、科技、土地、能源、交通、监管与公共项目政策；住建只是来源之一 | 国务院；政策发布；发改；财政；央行；金融监管；工信；自然资源；交通；商务；市场监管；统计；能源；国资；省政府；市政府；住建；基础设施 | strict 24h |
| `industry-data` | 行业数据 | 建筑业投资、开工、订单、产值、价格、PMI 与景气指标 | 建筑业产值；固定资产投资；新开工；订单；PMI；建材价格；景气指数 | strict 24h |
| `standards` | 标准规范 | 国家、行业、地方和团体标准，工程计价、审查与验收规则 | 标准发布；规范修订；征求意见；工程计价；施工验收；审图 | strict 24h |
| `green` | 绿色低碳 | 绿色建筑、建筑节能、既有建筑改造、双碳与循环建造 | 绿色建筑；近零能耗；节能改造；双碳；绿色建材；建筑碳排放 | strict 24h |
| `extended` | 拓展阅读 | 新发布的权威研究、白皮书、深度报告与趋势分析 | 研究报告；白皮书；行业展望；专题研究；年度报告 | strict 24h |

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
- Do not duplicate the full story across selected sections. Assign one primary section, then add a compact source-linked `关联资讯` card to each other selected section for which the same event has a distinct and explicit business implication. A related card is not a second story and must state why the event belongs in that section. If an event is the only qualifying result for a selected custom interest, make that custom section the primary location and use a related card in the overlapping standard section; never leave a custom section related-only.
