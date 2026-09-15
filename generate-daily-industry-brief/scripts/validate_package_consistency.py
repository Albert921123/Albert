#!/usr/bin/env python3
"""Fail when package versions, required files, or hard-gate docs drift apart."""
from __future__ import print_function
import argparse, ast, json, re, sys
from pathlib import Path
from py36_compat import configure_utf8_stdio

PYTHON_FILES=(
    "scripts/run_pipeline.py","scripts/run_brief.py","scripts/prepare_run_plan.py",
    "scripts/validate_retrieval_ledger.py","scripts/validate_source_registry.py",
    "scripts/validate_brief_model.py","scripts/validate_html.py",
)
REQUIRED_PHRASES={
    "SKILL.md":("run_pipeline.py","authorize-render","finalize","--profiles","source registry"),
    "references/anti-shortcut-execution.md":("actor_classes_checked","event_families_checked","authorize-render"),
    "entrypoints/通用调用提示词.txt":("run_pipeline.py","authorize-render","finalize"),
}

def main():
    configure_utf8_stdio(); ap=argparse.ArgumentParser(); ap.add_argument("--skill-dir",type=Path,default=Path(__file__).resolve().parent.parent); args=ap.parse_args()
    root=args.skill_dir.resolve(); issues=[]
    try: manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok":False,"issues":["cannot read manifest: %s"%exc]},ensure_ascii=False,indent=2)); return 2
    version=str(manifest.get("distribution_version") or ""); core=str(manifest.get("core_version") or "")
    for rel in manifest.get("required_files") or []:
        if not (root/rel).is_file(): issues.append("manifest required file missing: "+rel)
    readme=(root/"README.md").read_text(encoding="utf-8")
    latest=(root/"当前最新版说明.txt").read_text(encoding="utf-8")
    verifier=(root/"scripts/verify_install.py").read_text(encoding="utf-8")
    if ("Skill 版本：`%s`"%version) not in readme: issues.append("README distribution version mismatch")
    if ("核心规则版本：`%s`"%core) not in readme: issues.append("README core version mismatch")
    if ("版本：v%s"%version) not in latest: issues.append("latest-note distribution version mismatch")
    if ("核心规则：v%s"%core) not in latest: issues.append("latest-note core version mismatch")
    if ('default="%s"'%version) not in verifier: issues.append("verify_install default version mismatch")
    for rel,phrases in REQUIRED_PHRASES.items():
        text=(root/rel).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text: issues.append("%s missing current contract phrase: %s"%(rel,phrase))
    for rel in PYTHON_FILES:
        path=root/rel
        if not path.is_file(): issues.append("hard-gate script missing: "+rel); continue
        try: ast.parse(path.read_text(encoding="utf-8"))
        except Exception as exc: issues.append("python syntax failure %s: %s"%(rel,exc))
    if ".zhixun-state" not in (root/".gitignore").read_text(encoding="utf-8"):
        issues.append("runtime state is not excluded from portable package")
    print(json.dumps({"ok":not issues,"distribution_version":version,"core_version":core,"issues":issues},ensure_ascii=False,indent=2))
    return 0 if not issues else 2
if __name__=="__main__": sys.exit(main())
