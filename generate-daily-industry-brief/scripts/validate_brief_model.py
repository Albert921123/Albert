#!/usr/bin/env python3
"""Validate the structured editorial model before deterministic HTML rendering."""
from __future__ import print_function
import argparse, hashlib, html as html_module, json, re, sys
from pathlib import Path
from py36_compat import configure_utf8_stdio

FIELDS=("what_happened","why_matters","action_or_risk","judgement")
CAUSAL_TERMS=("导致","因此","从而","进而","必然","传导至","推动其","从…走向…")
THIN_TERMS=("持续关注","值得关注","建议关注","后续关注","可作为线索")

def text(value): return str(value or "").strip()
def included(decision): return str(decision or "").startswith("included-")

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(); ap.add_argument("model",type=Path); ap.add_argument("--ledger",type=Path,required=True); ap.add_argument("--plan",type=Path,required=True); ap.add_argument("--html",type=Path); args=ap.parse_args(); issues=[]
    try:
        model=json.loads(args.model.read_text(encoding="utf-8")); ledger=json.loads(args.ledger.read_text(encoding="utf-8")); plan=json.loads(args.plan.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok":False,"issues":["cannot read model/ledger/plan: %s"%exc]},ensure_ascii=False,indent=2)); return 2
    plan_ids=[x.get("section_id") for x in (plan.get("sections") or [])]
    for key in ("report_date","run_timestamp","window_start","window_end","fallback_window_start","timezone"):
        if not text(model.get(key)): issues.append("model missing "+key)
    rows=model.get("sections") if isinstance(model,dict) else None
    if not isinstance(rows,list): rows=[]; issues.append("model sections must be an array")
    if [x.get("section_id") for x in rows] != plan_ids: issues.append("model section order must exactly match the immutable plan")
    ledger_by_event={}
    for c in ledger.get("candidates") or []:
        if included(c.get("decision")) and c.get("event_id"): ledger_by_event[str(c["event_id"])]=c
    model_events={}; primary=[]
    for ri,row in enumerate(rows):
        sid=row.get("section_id"); cards=row.get("cards") or []
        if not isinstance(cards,list): issues.append("section[%d] cards must be an array"%ri); cards=[]
        for ci,card in enumerate(cards):
            p="section[%d].cards[%d]"%(ri,ci); event_id=text(card.get("event_id"))
            if not event_id or event_id in model_events: issues.append(p+" missing or duplicate event_id"); continue
            model_events[event_id]=card; source=ledger_by_event.get(event_id)
            if not source: issues.append(p+" does not correspond to an included ledger event_id"); continue
            if source.get("section_id")!=sid: issues.append(p+" section does not match ledger assignment")
            for key in ("title","source_name","source_url","published_at"):
                if not text(card.get(key)): issues.append(p+" missing "+key)
            if text(card.get("source_url")) != text(source.get("direct_record_url") or source.get("url")): issues.append(p+" source_url differs from ledger direct record")
            facts=card.get("facts") if isinstance(card.get("facts"),dict) else {}
            if not text(facts.get("actor")) or not text(facts.get("dated_action")) or not text(facts.get("affected_object")): issues.append(p+" needs actor, dated_action and affected_object")
            decision_facts=facts.get("decision_facts") or []
            if not isinstance(decision_facts,list) or len([x for x in decision_facts if text(x)])<2: issues.append(p+" needs at least two decision_facts")
            writing=card.get("writing") if isinstance(card.get("writing"),dict) else {}
            for key in FIELDS:
                value=text(writing.get(key))
                if len(value)<45: issues.append(p+" writing.%s is too short"%key)
                if value in THIN_TERMS: issues.append(p+" writing.%s is generic filler"%key)
            if source.get("decision")=="included-primary": primary.append(event_id)
    if set(model_events)!=set(ledger_by_event): issues.append("model cards must exactly match all included ledger events")
    highlights=model.get("highlights") or []
    if len(primary)>=3 and (not isinstance(highlights,list) or len(highlights)!=3): issues.append("exactly three highlights are required when at least three primary events exist")
    for event_id in highlights if isinstance(highlights,list) else []:
        if event_id not in primary: issues.append("highlight must reference an included-primary event: "+str(event_id))
    recommendations=model.get("recommendations") or []
    if not isinstance(recommendations,list): issues.append("recommendations must be an array"); recommendations=[]
    if len(recommendations)>3: issues.append("recommendations cannot exceed three themes")
    for ri,rec in enumerate(recommendations):
        p="recommendations[%d]"%ri; combined=text(rec.get("theme"))+text(rec.get("note")); segments=rec.get("segments") or []
        if len(segments)!=3: issues.append(p+" must contain exactly three parallel segments")
        ids=[]
        for si,segment in enumerate(segments):
            event_id=text(segment.get("event_id")); ids.append(event_id); combined+=text(segment.get("fact"))
            if event_id not in primary: issues.append(p+" segment[%d] must reference an included-primary event"%si)
            if not text(segment.get("label")) or not text(segment.get("fact")): issues.append(p+" segment[%d] needs label and fact"%si)
        if len(set(ids))!=len(ids): issues.append(p+" must use three independent event ids")
        for term in CAUSAL_TERMS:
            if term in combined: issues.append(p+" contains prohibited causal wording: "+term)
    if args.html:
        try: html=args.html.read_text(encoding="utf-8"); visible=html_module.unescape(html)
        except Exception as exc: issues.append("cannot read HTML: %s"%exc); html=""; visible=""
        model_hash=hashlib.sha256(args.model.read_bytes()).hexdigest()
        if ('name="zhixun-model-sha256" content="%s"'%model_hash) not in html: issues.append("HTML is not hash-bound to this editorial model")
        for event_id,card in model_events.items():
            if ('data-event-id="%s"'%event_id) not in html: issues.append("HTML missing model event_id: "+event_id)
            for value in (text(card.get("title")),)+tuple(text((card.get("writing") or {}).get(k)) for k in FIELDS):
                if value and value not in visible: issues.append("HTML differs from model content for event: "+event_id); break
        for rec in recommendations:
            if text(rec.get("theme")) and text(rec.get("theme")) not in visible: issues.append("HTML missing recommendation theme: "+text(rec.get("theme")))
    print(json.dumps({"ok":not issues,"section_count":len(rows),"card_count":len(model_events),"primary_count":len(primary),"recommendation_count":len(recommendations),"issues":issues},ensure_ascii=False,indent=2))
    return 0 if not issues else 2
if __name__=="__main__": sys.exit(main())
