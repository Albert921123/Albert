#!/usr/bin/env python3
"""Issue hash-bound render authorization and formal delivery receipts."""
from __future__ import print_function
import argparse, hashlib, json, re, subprocess, sys, uuid
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from py36_compat import configure_utf8_stdio

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def now_cn(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def gate(command, label):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True, encoding="utf-8", errors="replace")
    if result.returncode: raise SystemExit(label + " failed:\n" + result.stdout.strip())
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

REQUIRED_LANES = ("field", "actor", "official", "business-intersection")
FINAL_OUTCOMES = {"complete", "observed", "expanded", "business-observation", "checked-empty", "limited"}
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def csv_values(value): return sorted(set(x.strip() for x in (value or "").split(",") if x.strip()))
def section_record(state, section_id):
    for row in state.get("sections") or []:
        if row.get("section_id") == section_id: return row
    raise SystemExit("unknown section: " + section_id)
def assert_state_ledger_consistency(state, ledger):
    ledger_candidates=ledger.get("candidates") if isinstance(ledger,dict) else None
    if not isinstance(ledger_candidates,list): raise SystemExit("ledger candidates must be an array")
    for row in state.get("sections") or []:
        section_id=row.get("section_id")
        state_rows=Counter((str(c.get("url") or ""),str(c.get("decision") or "")) for c in (row.get("candidates") or []))
        ledger_rows=Counter((str(c.get("url") or ""),str(c.get("decision") or "")) for c in ledger_candidates if c.get("section_id")==section_id)
        if state_rows != ledger_rows:
            raise SystemExit("work-state and ledger candidates differ for section: " + str(section_id))
        ledger_section=next((x for x in (ledger.get("sections") or []) if x.get("section_id")==section_id),None)
        if not ledger_section: raise SystemExit("ledger section missing for work-state row: "+str(section_id))
        state_queries=Counter((lane,str(e.get("query") or ""),str(e.get("raw_results_sha256") or ""),int(e.get("result_count") or 0)) for lane,e in (row.get("queries") or {}).items())
        ledger_queries=Counter((str(e.get("lane") or ""),str(e.get("query") or ""),str(e.get("raw_results_sha256") or ""),int(e.get("result_count") or 0)) for e in ((ledger_section.get("retrieval_proof") or {}).get("query_evidence") or []))
        if state_queries != ledger_queries:
            raise SystemExit("work-state and ledger query receipts differ for section: "+str(section_id))
def next_action(state):
    for lane in REQUIRED_LANES:
        for row in state.get("sections") or []:
            if lane not in (row.get("queries") or {}): return {"action":"host_search","section_id":row["section_id"],"label":row["label"],"lane":lane}
    for row in state.get("sections") or []:
        for candidate in row.get("candidates") or []:
            if not candidate.get("decision"): return {"action":"verify_candidate","section_id":row["section_id"],"candidate":candidate}
    for row in state.get("sections") or []:
        included=len([c for c in row.get("candidates",[]) if str(c.get("decision","")).startswith("included-")])
        if included < int(row.get("target_card_count",2)) and "expansion" not in (row.get("queries") or {}): return {"action":"host_search","section_id":row["section_id"],"label":row["label"],"lane":"expansion"}
    for row in state.get("sections") or []:
        if not row.get("outcome"): return {"action":"close_section","section_id":row["section_id"],"label":row["label"]}
    return {"action":"authorize_render","message":"all planned sections are closed"}

