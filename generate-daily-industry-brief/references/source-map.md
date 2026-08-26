# Construction intelligence source map

Use this file to keep daily discovery current, authoritative, and broad enough for every selected field. Treat organization and product names as search targets, not endorsements. Read `section-source-catalog.md` for the exact per-section source families and query lanes.

## Daily 24-hour-first source policy

- Calculate the rolling 24-hour primary window and the preceding 24-to-48-hour fallback segment from the automation run timestamp. Apply the primary window first to every section. Search the fallback segment only for sections confirmed empty in the primary window.
- Search Tier 1 sources first. Run the field lane and source/actor lane before applying the construction/business intersection lane. Stop after useful candidates are verified or the empty-section threshold is met; do not narrow a broad selected field to AEC-only merely because the configured industry scope mentions construction.
- Include Tier 2 reporting only when it contains a genuinely new event and links to, quotes, or can be checked against an identifiable primary record.
- Never cite an aggregator, search-results page, public-account mirror, or repost when the original is available.
- Prefer a smaller set of authoritative source families across days so readers can recognize provenance. Twenty items per section is a ceiling, not a target.

## Source priority

1. **Tier 1 — final citation by default:** central and local government or regulator sites, standards bodies, public-resource and government-procurement notices, stock-exchange filings, company investor-relations or official newsroom pages, official event transcripts, and original research publishers.
2. **Tier 2 — verification fallback:** established financial media, major construction trade media, association publications, conference organizers, universities, and design institutes. Use when an original page is unavailable or when the publisher contributes material reporting. One accessible authoritative Tier 2 source may verify an ordinary, non-controversial event when it identifies the event, actor and time and clearly attributes the underlying record; require an official record or two independent credible sources for material, sensitive or disputed claims.
3. **Discovery only — never final citation:** reposting platforms, public-account aggregators, short-video summaries, content farms, and personal commentary.

Use one Tier 1 source whenever available. When the original page is blocked, follow `retrieval-routing.md`: try an official RSS/sitemap/print page, exchange or regulator filing, project-owner/counterparty announcement, then an accessible authoritative Tier 2 account. Record which route verified the event instead of discarding an otherwise verifiable ordinary event merely because the first domain failed.

## Core source pool by topic

| Topic families | Search first | Use only as fallback |
|---|---|---|
| 数科 | 央行与金融监管、平台官方新闻室、产品与客户案例、企业公告与投资者关系页面、交易所披露、客户或合作方原文、金融与数据行业协会原文 | 可核验原始事件的主流财经媒体、供应链金融、金融科技与建筑行业媒体 |
| 政府宏观 | 中国政府网/国务院；发改、财政、央行、金融监管、证监、工信、自然资源、交通、商务、市场监管、统计、能源、国资、应急、生态环境、住建等部委；省市政府及其部门原文 | 权威政策解读、主流财经媒体 |
| 标准、绿色低碳、行业数据 | 住建主管部门、统计与发改部门、标准发布机构、能源/生态环境/工信部门、地方政府原文 | 权威政策解读、主流财经与行业媒体 |
| 寻源、撮合、海外 | 全国及地方公共资源交易平台、政府采购平台、业主或承包商公告、企业官方签约或中标公告 | 行业媒体的项目报道 |
| 企业经营、投融资 | 交易所公告、上市公司投资者关系页面、企业官方新闻、债券与评级披露 | 主流财经媒体 |
| 高管观点 | 官方演讲稿、政策吹风会、业绩会纪要、投资者交流记录、官方专访、主办方实录 | 能核实原话和场合的权威媒体专访 |
| AI、建筑软件、建筑科技 | 厂商官方新闻室、产品发布页、客户或项目业主案例、科研院所原文 | 头部科技或建筑行业媒体 |
| 用工 | 人社与住建主管部门、企业官方招聘、公共就业服务平台、权威统计 | 主流招聘与行业媒体 |
| 拓展阅读 | 原始白皮书、研究机构发布页、学术出版页、协会原报告 | 对报告有实质增量的权威解读 |

## Daily official-index matrix

Use this compact matrix to finish coverage without launching an unbounded open-web sweep. The names are discovery targets; use the currently reachable official index, feed, or site-native search.

| Retrieval cluster | Minimum daily official checks | Rows supported when inspected separately |
|---|---|---|
| Project and labor | 中国政府采购网/地方公共资源交易索引；公共就业或人社发布索引 | 寻源、撮合、用工 |
| Company and capital | 上交所、深交所、北交所或巨潮资讯公告索引；公司投资者关系/官方新闻 | 企业经营、投融资、高管观点 |
| Policy and evidence | 中国政府网；发改、财政、央行/金融监管、工信、自然资源、交通、商务、市场监管、统计、能源、国资、应急、生态环境、住建；省市政府；标准发布索引 | 政府宏观、行业数据、标准规范、绿色低碳及相关自定义板块 |
| Technology ecosystem | 建筑软件/科技厂商官方新闻室或客户案例；科研院所/项目业主原文 | AI、建筑软件、建筑科技 |
| Overseas and extended | 外交部、商务部、国际合作项目业主/承包商公告；原始研究发布页 | 海外、拓展阅读 |
| Construction fintech | 用户指定数科企业官方新闻/IR；交易所或产业链客户/合作方原文 | 数科 |

