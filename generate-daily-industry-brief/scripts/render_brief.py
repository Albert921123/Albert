#!/usr/bin/env python3
"""Deterministically render a validated brief model into the locked shell."""
from __future__ import print_function
import argparse, hashlib, html, json, re, sys
from collections import Counter
from pathlib import Path
from py36_compat import configure_utf8_stdio

GROUPS=(("业务与市场",{"fintech","sourcing","matching","employment","overseas","leadership","enterprise","capital"}),("技术与生态",{"digital","informatization","construction-tech"}),("政策与行业",{"government","industry-data","standards","green","extended"}))
KIND={"included-primary":"primary","included-date-observation":"date-observation","included-expanded":"expanded","included-business-observation":"business-observation"}
BADGE={"primary":"24小时内","fallback":"48小时补充","observed":"48小时窗口观察","expanded":"扩展相关资讯","business-observation":"业务观察"}
def esc(value): return html.escape(str(value or ""),quote=True)
def slug(value): return re.sub(r"[^a-zA-Z0-9_-]+","-",str(value or "")).strip("-") or "section"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def included(value): return str(value or "").startswith("included-")

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(); ap.add_argument("--model",type=Path,required=True); ap.add_argument("--ledger",type=Path,required=True); ap.add_argument("--plan",type=Path,required=True); ap.add_argument("--registry",type=Path,required=True); ap.add_argument("--template",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    scripts=Path(__file__).resolve().parent
    for command,label in (([sys.executable,str(scripts/"validate_brief_model.py"),str(args.model),"--ledger",str(args.ledger),"--plan",str(args.plan)],"model"),([sys.executable,str(scripts/"validate_source_registry.py"),str(args.ledger),"--registry",str(args.registry)],"source registry")):
        import subprocess
        result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,encoding="utf-8",errors="replace")
        if result.returncode: raise SystemExit(label+" gate failed:\n"+result.stdout)
    model=json.loads(args.model.read_text(encoding="utf-8")); ledger=json.loads(args.ledger.read_text(encoding="utf-8")); plan=json.loads(args.plan.read_text(encoding="utf-8")); template=args.template.read_text(encoding="utf-8")
    head_end=template.index("</head>")
    head=template[:head_end]+'<meta name="zhixun-model-sha256" content="%s">'%sha(args.model)+template[head_end:head_end+7]
    scripts_html="\n".join(re.findall(r"<script\b[^>]*>.*?</script>",template,re.I|re.S))
    candidates={str(c.get("event_id")):c for c in ledger.get("candidates") or [] if included(c.get("decision")) and c.get("event_id")}
    section_audit={x.get("section_id"):x for x in ledger.get("sections") or []}
    cards={str(c.get("event_id")):c for row in model.get("sections") or [] for c in row.get("cards") or []}
    highlights=[cards[x] for x in model.get("highlights") or [] if x in cards]
    total=len(cards); fallback=sum(1 for x in candidates.values() if x.get("window_class")=="fallback"); coverage=sum(1 for x in ledger.get("sections") or [] if x.get("status")=="complete")
    body=[]; add=body.append
    add('<body><div class="app-shell"><header class="topbar"><div class="topbar-inner"><div class="topline"><div class="brand"><div><p class="brand-kicker">CONSTRUCTION INTELLIGENCE · DAILY EDITION</p><h1>知讯日报</h1></div><p class="runline">%s · %d 条 · %s 分钟</p></div>'%(esc(model.get("report_date")),total,esc(model.get("reading_minutes") or max(1,total*2))))
    add('<section class="highlights" aria-labelledby="highlights-title"><p class="highlights-label" id="highlights-title">今日重点 · 按业务类型</p><ol>')
    for card in highlights: add('<li><a href="#story-%s"><span class="business-type">%s</span>%s</a></li>'%(slug(card.get("event_id")),esc(card.get("business_type") or "重点动态"),esc(card.get("highlight_text") or card.get("title"))))
    add('</ol></section><div class="search-box" role="search"><label class="search-label" for="brief-search">搜索标题、正文、来源或业务关键词</label><div class="search-control"><input id="brief-search" type="search" placeholder="搜索本期知讯，例如：AI、招标、城市更新" autocomplete="off"><button id="clear-search" type="button" aria-label="清空搜索">清空</button></div><p class="search-status" id="search-status" aria-live="polite">输入关键词即可筛选本期内容</p></div></div>')
    add('<div class="meta" aria-label="日报信息"><span>生成时间 <strong>%s</strong></span><span>主检索窗口 <strong>%s — %s</strong></span><span>空板块补充窗口 <strong>%s — %s</strong></span><span>收录 <strong>%d 条</strong></span><span>其中48小时补充 <strong>%d 条</strong></span><span>检索覆盖 <strong>%d/%d 板块</strong></span><span>时区 <strong>%s</strong></span></div></div></header>'%(esc(model.get("run_timestamp")),esc(model.get("window_start")),esc(model.get("window_end")),esc(model.get("fallback_window_start")),esc(model.get("window_start")),total,fallback,coverage,len(model.get("sections") or []),esc(model.get("timezone") or "Asia/Shanghai")))
    add('<div class="reading-frame"><aside class="sidebar" aria-label="板块导航窗格"><p class="nav-kicker">CONTENTS</p><h2>本期板块</h2><nav class="topic-nav" id="topic-nav" aria-label="板块导航"><a class="nav-featured" href="#management-map"><span class="nav-number">↗</span><span>今日推荐关注</span></a>')
    rows=model.get("sections") or []; numbered={x.get("section_id"):i+1 for i,x in enumerate(rows)}
    for label,ids in GROUPS:
        members=[x for x in rows if x.get("section_id") in ids]
        if members:
            add('<div class="nav-group"><p class="nav-group-title">%s</p>'%esc(label))
            for row in members: add('<a class="topic-nav-link" href="#section-%s"><span class="nav-number">%02d</span><span>%s</span></a>'%(slug(row.get("section_id")),numbered[row.get("section_id")],esc(row.get("label"))))
            add('</div>')
    custom=[x for x in rows if x.get("section_id") not in set().union(*[g[1] for g in GROUPS])]
    if custom:
        add('<div class="nav-group"><p class="nav-group-title">自定义关注</p>')
        for row in custom: add('<a class="topic-nav-link" href="#section-%s"><span class="nav-number">%02d</span><span>%s</span></a>'%(slug(row.get("section_id")),numbered[row.get("section_id")],esc(row.get("label"))))
        add('</div>')
    add('</nav><div class="sidebar-summary"><strong>%s</strong>当前共 %d 个关注板块</div></aside><main class="content-scroll" id="content-scroll" tabindex="-1"><div class="content-inner"><div class="no-results" id="no-results">没有找到匹配内容，请更换关键词或清空搜索。</div>'%(esc("、".join(x.get("label","") for x in rows)),len(rows)))
    add('<section class="management-map" id="management-map" aria-labelledby="management-map-title"><div class="management-map-head"><div><p class="eyebrow">TODAY\'S PICKS · 三类已核验线索</p><h2 id="management-map-title">今日推荐关注</h2></div><p>同一主题下并列展示三类来源卡，不表示它们存在因果关系；无正式来源的板块不进入本区。</p></div>')
    for i,rec in enumerate(model.get("recommendations") or [],1):
        add('<article class="chain-card"><div class="chain-title"><span>推荐 %02d</span><h3>%s</h3><p class="chain-status">三类事实线索</p></div><ol class="chain-steps">'%(i,esc(rec.get("theme"))))
        for seg in rec.get("segments") or []: add('<li><b>%s</b><a href="#story-%s">%s</a><small>%s</small></li>'%(esc(seg.get("label")),slug(seg.get("event_id")),esc(cards.get(seg.get("event_id"),{}).get("title")),esc(seg.get("fact"))))
        add('</ol>%s</article>'%(('<p class="chain-note">%s</p>'%esc(rec.get("note"))) if rec.get("note") else ""))
    add('</section>')
    for row in rows:
        sid=row.get("section_id"); audit=section_audit.get(sid,{})
        add('<section class="section" id="section-%s" data-section-name="%s" data-section-kind="%s" data-coverage-status="%s" data-topic-name="%s"><div class="section-head"><h2>%s</h2><span>%s · %d 张完整卡</span></div>'%(slug(sid),esc(row.get("label")),"custom" if str(sid).startswith("custom-") else "standard",esc(row.get("status") or audit.get("status")),esc(row.get("label")),esc(row.get("label")),"自定义关注" if str(sid).startswith("custom-") else "标准板块",len(row.get("cards") or [])))
        for index,card in enumerate(row.get("cards") or [],1):
            source=candidates.get(str(card.get("event_id")),{}); kind=KIND.get(source.get("decision"),"primary"); window=source.get("window_class") or kind; writing=card.get("writing") or {}
            add('<article class="story" id="story-%s" data-event-id="%s" data-entry-kind="%s" data-story-section="%s" data-freshness-window="%s"><span class="story-index">%02d / %s</span><span class="freshness-badge">%s</span><span class="relevance-badge">%s</span><h3>%s</h3><dl><dt>发生了什么</dt><dd>%s</dd><dt>为何值得关注</dt><dd>%s</dd><dt>行动/风险点</dt><dd>%s</dd><dt>研判</dt><dd class="judgement">%s</dd></dl><p class="source">来源：<a href="%s" target="_blank" rel="noopener noreferrer">%s</a> · <time datetime="%s">%s</time></p></article>'%(slug(card.get("event_id")),esc(card.get("event_id")),esc(kind),esc(row.get("label")),esc(window),index,esc(source.get("source_tier")),esc(BADGE.get(window,BADGE.get(kind,"已核验"))),esc(card.get("relevance_label") or "直接相关"),esc(card.get("title")),esc(writing.get("what_happened")),esc(writing.get("why_matters")),esc(writing.get("action_or_risk")),esc(writing.get("judgement")),esc(card.get("source_url")),esc(card.get("source_name")),esc(card.get("published_at")),esc(card.get("published_at"))))
        if not row.get("cards"):
            reason=esc(audit.get("reason") or row.get("reason") or "已完成规定检索，但本窗口内暂无同时满足来源、时间、相关性和唯一归属要求的资讯。")
            add('<div class="empty limited-card" data-empty-state="%s"><p class="story-index">%s / 覆盖说明</p><h3>本轮暂无独立资讯</h3><p class="limited-reason">%s</p></div>'%(esc(row.get("status") or audit.get("status") or "checked-empty"),esc(row.get("label")),reason))
        add('</section>')
    exclusions=Counter(c.get("reason") for c in ledger.get("candidates") or [] if c.get("decision")=="excluded")
    add('<details class="coverage-audit" id="coverage-audit"><summary>检索审计 · %d/%d 板块完成</summary><div class="audit-body"><p class="audit-summary">独立事件 %d 个 · 完整板块卡 %d 张 · 候选页面 %d 个 · 48小时补充 %d 张 · 排除 %d 条</p><div class="audit-grid" role="table" aria-label="逐板块检索覆盖"><div class="audit-head" role="columnheader">板块</div><div class="audit-head" role="columnheader">来源族</div><div class="audit-head" role="columnheader">候选</div><div class="audit-head" role="columnheader">独立卡</div><div class="audit-head" role="columnheader">跨板块</div><div class="audit-head" role="columnheader">紧凑关联</div><div class="audit-head" role="columnheader">状态</div>'%(coverage,len(rows),len(cards),len(cards),len(ledger.get("candidates") or []),fallback,sum(exclusions.values())))
    for row in rows:
        a=section_audit.get(row.get("section_id"),{}); add('<div data-audit-row="%s" role="row"><span>%s</span><span>%s</span><span>%s</span><span>%s</span><span>0</span><span>0</span><span>%s</span></div>'%(esc(row.get("section_id")),esc(row.get("label")),a.get("source_family_count",0),a.get("candidate_count",0),a.get("primary_card_count",0),esc(a.get("status"))))
    add('</div>')
    for row in rows:
        a=section_audit.get(row.get("section_id"),{}); proof=a.get("retrieval_proof") or {}; names="、".join(proof.get("source_families_checked") or []) or "见台账"; titles="、".join(c.get("title","") for c in row.get("cards") or []) or "无"; add('<details class="audit-section-detail"><summary>%s：来源与入选依据</summary><div><p>已检查来源族：%s</p><p>入选资讯：%s</p><p>状态说明：%s</p></div></details>'%(esc(row.get("label")),esc(names),esc(titles),esc(a.get("reason") or proof.get("closure_reason"))))
    exclusion_text="；".join("%s %d条"%(reason or "未注明",count) for reason,count in exclusions.most_common()) or "无"
    add('<p class="audit-reasons">排除原因：%s</p></div></details><footer class="foot">本期按生成时点执行24小时主窗口与板块独立补充窗口；所有来源链接均在新窗口打开。</footer></div></main></div></div>%s</body>'%(esc(exclusion_text),scripts_html))
    output=head+"\n"+"".join(body)+"\n</html>\n"; args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(output,encoding="utf-8")
    print(json.dumps({"ok":True,"output":str(args.output.resolve()),"model_sha256":sha(args.model),"story_count":total,"section_count":len(rows)},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": sys.exit(main())
