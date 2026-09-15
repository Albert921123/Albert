#!/usr/bin/env python3
"""Validate candidate source claims against the portable source registry."""
from __future__ import print_function
import argparse, json, re, sys
from pathlib import Path
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from py36_compat import configure_utf8_stdio

GENERIC_FAMILIES={"websearch","search","news","media","internet","网络搜索","多个媒体","混合来源"}

def host_of(value):
    try: return (urlparse(str(value or "")).hostname or "").lower().rstrip(".")
    except Exception: return ""

def matches(host, domain, mode):
    domain=str(domain or "").lower().lstrip(".")
    if not host or not domain: return False
    return host==domain or (mode=="suffix" and host.endswith("."+domain))

def main():
    configure_utf8_stdio()
    ap=argparse.ArgumentParser()
    ap.add_argument("ledger",type=Path)
    ap.add_argument("--registry",type=Path,required=True)
    args=ap.parse_args(); issues=[]
    try:
        ledger=json.loads(args.ledger.read_text(encoding="utf-8"))
        registry=json.loads(args.registry.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok":False,"issues":["cannot read ledger/registry: %s"%exc]},ensure_ascii=False,indent=2)); return 2
    allowed=set(registry.get("allowed_source_classes") or [])
    entries=registry.get("sources") or []
    if not allowed or not isinstance(entries,list): issues.append("source registry is incomplete")
    for index,item in enumerate(ledger.get("candidates") or []):
        p="candidate[%d]"%index
        source_class=str(item.get("source_class") or "").strip()
        if source_class not in allowed: issues.append(p+" has invalid or missing source_class")
        family=str(item.get("source_family_id") or "").strip()
        if not family or family.lower() in GENERIC_FAMILIES: issues.append(p+" has generic source_family_id")
        host=host_of(item.get("direct_record_url") or item.get("url"))
        if not host: issues.append(p+" has no verifiable source host"); continue
        found=[]
        for entry in entries:
            if any(matches(host,d,entry.get("match","suffix")) for d in (entry.get("domains") or [])): found.append(entry)
        official_claim=source_class=="official-or-regulatory" or item.get("direct_record_kind")=="official-record"
        tier1=str(item.get("source_tier") or "").upper()=="T1"
        exception=item.get("source_registry_exception") if isinstance(item.get("source_registry_exception"),dict) else {}
        reason=str(exception.get("reason") or "").strip()
        evidence_host=host_of(exception.get("evidence_url"))
        valid_exception=len(reason)>=int((registry.get("policy") or {}).get("unregistered_exception_min_reason_chars",20)) and evidence_host==host
        if official_claim and not any("official-or-regulatory" in (x.get("classes") or []) for x in found):
            issues.append(p+" claims official/regulatory status for an unregistered domain: "+host)
        if tier1 and not found and not valid_exception:
            issues.append(p+" claims T1 for an unregistered domain without a same-domain evidence exception: "+host)
        if found and source_class and not any(source_class in (x.get("classes") or []) for x in found):
            issues.append(p+" source_class conflicts with registry for domain: "+host)
    print(json.dumps({"ok":not issues,"ledger":str(args.ledger.resolve()),"registry_version":registry.get("registry_version"),"candidate_count":len(ledger.get("candidates") or []),"issues":issues},ensure_ascii=False,indent=2))
    return 0 if not issues else 2
if __name__=="__main__": sys.exit(main())