One current official index can be checked for more than one related row, but the agent must inspect and record each row's own keywords and result. A successfully inspected quiet index is valid coverage evidence under `retrieval-audit.md`.

## Knowledge layers

### Government, standards, and associations

- National and local housing and urban-rural development authorities
- Development, finance, statistics, market-regulation, energy, transport, and emergency-management authorities
- National, industry, local, and group standards publishers
- Construction, engineering cost, survey and design, real-estate, municipal, green-building, and intelligent-construction associations

### Construction enterprises and professional institutions

- Central and local state-owned construction groups
- General contractors, specialist contractors, developers, infrastructure investors, and building-material companies
- Architectural design institutes, engineering consultancies, cost consultancies, supervision firms, research institutes, and universities
- Track: orders, backlog, margin, cash flow, organization, strategy, project delivery, technology investment, and overseas localization

### Construction software and technology ecosystem

- Domestic BIM, cost, project-management, digital-construction, collaborative-design, and enterprise-management vendors
- Global AEC design, digital-twin, geospatial, construction-cloud, project-controls, and asset-lifecycle platforms
- Cloud providers, AI companies, robotics firms, reality-capture vendors, hardware and IoT companies serving design, construction, and operations
- Example discovery targets: 广联达、品茗科技、盈建科、用友、金蝶，以及 Autodesk、Bentley Systems、Trimble、Nemetschek、Hexagon、Dassault Systèmes、Procore
- Track: product releases, pricing or business-model shifts, ecosystem partnerships, customer adoption, AI strategy, localization, acquisitions, and executive commentary

### Financial services and data-tech platforms

- Cover financial services and data-technology platforms supporting enterprise finance, industrial finance, procurement, settlement, receivables, factoring, credit, leasing, risk control, trusted data and supply-chain financing. Construction, engineering, materials and infrastructure cases receive higher business-relevance ranking but are not the only admissible field.
- Primary discovery targets supplied by the user: 联易融数科、怡亚通、欧冶金服、广联达数字金融、中企云链、中企云租、蚂蚁数科、金网络、金网络数科、成都金网络供应链金融、航信金融.
- Supplement only with directly comparable industry-facing organizations, including construction-group factoring or finance companies, bank industrial-finance platforms, and supply-chain-finance technology providers with identifiable AEC or industrial-chain customers.
- Track: new products, customer or project adoption, platform transactions, financing or factoring programs, ecosystem partnerships, regulatory developments, risk-control changes, operating results, executive statements, and material risk events.
- Require an explicit `数科` bridge in every included item: identify the financial/data product, enterprise customer, transaction, policy, operating result, partnership or risk signal. Add the AEC/industrial bridge when present; do not invent one.
- Exclude consumer-credit promotions, unrelated retail-finance products, generic AI/cloud marketing, awards without a new business event, and corporate publicity with no financial/data-platform implication.

### Broad custom-interest retrieval

- Search every custom interest as its own field before combining it with construction. The current recurring profiles and named sources are maintained in `section-source-catalog.md`.
- For `半导体`, search government policy, fabs and capital expenditure, chips, equipment, materials, EDA, packaging/testing, export controls, financing, M&A, earnings and company products. Semiconductor-factory design/EPC is one optional bridge, not the definition of the section.
- For `光伏` and `储能`, search their full energy-industry chains, policy, capacity, price, projects, procurement, financing, technology and company events; construction/EPC items rank highly but are not required.
- For `AI方向`, broad AI models, agents, compute, data, governance, investment and enterprise adoption qualify; AEC use is a ranking bonus.

### Capital, data, and research

- Exchange filings, earnings calls, investor presentations, bond disclosures, rating reports, industry funds, and M&A announcements
- National statistics, construction PMI, fixed-asset investment, new starts, land, cement, steel, glass, machinery, labor, and tender data
- Broker research, consulting reports, academic papers, white papers, and annual industry reports; link to the original publisher

## Executive-viewpoint protocol

Search by role and occasion, not only by remembered names:

- Roles: 主管部门负责人、协会会长、院士、董事长、总经理、总裁、CEO、CIO、CTO、总工程师、首席科学家、设计总监、研究院负责人
- Occasions: 政策吹风会、论坛演讲、开幕致辞、业绩说明会、投资者交流、媒体专访、白皮书发布、产品发布会、内部公开信
- Themes: 行业判断、订单与需求、城市更新、智能建造、AI、BIM、软件商业模式、出海、组织能力、人才、现金流、绿色低碳

For every included viewpoint, capture:

1. Speaker name and current verified title
2. Organization and occasion
3. Event or publication date
4. Faithful one-sentence viewpoint
5. Evidence link to the original or closest authoritative record
6. Why it matters to construction business, technology adoption, or policy direction

Do not turn marketing slogans into industry forecasts. Mark forward-looking claims as the speaker's view. If the speaker's title or wording cannot be verified, exclude the item.
