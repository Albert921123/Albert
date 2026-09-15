#!/usr/bin/env python3
"""Single supervisor for the resumable 知讯日报 execution contract.

Host-native search still happens outside Python.  This supervisor makes the
next required action observable and seals retrieval before formal rendering.
"""
from __future__ import print_function
import argparse, hashlib, json, subprocess, sys, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from py36_compat import configure_utf8_stdio

def now_cn(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def save(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def call(command,label):
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,encoding="utf-8",errors="replace")
    if result.returncode: raise SystemExit(label+" failed:\n"+result.stdout.strip())
    return result.stdout.strip()
def scripts(): return Path(__file__).resolve().parent

def verify_binding(state_path,work_path,require_sealed=False):
    state=load(state_path); work=load(work_path)
    if state.get("kind")!="zhixun-pipeline-state": raise SystemExit("invalid pipeline state")
    if str(work_path.resolve())!=state.get("work_state"): raise SystemExit("pipeline references a different work state")
    if work.get("pipeline_id")!=state.get("pipeline_id"): raise SystemExit("work state is not bound to this pipeline")
    for field,path_field in (("plan_sha256","plan"),("profiles_sha256","profiles")):
        path=Path(state.get(path_field) or "")
        if not path.is_file() or sha(path)!=state.get(field) or work.get(field)!=state.get(field): raise SystemExit("pipeline %s binding failed"%path_field)
    if require_sealed:
        if state.get("phase")!="retrieval-sealed": raise SystemExit("pipeline retrieval has not been sealed")
        if sha(work_path)!=state.get("sealed_work_state_sha256"): raise SystemExit("work state changed after pipeline seal")
    return state,work

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="action")
    init=sub.add_parser("init")
    for name in ("plan","profiles","reading-receipt","work-state","output"): init.add_argument("--"+name,type=Path,required=True)
    nxt=sub.add_parser("next"); nxt.add_argument("--state",type=Path,required=True); nxt.add_argument("--work-state",type=Path,required=True)
    status=sub.add_parser("status"); status.add_argument("--state",type=Path,required=True); status.add_argument("--work-state",type=Path,required=True)
    seal=sub.add_parser("seal-retrieval"); seal.add_argument("--state",type=Path,required=True); seal.add_argument("--work-state",type=Path,required=True)
    verify=sub.add_parser("verify"); verify.add_argument("--state",type=Path,required=True); verify.add_argument("--work-state",type=Path,required=True); verify.add_argument("--require-sealed",action="store_true")
    rq=sub.add_parser("record-query"); rq.add_argument("--state",type=Path,required=True); rq.add_argument("--work-state",type=Path,required=True); rq.add_argument("--section",required=True); rq.add_argument("--lane",required=True); rq.add_argument("--query",required=True); rq.add_argument("--route",required=True); rq.add_argument("--raw-results",type=Path,required=True); rq.add_argument("--source-families-checked",required=True); rq.add_argument("--actor-classes-checked",required=True); rq.add_argument("--event-families-checked",required=True)
    rd=sub.add_parser("record-decision"); rd.add_argument("--state",type=Path,required=True); rd.add_argument("--work-state",type=Path,required=True); rd.add_argument("--section",required=True); rd.add_argument("--candidate-id",required=True); rd.add_argument("--decision",required=True); rd.add_argument("--reason",required=True); rd.add_argument("--direct-url"); rd.add_argument("--published-at"); rd.add_argument("--source-name")
    cs=sub.add_parser("close-section"); cs.add_argument("--state",type=Path,required=True); cs.add_argument("--work-state",type=Path,required=True); cs.add_argument("--section",required=True); cs.add_argument("--outcome",required=True); cs.add_argument("--below-target-reason")
    auth=sub.add_parser("authorize-render"); auth.add_argument("--state",type=Path,required=True); auth.add_argument("--work-state",type=Path,required=True); auth.add_argument("--ledger",type=Path,required=True); auth.add_argument("--model",type=Path,required=True); auth.add_argument("--registry",type=Path,required=True); auth.add_argument("--output",type=Path,required=True)
    render=sub.add_parser("render"); render.add_argument("--state",type=Path,required=True); render.add_argument("--work-state",type=Path,required=True); render.add_argument("--authorization",type=Path,required=True); render.add_argument("--ledger",type=Path,required=True); render.add_argument("--model",type=Path,required=True); render.add_argument("--registry",type=Path,required=True); render.add_argument("--template",type=Path,required=True); render.add_argument("--output",type=Path,required=True)
    final=sub.add_parser("finalize"); final.add_argument("--state",type=Path,required=True); final.add_argument("--work-state",type=Path,required=True); final.add_argument("--authorization",type=Path,required=True); final.add_argument("--ledger",type=Path,required=True); final.add_argument("--artifact",type=Path,required=True); final.add_argument("--template",type=Path,required=True); final.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(); helper=scripts()/"run_brief.py"
    if args.action=="init":
        receipt=load(args.reading_receipt)
        if receipt.get("purpose")!="full-package-reading-receipt" or not receipt.get("run_id"): raise SystemExit("invalid full-package reading receipt")
        call([sys.executable,str(scripts()/"verify_reading_receipt.py"),"--skill-dir",str(scripts().parent),"--receipt",str(args.reading_receipt),"--run-id",str(receipt["run_id"])],"reading gate")
        pipeline_id=uuid.uuid4().hex
        call([sys.executable,str(helper),"start-work","--plan",str(args.plan),"--profiles",str(args.profiles),"--pipeline-id",pipeline_id,"--output",str(args.work_state)],"work initialization")
        state={"kind":"zhixun-pipeline-state","schema_version":1,"pipeline_id":pipeline_id,"phase":"retrieval","created_at":now_cn(),"updated_at":now_cn(),"reading_receipt":str(args.reading_receipt.resolve()),"reading_receipt_sha256":sha(args.reading_receipt),"plan":str(args.plan.resolve()),"plan_sha256":sha(args.plan),"profiles":str(args.profiles.resolve()),"profiles_sha256":sha(args.profiles),"work_state":str(args.work_state.resolve()),"sealed_work_state_sha256":""}
        save(args.output,state); print(json.dumps({"ok":True,"pipeline":str(args.output.resolve()),"pipeline_id":pipeline_id,"next":json.loads(call([sys.executable,str(helper),"next","--state",str(args.work_state)],"next action"))},ensure_ascii=False)); return 0
    if args.action in ("next","status","seal-retrieval","verify"):
        state,work=verify_binding(args.state,args.work_state,require_sealed=(args.action=="verify" and args.require_sealed))
        output=call([sys.executable,str(helper),"next","--state",str(args.work_state)],"next action"); action=json.loads(output)
        if args.action=="next": print(output); return 0
        if args.action=="status":
            sections=work.get("sections") or []; closed=len([x for x in sections if x.get("outcome")]); candidates=sum(len(x.get("candidates") or []) for x in sections)
            print(json.dumps({"ok":True,"phase":state.get("phase"),"sections_closed":closed,"sections_total":len(sections),"candidate_count":candidates,"next":action},ensure_ascii=False,indent=2)); return 0
        if args.action=="seal-retrieval":
            if action.get("action")!="authorize_render": raise SystemExit("cannot seal retrieval; next required action: "+json.dumps(action,ensure_ascii=False))
            state["phase"]="retrieval-sealed"; state["sealed_at"]=now_cn(); state["sealed_work_state_sha256"]=sha(args.work_state); state["updated_at"]=now_cn(); save(args.state,state)
            print(json.dumps({"ok":True,"phase":"retrieval-sealed","work_state_sha256":state["sealed_work_state_sha256"]},ensure_ascii=False)); return 0
        print(json.dumps({"ok":True,"phase":state.get("phase"),"sealed":state.get("phase")=="retrieval-sealed","next":action},ensure_ascii=False)); return 0
    if args.action in ("record-query","record-decision","close-section"):
        state,work=verify_binding(args.state,args.work_state)
        if state.get("phase")!="retrieval": raise SystemExit("pipeline is sealed; retrieval mutations are forbidden")
        command=[sys.executable,str(helper),args.action,"--state",str(args.work_state),"--section",args.section]
        if args.action=="record-query":
            command += ["--lane",args.lane,"--query",args.query,"--route",args.route,"--raw-results",str(args.raw_results),"--source-families-checked",args.source_families_checked,"--actor-classes-checked",args.actor_classes_checked,"--event-families-checked",args.event_families_checked]
        elif args.action=="record-decision":
            command += ["--candidate-id",args.candidate_id,"--decision",args.decision,"--reason",args.reason]
            for key,value in (("--direct-url",args.direct_url),("--published-at",args.published_at),("--source-name",args.source_name)):
                if value: command += [key,value]
        else:
            command += ["--outcome",args.outcome]
            if args.below_target_reason: command += ["--below-target-reason",args.below_target_reason]
        output=call(command,args.action); print(output); return 0
    if args.action=="authorize-render":
        state,work=verify_binding(args.state,args.work_state,require_sealed=True)
        expected=len(work.get("sections") or [])
        command=[sys.executable,str(helper),"authorize-render","--work-state",str(args.work_state),"--pipeline-state",str(args.state),"--ledger",str(args.ledger),"--plan",state["plan"],"--model",str(args.model),"--registry",str(args.registry),"--expected-sections",str(expected),"--output",str(args.output)]
        print(call(command,"render authorization")); return 0
    if args.action=="render":
        verify_binding(args.state,args.work_state,require_sealed=True)
        auth_payload=load(args.authorization)
        if auth_payload.get("pipeline_state")!=str(args.state.resolve()) or auth_payload.get("model_sha256")!=sha(args.model) or auth_payload.get("ledger_sha256")!=sha(args.ledger) or auth_payload.get("registry_sha256")!=sha(args.registry): raise SystemExit("authorization does not bind the supplied pipeline/model/ledger/registry")
        command=[sys.executable,str(scripts()/"render_brief.py"),"--model",str(args.model),"--ledger",str(args.ledger),"--plan",load(args.state)["plan"],"--registry",str(args.registry),"--template",str(args.template),"--output",str(args.output)]
        print(call(command,"deterministic render")); return 0
    if args.action=="finalize":
        state,work=verify_binding(args.state,args.work_state,require_sealed=True)
        command=[sys.executable,str(helper),"finalize","--authorization",str(args.authorization),"--ledger",str(args.ledger),"--artifact",str(args.artifact),"--template",str(args.template),"--output",str(args.output)]
        # Do not mutate the sealed pipeline after authorization.  The formal
        # delivery receipt is the terminal record; changing the pipeline here
        # would invalidate the authorization's pipeline_state_sha256.
        print(call(command,"formal delivery")); return 0
    ap.error("choose init, next, status, seal-retrieval or verify")
if __name__=="__main__": sys.exit(main())
