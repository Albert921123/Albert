#!/usr/bin/env python3
"""Block delivery when a brief replaced the approved application shell."""
from __future__ import print_function
import argparse, hashlib, json, re, sys
from pathlib import Path

REQUIRED_IDS=("brief-search","clear-search","search-status","topic-nav","content-scroll","no-results","management-map")
REQUIRED_CLASSES=("app-shell","topbar","brand","highlights","highlights-label","topic-nav","section","coverage-audit","audit-body","audit-grid")
MARKERS=("filterBrief","searchableUnits","ResizeObserver","scrollIntoView","Enter")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("html_file",type=Path)
    p.add_argument("--template",type=Path,required=True)
    a=p.parse_args()
    issues=[]
    try:
        template=a.template.read_text(encoding="utf-8")
        html=a.html_file.read_text(encoding="utf-8")
    except Exception as exc:
        print(json.dumps({"ok":False,"issues":["cannot read file: %s"%exc]},ensure_ascii=False,indent=2)); return 2
    for value in REQUIRED_IDS:
        if len(re.findall(r'id\s*=\s*["\']%s["\']'%re.escape(value),html))!=1: issues.append("missing or duplicate required id: "+value)
    for value in REQUIRED_CLASSES:
        if not re.search(r'class\s*=\s*["\'][^"\']*\b%s\b'%re.escape(value),html): issues.append("missing required application-shell class: "+value)
    script="\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>",html,re.I|re.S))
    for value in MARKERS:
        if value not in script: issues.append("search/navigation script is missing marker: "+value)
    if "coverage-audit" not in template or "management-map" not in template: issues.append("approved template lacks required shell markers")
    if "今日推荐关注" not in html: issues.append("missing 今日推荐关注")
    for marker in ("管理层动作清单", "management-actions", "today-signals"):
        if marker in html: issues.append("obsolete management-action block is present: "+marker)
    if re.search(r"chain-steps\\s+li:not\\(:last-child\\)::after\\s*\\{[^}]*content\\s*:\\s*['\\\"](?:→|↓)", html):
        issues.append("recommendation cards contain obsolete directional arrows")
    print(json.dumps({"ok":not issues,"html_file":str(a.html_file.resolve()),"template_sha256":hashlib.sha256(template.encode("utf-8")).hexdigest(),"issues":issues},ensure_ascii=False,indent=2))
    return 0 if not issues else 2
if __name__=="__main__": sys.exit(main())
