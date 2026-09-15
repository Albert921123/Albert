#!/usr/bin/env python3
"""Persist and report a single 知讯日报 run state.

It deliberately does not search or render. Host-native search and browser tools
remain under the Agent's control; this helper prevents a draft from being
described as a completed delivery before the evidence and artifact gates pass.
"""
from __future__ import print_function

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from py36_compat import configure_utf8_stdio

PHASES = ("full-package-reading", "capability-preflight", "candidate-discovery",
          "original-page-verification", "full-section-ledger", "html-render",
          "validation", "delivered")
ACTIVE = {"running", "blocked"}
FINAL_OUTCOMES = {"complete", "observed", "expanded", "business-observation", "checked-empty", "limited", "baseline"}


def now_iso():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("cannot read state file: %s" % exc)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, str(path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def phase_index(value):
    if value not in PHASES:
        raise SystemExit("unknown phase: %s" % value)
    return PHASES.index(value)


def planned_section_ids(state):
    """Read the immutable queue attached to this run, when present."""
    plan_path = state.get("execution_plan") or ""
    if not plan_path:
        return []
    try:
        payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("cannot read execution plan: %s" % exc)
    rows = payload.get("sections") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise SystemExit("execution plan has no section array")
    values = []
    for row in rows:
        value = row.get("section_id") if isinstance(row, dict) else None
        if not isinstance(value, str) or not value.strip():
            raise SystemExit("execution plan contains an invalid section id")
        values.append(value.strip())
    if len(values) != len(set(values)):
        raise SystemExit("execution plan contains duplicate section ids")
    return values


def ensure_closure_ready(state):
    """Prevent a delivery/HTML phase from bypassing unfinished planned rows."""
    section_ids = planned_section_ids(state)
    if not section_ids:
        raise SystemExit("closure requires an attached deterministic execution plan")
    progress = state.get("section_progress") or {}
    unresolved = []
    for section_id in section_ids:
        outcome = (progress.get(section_id) or {}).get("outcome")
        if outcome not in FINAL_OUTCOMES:
            unresolved.append(section_id)
    if unresolved:
        raise SystemExit("planned sections lack final outcomes: %s" % ", ".join(unresolved))
    if state.get("pending_sections"):
        raise SystemExit("delivery blocked while pending sections remain: %s" % ", ".join(state.get("pending_sections")))


def run_gate(command, label):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if result.returncode != 0:
        raise SystemExit("%s failed; phase transition blocked:\n%s" % (label, result.stdout.strip()))


def make_feedback(state):
    output = {"run_id": state.get("run_id"), "report_date": state.get("report_date"),
              "phase": state.get("phase"), "updated_at": state.get("updated_at")}
    if state.get("status") == "delivered":
        output.update({"result": "已交付", "artifact": state.get("artifact"), "ledger": state.get("ledger"),
                       "validated_gates": state.get("validated_gates"), "message": "1—7 步均已通过；可使用正式 HTML。"})
    elif state.get("status") == "blocked" and state.get("requires_human"):
        output.update({"result": "未交付，需人工处理", "reason": state.get("reason"),
                       "pending_sections": state.get("pending_sections", []), "next_action": state.get("next_action")})
    else:
        phase = state.get("phase")
        output.update({"result": "未交付，待续跑", "reason": state.get("reason"),
                       "completed_phases": list(PHASES[:phase_index(phase)]),
                       "next_phase": phase, "pending_sections": state.get("pending_sections", []),
                       "next_action": state.get("next_action") or "从当前阶段继续；不得将此状态描述为后台运行或已交付。"})
    return output


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Persist a 知讯日报 run state")
    parser.add_argument("action", choices=("start", "advance", "resume", "checkpoint", "block", "deliver", "status"))
    parser.add_argument("--state-dir", type=Path, default=Path(".zhixun-state"))
    parser.add_argument("--report-date")
    parser.add_argument("--run-id")
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--selected-sections", type=int)
    parser.add_argument("--config-fingerprint")
    parser.add_argument("--plan")
    parser.add_argument("--section", action="append", default=[], help="section-id=checkpoint; repeatable")
    parser.add_argument("--section-outcome", action="append", default=[], help="section-id=final outcome; repeatable")
    parser.add_argument("--reason")
    parser.add_argument("--needs-human", action="store_true")
    parser.add_argument("--next-action")
    parser.add_argument("--pending", action="append", default=[])
    parser.add_argument("--ledger")
    parser.add_argument("--artifact")
    parser.add_argument("--template")
    parser.add_argument("--ledger-gate")
    parser.add_argument("--html-gate")
    parser.add_argument("--editorial-gate")
    parser.add_argument("--delivery-gate")
    args = parser.parse_args()

    if args.action == "start":
        if not args.report_date or not args.run_id or not args.selected_sections:
            raise SystemExit("start needs --report-date, --run-id and --selected-sections")
        path = args.state_dir / "runs" / ("run-%s-%s.json" % (args.report_date, args.run_id))
        if path.exists():
            raise SystemExit("run state already exists: %s" % path)
        state = {"schema_version": 1, "run_id": args.run_id, "report_date": args.report_date,
                 "config_fingerprint": args.config_fingerprint or "", "selected_sections": args.selected_sections,
                 "status": "running", "phase": "full-package-reading", "started_at": now_iso(),
                 "updated_at": now_iso(), "history": [], "pending_sections": [],
                 "execution_plan": args.plan or "", "section_progress": {}}
        state["history"].append({"phase": state["phase"], "at": now_iso(), "note": "run created"})
        write_json(path, state)
        print(json.dumps({"state_file": str(path), "feedback": make_feedback(state)}, ensure_ascii=False, indent=2))
        return 0

    if not args.state_file:
        raise SystemExit("%s needs --state-file" % args.action)
    state = read_json(args.state_file)
    current = state.get("phase")
    phase_index(current)
    if args.action == "resume":
        if state.get("status") != "blocked":
            raise SystemExit("resume needs a blocked state")
        state.update({"status": "running", "updated_at": now_iso(), "reason": None, "next_action": None})
        # A v1.35 state may predate deterministic run plans.  Attach a plan
        # during its first v1.36 resume instead of forcing a new state file.
        if args.plan:
            state["execution_plan"] = args.plan
        state["history"].append({"phase": current, "at": now_iso(), "note": "resumed from blocked state"})
    elif args.action == "advance":
        if state.get("status") not in ACTIVE or not args.phase:
            raise SystemExit("advance needs an active state and --phase")
        if phase_index(args.phase) != phase_index(current) + 1:
            raise SystemExit("phase transition must advance exactly one step: %s -> %s" % (current, args.phase))
        if args.phase == "html-render":
            ensure_closure_ready(state)
            if not args.ledger:
                raise SystemExit("html-render requires --ledger; a few discovered items cannot bypass full-section ledger closure")
            plan = state.get("execution_plan") or ""
            command = [sys.executable, str(Path(__file__).with_name("validate_retrieval_ledger.py")), args.ledger,
                       "--expected-sections", str(state.get("selected_sections")), "--plan", plan]
            run_gate(command, "full-section ledger gate")
            run_gate([sys.executable, str(Path(__file__).with_name("validate_time_window.py")), args.ledger], "time-window gate")
            state["validated_ledger"] = args.ledger
        state.update({"status": "running", "phase": args.phase, "updated_at": now_iso(), "reason": None, "next_action": None})
        state["history"].append({"phase": args.phase, "at": now_iso(), "note": "completed previous phase"})
    elif args.action == "checkpoint":
        if state.get("status") not in ACTIVE or (not args.section and not args.section_outcome):
            raise SystemExit("checkpoint needs an active state and one or more section updates")
        progress = state.setdefault("section_progress", {})
        allowed = set(planned_section_ids(state))
        for value in args.section:
            if "=" not in value:
                raise SystemExit("--section must be section-id=checkpoint")
            section_id, checkpoint = value.split("=", 1)
            if not section_id.strip() or not checkpoint.strip():
                raise SystemExit("--section must contain non-empty section id and checkpoint")
            if allowed and section_id.strip() not in allowed:
                raise SystemExit("checkpoint references a section outside the execution plan: %s" % section_id.strip())
            progress[section_id.strip()] = {"checkpoint": checkpoint.strip(), "at": now_iso()}
        for value in args.section_outcome:
            if "=" not in value:
                raise SystemExit("--section-outcome must be section-id=final-outcome")
            section_id, outcome = value.split("=", 1)
            section_id, outcome = section_id.strip(), outcome.strip()
            if not section_id or outcome not in FINAL_OUTCOMES:
                raise SystemExit("--section-outcome needs a planned section and a valid final outcome")
            if allowed and section_id not in allowed:
                raise SystemExit("section outcome references a section outside the execution plan: %s" % section_id)
            record = progress.setdefault(section_id, {})
            record.update({"outcome": outcome, "outcome_at": now_iso()})
        state.update({"updated_at": now_iso(), "reason": args.reason or state.get("reason")})
        state["history"].append({"phase": current, "at": now_iso(), "note": "section checkpoint updated"})
    elif args.action == "block":
        if state.get("status") not in ACTIVE or not args.reason:
            raise SystemExit("block needs an active state and --reason")
        state.update({"status": "blocked", "updated_at": now_iso(), "reason": args.reason,
                      "next_action": args.next_action or "从当前阶段继续。", "pending_sections": args.pending or state.get("pending_sections", []),
                      "requires_human": bool(args.needs_human)})
        state["history"].append({"phase": current, "at": now_iso(), "note": "blocked: " + args.reason})
    elif args.action == "deliver":
        gates = {"ledger": args.ledger_gate, "html": args.html_gate, "editorial": args.editorial_gate, "delivery": args.delivery_gate}
        if current != "validation" or state.get("status") not in ACTIVE or not args.ledger or not args.artifact or any(value != "passed" for value in gates.values()):
            raise SystemExit("delivery requires validation phase, artifact/ledger and four passed gates")
        ensure_closure_ready(state)
        if state.get("validated_ledger") != args.ledger:
            raise SystemExit("delivery ledger differs from the ledger validated before HTML rendering")
        if not args.template:
            raise SystemExit("delivery requires --template so the four gates can be rerun, not self-attested")
        run_gate([sys.executable, str(Path(__file__).with_name("validate_retrieval_ledger.py")), args.ledger,
                  "--expected-sections", str(state.get("selected_sections")), "--plan", state.get("execution_plan")], "ledger gate")
        run_gate([sys.executable, str(Path(__file__).with_name("validate_time_window.py")), args.ledger], "time-window gate")
        run_gate([sys.executable, str(Path(__file__).with_name("validate_html.py")), args.artifact, "--ledger", args.ledger], "HTML gate")
        run_gate([sys.executable, str(Path(__file__).with_name("verify_editorial_gate.py")), args.artifact], "editorial gate")
        run_gate([sys.executable, str(Path(__file__).with_name("verify_delivery_gate.py")), args.artifact, "--template", args.template], "delivery gate")
        state.update({"status": "delivered", "phase": "delivered", "updated_at": now_iso(), "delivered_at": now_iso(),
                      "ledger": args.ledger, "artifact": args.artifact, "validated_gates": gates, "pending_sections": []})
        state["history"].append({"phase": "delivered", "at": now_iso(), "note": "all gates passed"})
    write_json(args.state_file, state)
    print(json.dumps({"state_file": str(args.state_file), "feedback": make_feedback(state)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