def main():
    configure_utf8_stdio(); parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="action")
    start = sub.add_parser("start-work"); start.add_argument("--plan",type=Path,required=True); start.add_argument("--profiles",type=Path,required=True); start.add_argument("--pipeline-id",required=True); start.add_argument("--output",type=Path,required=True)
    nxt = sub.add_parser("next"); nxt.add_argument("--state",type=Path,required=True)
    record = sub.add_parser("record-query"); record.add_argument("--state",type=Path,required=True); record.add_argument("--section",required=True); record.add_argument("--lane",choices=REQUIRED_LANES+("expansion",),required=True); record.add_argument("--query",required=True); record.add_argument("--route",required=True); record.add_argument("--raw-results",type=Path,required=True); record.add_argument("--source-families-checked",required=True); record.add_argument("--actor-classes-checked",required=True); record.add_argument("--event-families-checked",required=True)
    decide = sub.add_parser("record-decision"); decide.add_argument("--state",type=Path,required=True); decide.add_argument("--section",required=True); decide.add_argument("--candidate-id",required=True); decide.add_argument("--decision",required=True); decide.add_argument("--reason",required=True); decide.add_argument("--direct-url"); decide.add_argument("--published-at"); decide.add_argument("--source-name")
    close = sub.add_parser("close-section"); close.add_argument("--state",type=Path,required=True); close.add_argument("--section",required=True); close.add_argument("--outcome",choices=sorted(FINAL_OUTCOMES),required=True); close.add_argument("--below-target-reason")
    end = sub.add_parser("assert-complete"); end.add_argument("--state",type=Path,required=True)
    a = sub.add_parser("authorize-render")
    for name in ("ledger", "plan", "pipeline-state", "model", "registry", "output"): a.add_argument("--" + name, type=Path, required=True)
    a.add_argument("--work-state", type=Path, required=True)
    a.add_argument("--expected-sections", type=int, required=True)
    f = sub.add_parser("finalize")
    for name in ("authorization", "ledger", "artifact", "template", "output"): f.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(); scripts = Path(__file__).resolve().parent
    if args.action == "start-work":
        plan=load(args.plan); profile_payload=load(args.profiles)
        gate([sys.executable,str(scripts/"validate_section_profiles.py"),str(args.profiles),"--expected-sections",str(len(plan.get("sections") or []))],"section-profile gate")
        profile_rows={r.get("section_id"):r for r in (profile_payload.get("sections") or []) if isinstance(r,dict)}
        plan_ids=[r.get("section_id") for r in (plan.get("sections") or [])]
        if set(plan_ids) != set(profile_rows): raise SystemExit("section profiles do not exactly match the immutable plan")
        rows=[{"section_id":r["section_id"],"label":r["label"],"target_card_count":r["target_card_count"],"candidate_review_floor":r["candidate_review_floor"],"source_family_floor":r["source_family_floor"],"actor_classes":r.get("actor_classes") or [],"source_classes":r.get("source_classes") or [],"event_families":r.get("event_families") or [],"profile":profile_rows[r["section_id"]],"queries":{},"candidates":[],"outcome":None} for r in (plan.get("sections") or [])]
        if not rows: raise SystemExit("plan has no sections")
        if len(str(args.pipeline_id or "").strip()) < 16: raise SystemExit("start-work requires a supervisor-issued pipeline-id")
        save(args.output,{"kind":"zhixun-retrieval-work-state","retrieval_contract":"universal-overseas-parity-v1","pipeline_id":args.pipeline_id,"run_id":plan.get("run_id"),"plan":str(args.plan.resolve()),"plan_sha256":sha(args.plan),"profiles":str(args.profiles.resolve()),"profiles_sha256":sha(args.profiles),"created_at":now_cn(),"updated_at":now_cn(),"sections":rows})
        state=load(args.output); print(json.dumps({"ok":True,"state":str(args.output.resolve()),"next":next_action(state)},ensure_ascii=False)); return 0
    if args.action == "next": print(json.dumps(next_action(load(args.state)),ensure_ascii=False)); return 0
    if args.action == "record-query":
        state=load(args.state); row=section_record(state,args.section)
        if args.lane in row["queries"]: raise SystemExit("lane already recorded")
        families=csv_values(args.source_families_checked); actors=csv_values(args.actor_classes_checked); events=csv_values(args.event_families_checked)
        if not families or not actors or not events: raise SystemExit("each query record needs named source families, actor classes and event families checked")
        envelope=load(args.raw_results)
        if not isinstance(envelope,dict) or envelope.get("schema_version")!=1: raise SystemExit("raw-results must be a version-1 query evidence object")
        if str(envelope.get("query") or "").strip()!=args.query.strip() or str(envelope.get("route") or "").strip()!=args.route.strip(): raise SystemExit("raw-results query/route differs from command")
        status=str(envelope.get("status") or "").strip()
        if status not in ("completed","failed","skipped-unavailable"): raise SystemExit("raw-results needs a valid status")
        transport=envelope.get("transport_evidence") if isinstance(envelope.get("transport_evidence"),dict) else {}
        tool_name=str(transport.get("tool_name") or "").strip(); captured_at=str(transport.get("captured_at") or "").strip()
        invocation_id=str(transport.get("invocation_id") or "").strip(); no_id_reason=str(transport.get("invocation_id_not_exposed_reason") or "").strip()
        if not tool_name or not captured_at: raise SystemExit("raw-results needs transport_evidence.tool_name and captured_at")
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$",captured_at): raise SystemExit("transport_evidence.captured_at must be an ISO-8601 timestamp with timezone")
        if not invocation_id and len(no_id_reason)<10: raise SystemExit("transport evidence needs invocation_id or a specific invocation_id_not_exposed_reason")
        raw=envelope.get("results")
        if not isinstance(raw,list): raise SystemExit("raw-results results must be a JSON array")
        if status != "completed" and raw: raise SystemExit("failed or unavailable query attempts cannot claim candidates")
        result_count=len(raw)
        by_url={c.get("url"):c for c in row["candidates"]}; added=[]
        for item in raw:
            if not isinstance(item,dict) or not item.get("title") or not item.get("source_name") or not str(item.get("url","")).startswith(("http://","https://")): raise SystemExit("candidate needs title, source_name and HTTP(S) URL")
            for field in ("source_family_id","source_class","actor_class","event_family"):
                if not str(item.get(field) or "").strip(): raise SystemExit("candidate needs " + field)
            if item["source_family_id"] not in families or item["actor_class"] not in actors or item["event_family"] not in events: raise SystemExit("candidate source/actor/event values must be declared in the query evidence")
            if item["url"] in by_url:
                added.append(by_url[item["url"]]["candidate_id"])
                continue
            item=dict(item); item["candidate_id"]=item.get("candidate_id") or uuid.uuid4().hex; item["query_lane"]=args.lane; row["candidates"].append(item); by_url[item["url"]]=item; added.append(item["candidate_id"])
        # Every result returned by the host search must be persisted.  A previous
        # version only rejected ``result_count < recorded``; this allowed a lane
        # reporting five hits to retain zero candidates and later masquerade as
        # an exhausted pool.
        evidence={"query":args.query,"route":args.route,"status":status,"result_count":result_count,"recorded_candidate_ids":added,"source_families_checked":families,"actor_classes_checked":actors,"event_families_checked":events,"raw_results":str(args.raw_results.resolve()),"raw_results_sha256":sha(args.raw_results),"transport_evidence":transport,"at":now_cn()}
        if status == "completed":
            row["queries"][args.lane]=evidence
        else:
            row.setdefault("failed_query_attempts",[]).append(dict(evidence, lane=args.lane))
        state["updated_at"]=now_cn(); save(args.state,state)
        print(json.dumps({"ok":True,"next":next_action(state)},ensure_ascii=False)); return 0
    if args.action == "record-decision":
        state=load(args.state); row=section_record(state,args.section); found=next((c for c in row["candidates"] if c.get("candidate_id")==args.candidate_id),None)
        if found is None: raise SystemExit("candidate not found")
        if found.get("decision"): raise SystemExit("candidate already decided")
        if args.decision.startswith("included-") and not all((args.direct_url,args.published_at,args.source_name)): raise SystemExit("included candidate needs direct URL, time and source")
        found.update({"decision":args.decision,"reason":args.reason,"direct_record_url":args.direct_url or "","published_at":args.published_at or "","verified_source_name":args.source_name or "","decided_at":now_cn()}); state["updated_at"]=now_cn(); save(args.state,state)
        print(json.dumps({"ok":True,"next":next_action(state)},ensure_ascii=False)); return 0
    if args.action == "close-section":
        state=load(args.state); row=section_record(state,args.section); missing=[x for x in REQUIRED_LANES if x not in row["queries"]]
        if missing: raise SystemExit("missing lanes: "+", ".join(missing))
        undecided=[c["candidate_id"] for c in row["candidates"] if not c.get("decision")]
        if undecided: raise SystemExit("undecided candidates: "+", ".join(undecided))
        incomplete=[]
        for lane, evidence in row["queries"].items():
            if int(evidence.get("result_count", -1)) != len(evidence.get("recorded_candidate_ids") or []):
                incomplete.append(lane)
        if incomplete:
            raise SystemExit("query results were not fully persisted for lanes: "+", ".join(incomplete))
        included=len([c for c in row["candidates"] if str(c.get("decision","")).startswith("included-")]); target=int(row["target_card_count"])
        if included < target and ("expansion" not in row["queries"] or not args.below_target_reason): raise SystemExit("below target requires expansion and specific reason")
        query_strings=[str(x.get("query") or "").strip().lower() for x in row["queries"].values()]
        if len(query_strings) != len(set(query_strings)): raise SystemExit("each lane and expansion must use a distinct query")
        all_families=set(); all_actors=set(); all_events=set()
        for evidence in row["queries"].values():
            all_families.update(evidence.get("source_families_checked") or [])
            all_actors.update(evidence.get("actor_classes_checked") or [])
            all_events.update(evidence.get("event_families_checked") or [])
        family_floor=int(row.get("source_family_floor") or 2); candidate_floor=int(row.get("candidate_review_floor") or 4)
        if len(all_families) < family_floor: raise SystemExit("section has not checked the planned minimum independent source families")
        if len(all_actors) < 3: raise SystemExit("section must check at least three actor classes")
        if len(all_events) < 3: raise SystemExit("section must check at least three event families")
        scarcity_proof=False
        if included < target and "expansion" in row["queries"]:
            expansion=row["queries"]["expansion"]; earlier=set()
            for lane,evidence in row["queries"].items():
                if lane != "expansion": earlier.update(evidence.get("source_families_checked") or [])
            changed=set(expansion.get("source_families_checked") or [])-earlier
            scarcity_proof=len(expansion.get("source_families_checked") or [])>=2 and len(changed)>=1 and bool(args.below_target_reason.strip())
            if not scarcity_proof: raise SystemExit("below-target expansion must check at least two families and add a changed source family")
        if len(row["candidates"]) < candidate_floor and not scarcity_proof: raise SystemExit("section has not reached the planned candidate review floor")
        if included==0 and args.outcome not in {"checked-empty","limited"}: raise SystemExit("zero-card section must close empty/limited")
        if included>0 and args.outcome in {"checked-empty","limited"}: raise SystemExit("card-bearing section cannot close empty/limited")
        row.update({"outcome":args.outcome,"candidate_pool_exhausted":included<target,"additional_discovery_completed":"expansion" in row["queries"],"below_target_reason":args.below_target_reason or "","source_families_checked":sorted(all_families),"actor_classes_checked":sorted(all_actors),"event_families_checked":sorted(all_events),"scarcity_proof":scarcity_proof,"closed_at":now_cn()}); state["updated_at"]=now_cn(); save(args.state,state)
        print(json.dumps({"ok":True,"next":next_action(state)},ensure_ascii=False)); return 0
    if args.action == "assert-complete":
        state=load(args.state); action=next_action(state)
        if action.get("action")!="authorize_render": raise SystemExit("run cannot end; next required action: "+json.dumps(action,ensure_ascii=False))
        print(json.dumps({"ok":True,"status":"retrieval-complete","next":action},ensure_ascii=False)); return 0
    if args.action == "authorize-render":
        work_state=load(args.work_state); pending=next_action(work_state)
        if pending.get("action") != "authorize_render": raise SystemExit("retrieval loop incomplete; next required action: "+json.dumps(pending,ensure_ascii=False))
        if str(args.plan.resolve()) != work_state.get("plan") or sha(args.plan) != work_state.get("plan_sha256"): raise SystemExit("work state is not bound to this immutable plan")
        profiles_path=Path(work_state.get("profiles") or "")
        if not profiles_path.is_file() or sha(profiles_path) != work_state.get("profiles_sha256"): raise SystemExit("work state is not bound to the validated section profiles")
        gate([sys.executable,str(scripts/"run_pipeline.py"),"verify","--state",str(args.pipeline_state),"--work-state",str(args.work_state),"--require-sealed"],"pipeline gate")
        assert_state_ledger_consistency(work_state,load(args.ledger))
        gate([sys.executable, str(scripts / "validate_retrieval_ledger.py"), str(args.ledger), "--expected-sections", str(args.expected_sections), "--plan", str(args.plan)], "ledger gate")
        gate([sys.executable,str(scripts/"validate_source_registry.py"),str(args.ledger),"--registry",str(args.registry)],"source-registry gate")
        gate([sys.executable,str(scripts/"validate_brief_model.py"),str(args.model),"--ledger",str(args.ledger),"--plan",str(args.plan)],"editorial-model gate")
        gate([sys.executable, str(scripts / "validate_time_window.py"), str(args.ledger)], "time gate")
        save(args.output, {"kind":"zhixun-render-authorization", "issued_at":now_cn(), "pipeline_state":str(args.pipeline_state.resolve()),"pipeline_state_sha256":sha(args.pipeline_state),"work_state":str(args.work_state.resolve()), "work_state_sha256":sha(args.work_state), "ledger":str(args.ledger.resolve()), "ledger_sha256":sha(args.ledger), "plan":str(args.plan.resolve()), "plan_sha256":sha(args.plan),"model":str(args.model.resolve()),"model_sha256":sha(args.model),"registry":str(args.registry.resolve()),"registry_sha256":sha(args.registry), "expected_sections":args.expected_sections})
        print(json.dumps({"ok":True,"authorization":str(args.output.resolve())}, ensure_ascii=False)); return 0
    if args.action == "finalize":
        auth=json.loads(args.authorization.read_text(encoding="utf-8"))
        if auth.get("kind") != "zhixun-render-authorization": raise SystemExit("invalid render authorization")
        work_state_path=Path(auth.get("work_state") or "")
        if not work_state_path.is_file() or sha(work_state_path) != auth.get("work_state_sha256"): raise SystemExit("retrieval work state changed or is missing after render authorization")
        for key in ("pipeline_state","model","registry"):
            path=Path(auth.get(key) or "")
            if not path.is_file() or sha(path)!=auth.get(key+"_sha256"): raise SystemExit(key+" changed or is missing after render authorization")
        if str(args.ledger.resolve()) != auth.get("ledger") or sha(args.ledger) != auth.get("ledger_sha256"): raise SystemExit("ledger changed after render authorization")
        expected=int(auth["expected_sections"])
        gate([sys.executable,str(scripts/"validate_retrieval_ledger.py"),str(args.ledger),"--expected-sections",str(expected),"--plan",auth["plan"]],"ledger gate")
        gate([sys.executable,str(scripts/"validate_source_registry.py"),str(args.ledger),"--registry",auth["registry"]],"source-registry gate")
        gate([sys.executable,str(scripts/"validate_brief_model.py"),auth["model"],"--ledger",str(args.ledger),"--plan",auth["plan"],"--html",str(args.artifact)],"editorial-model gate")
        gate([sys.executable,str(scripts/"validate_time_window.py"),str(args.ledger)],"time gate")
        gate([sys.executable,str(scripts/"validate_html.py"),str(args.artifact),"--ledger",str(args.ledger),"--plan",auth["plan"],"--expected-sections",str(expected)],"HTML gate")
        gate([sys.executable,str(scripts/"verify_editorial_gate.py"),str(args.artifact)],"editorial gate")
        gate([sys.executable,str(scripts/"verify_delivery_gate.py"),str(args.artifact),"--template",str(args.template)],"template gate")
        ledger=json.loads(args.ledger.read_text(encoding="utf-8"))
        query_receipts=sum(len((row.get("retrieval_proof") or {}).get("query_evidence") or []) for row in (ledger.get("sections") or []))
        save(args.output,{"kind":"zhixun-formal-delivery-receipt","issued_at":now_cn(),"artifact":str(args.artifact.resolve()),"artifact_sha256":sha(args.artifact),"ledger":str(args.ledger.resolve()),"ledger_sha256":sha(args.ledger),"model":auth["model"],"model_sha256":auth["model_sha256"],"registry_version":load(Path(auth["registry"])).get("registry_version"),"template_sha256":sha(args.template),"section_count":len(ledger.get("sections") or []),"candidate_count":len(ledger.get("candidates") or []),"query_evidence_count":query_receipts,"all_gates_passed":True})
        print(json.dumps({"ok":True,"delivery_receipt":str(args.output.resolve()),"all_gates_passed":True},ensure_ascii=False)); return 0
    parser.error("choose authorize-render or finalize")
if __name__ == "__main__": sys.exit(main())
