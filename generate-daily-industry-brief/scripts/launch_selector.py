#!/usr/bin/env python3
"""Open the bundled selector and return the confirmed subscription JSON."""

import argparse
import json
import os
import re
import secrets
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from config_fingerprint import compute_config_fingerprint
from py36_compat import configure_utf8_stdio, isoformat_seconds
from verify_schedule import build_contract


SHANGHAI_TZ = timezone(timedelta(hours=8), "Asia/Shanghai")


MAX_BODY_BYTES = 64 * 1024
SUBSCRIPTION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
VALID_TOPIC_IDS = {
    "fintech", "sourcing", "matching", "employment", "overseas", "leadership",
    "enterprise", "capital", "digital", "informatization",
    "construction-tech", "government", "industry-data", "standards",
    "green", "extended",
}
MAX_CUSTOM_INTERESTS = 20
MAX_CUSTOM_INTEREST_LENGTH = 50


def default_state_file() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "zhixun-daily-brief" / "preferences.json"
    config_root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_root / "zhixun-daily-brief" / "preferences.json"


def load_state(path):
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("saved preferences must be a JSON object")
    return data


def save_state(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_custom_interests(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("custom_interests must be a list")
    if len(value) > MAX_CUSTOM_INTERESTS:
        raise ValueError(f"custom_interests must contain at most {MAX_CUSTOM_INTERESTS} values")
    normalized = []
    seen = set()
    for raw in value:
        raw_text = str(raw)
        if any(ord(character) < 32 for character in raw_text):
            raise ValueError("custom interest contains control characters")
        interest = " ".join(raw_text.split()).strip()
        if not interest:
            continue
        if len(interest) > MAX_CUSTOM_INTEREST_LENGTH:
            raise ValueError(f"custom interest exceeds {MAX_CUSTOM_INTEREST_LENGTH} characters")
        key = interest.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(interest)
    return normalized


def validate_submission(data, previous=None, force_update=False):
    if not isinstance(data, dict):
        raise ValueError("configuration must be a JSON object")
    topic_ids = data.get("topic_ids")
    if not isinstance(topic_ids, list) or len(topic_ids) > 16:
        raise ValueError("topic_ids must be a list containing at most 16 topics")
    if len(set(map(str, topic_ids))) != len(topic_ids):
        raise ValueError("topic_ids must not contain duplicates")
    unknown_topics = [str(topic_id) for topic_id in topic_ids if str(topic_id) not in VALID_TOPIC_IDS]
    if unknown_topics:
        raise ValueError("unknown topic_ids: " + ", ".join(unknown_topics))
    custom_interests = normalize_custom_interests(data.get("custom_interests"))
    if not topic_ids and not custom_interests:
        raise ValueError("choose a standard topic or add a custom interest")
    max_items = int(data.get("max_items_per_topic", 20))
    if not 1 <= max_items <= 20:
        raise ValueError("max_items_per_topic must be between 1 and 20")
    subscription_id = str(
        data.get("subscription_id")
        or (previous or {}).get("subscription_id")
        or "primary"
    )
    if not SUBSCRIPTION_ID_PATTERN.fullmatch(subscription_id):
        raise ValueError("invalid subscription_id")
    data["max_items_per_topic"] = max_items
    data["version"] = "4.22"
    data["lookback_hours"] = 24
    data["fallback_lookback_hours"] = 48
    data["fallback_policy"] = "extend_empty_sections"
    data["custom_interests"] = custom_interests
    data["subscription_id"] = subscription_id
    data["update_existing"] = True
    data["configuration_mode"] = "update" if previous or force_update else "create"
    if previous:
        data["previous_delivery_time"] = previous.get("delivery_time")
        data["previous_cadence"] = previous.get("cadence")
    data["create_schedule"] = True
    data["host"] = "universal"
    data["missed_run_policy"] = "catch_up_same_day"
    data["catch_up_dedupe"] = True
    data["schedule_contract"] = build_contract(
        str(data.get("cadence", "weekdays")),
        str(data.get("delivery_time", "08:30")),
        str(data.get("timezone", "Asia/Shanghai")),
    )
    return data


def build_automation_request(config: dict) -> dict:
    cadence_label = "每个工作日" if config.get("cadence") == "weekdays" else "每天"
    delivery_time = str(config.get("delivery_time", "08:30"))
    timezone = str(config.get("timezone", "Asia/Shanghai"))
    topic_names = "、".join(map(str, config.get("topics", []))) or "无"
    custom_names = "、".join(map(str, config.get("custom_interests", []))) or "无"
    subscription_id = str(config.get("subscription_id", "primary"))
    task_name = "知讯日报｜主订阅" if subscription_id == "primary" else f"知讯日报｜{subscription_id}"
    contract = config.get("schedule_contract") or build_contract(
        str(config.get("cadence", "weekdays")), delivery_time, timezone
    )
    normalized_json = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    prompt = (
        "使用已安装的 $generate-daily-industry-brief 生成知讯日报。"
        "先严格检索本次运行时点前滚动24小时内发布或发生的信息；某板块确认24小时内无合格信息时，才检索此前24至48小时区段；"
        "所有补充资讯必须标记为48小时补充，已有24小时内资讯的板块不得混入补充资讯，且不得扩展到72小时或近一周；"
        "优先采用政府、监管、交易所、采购平台、公司官网/投资者关系、官方活动实录等一手信源；"
        "每板块最多20条，数量不足时宁缺毋滥。"
        "必须按 references/retrieval-audit.md 先为全部标准板块和自定义兴趣完成广度优先检索，并按 references/retrieval-routing.md 对失败页面逐级切换搜索、浏览器、官方替代端点、事件相关方和权威媒体证据链；"
        "有可核验合格信息的板块按发现阈值完成；零结果查询和最新条目超出窗口的官方索引属于已完成检索证据，不得因此标记受限；"
        "搜索能发现事件但原网页打不开时不得立即标记受限或丢弃，必须完成替代证据链；普通事实可由一个可访问的官方替代记录或一个明确指向原始事件的权威行业/财经来源核验，重大或争议信息需要官方记录或两个独立权威来源；"
        "一条资讯同时真实关联多个已选板块时只保留一个主故事，并在其他相关板块显示带来源链接的关联资讯卡，不得因主板块去重让相关板块被误判为空；"
        "每个自定义兴趣必须独立执行精确字段、来源主体、官方记录和业务交叉四条路径，只有零或一条正式资讯时再做一次全国媒体、专业垂直或可靠镜像扩展；"
        "自定义板块不能仅靠关联资讯卡判定完成，只要存在直接相关合格事件就必须至少形成一条正式主资讯；"
        "只有发现路径和适用的核验替代路径均实际失败时才标记检索受限；"
        "不得把检索受限写成暂无动态，且存在检索受限板块时不得写入成功标记；"
        "读取订阅配置中的 custom_interests，并把每个值作为独立的自定义关注板块检索和输出，相关板块重叠时优先保证自定义板块有正式主资讯；"
        "最终必须在自动化工作空间生成完整、可独立打开的HTML5文件，"
        "文件名为 daily-industry-brief-YYYY-MM-DD.html，并在文末附逐板块检索审计；不得以Markdown代替。"
        "每次成功后用 scripts/mark_success.py 写入包含当前配置指纹的成功标记；"
        "只将同一订阅ID、上海日期和当前配置指纹均匹配的成功标记视为已经完成。"
        "每次宿主恢复或Agent启动时先运行 scripts/check_catchup.py；旧配置生成的同日HTML不得阻止当前配置补发。"
        f"订阅配置：{normalized_json}"
    )
    natural_language_request = (
        f"请立即更新或创建并启用订阅 {subscription_id}，稳定任务名为“{task_name}”。"
        "先按订阅配置中的 subscription_id 查找现有任务并原地更新。"
        "如旧任务没有 subscription_id，但只有一条名称以“知讯日报｜”开头的任务，将它迁移并改名为稳定任务名；禁止保留重复任务。"
        f"按{cadence_label} {delivery_time}（{timezone}，UTC+08:00）执行。"
        f"第一次运行必须是 {contract['expected_next_run_local']}，"
        f"对应 Unix 秒 {contract['expected_next_run_epoch']}。"
        "必须把 timezone、墙上时钟和绝对首跑时间写入宿主支持的真实调度字段；"
        "禁止只把时间写进任务名称。若宿主支持完整 RRULE，必须包含带时区的 DTSTART；"
        "若 Codex 本地 Automation 只接受裸 RRULE，必须原样使用所选本地小时、分钟和工作日，禁止换算成其他时间。"
        f"关注板块：{topic_names}。使用提示词字段中的完整提示词。"
        f"自定义兴趣：{custom_names}。必须把每个自定义兴趣作为独立日报板块检索和输出。"
        "创建后读取真实 nextRunAt 和后台最终持久化的循环规则，并使用 scripts/verify_schedule.py 同时校验两者。"
        "仅 nextRunAt 匹配但持久化规则不匹配时也必须判定失败。"
        "如果不匹配，立即修正同一任务并重新校验；最多重试两次。"
        "仍不匹配时停用错误任务并明确报告调度失败，绝不能声称部署成功。"
        "任务部署校验成功后，先用 scripts/record_config_state.py 保存当前配置与生效时间；"
        "若当前上海时间已经超过本次新设的当天计划时间，必须在同一轮立即运行 scripts/check_catchup.py，"
        "返回10时立即按当前配置补发一次，不得等待下一次循环。"
        "如果宿主支持开机、恢复或Agent启动触发器，将同一订阅的漏跑检查挂到该触发器；"
        "如果不支持，必须明确报告本地模式无法保证关机期间执行或开机即补发，并建议使用该宿主的云端调度器或操作系统任务计划。"
    )
    return {
        "action": "create_or_update_native_automation",
        "operation": config.get("configuration_mode", "upsert"),
        "subscription_id": subscription_id,
        "task_name": task_name,
        "schedule": {
            "cadence": config.get("cadence", "weekdays"),
            "time": delivery_time,
            "timezone": timezone,
            "first_run_at": contract["expected_next_run_local"],
            "first_run_epoch": contract["expected_next_run_epoch"],
            "cron_expression": contract["cron_expression"],
            "cron_timezone": contract["cron_timezone"],
            "rrule": contract["rrule"],
        },
        "schedule_contract": contract,
        "verification_command_template": (
            "python scripts/verify_schedule.py "
            f"--cadence {config.get('cadence', 'weekdays')} --time {delivery_time} "
            f"--timezone {timezone} --now {contract['contract_generated_at']} "
            "--reported-next-run <HOST_NEXT_RUN_AT> "
            "--reported-rrule <HOST_PERSISTED_RRULE>"
        ),
        "skill": "generate-daily-industry-brief",
        "delivery_channel": config.get("delivery_channel", "host-default"),
        "prompt": prompt,
        "natural_language_request": natural_language_request,
        "require_enabled_verification": True,
        "require_next_run_verification": True,
        "require_persisted_recurrence_verification": True,
    }


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--edit", action="store_true", help="reopen the full selector to edit an existing subscription")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--state-file", type=Path, default=default_state_file())
    parser.add_argument("--initial-config-file", type=Path)
    args = parser.parse_args()

    asset = Path(__file__).resolve().parent.parent / "assets" / "browser-subscription-selector.html"
    if not asset.is_file():
        print(f"selector asset not found: {asset}", file=sys.stderr)
        return 2

    try:
        initial_config = load_state(args.initial_config_file or args.state_file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ZHIXUN_STATE_WARNING=could not load saved preferences: {exc}", file=sys.stderr)
        initial_config = None
    asset_text = asset.read_text(encoding="utf-8")
    initial_json = json.dumps(initial_config or {}, ensure_ascii=False).replace("</", "<\\/")
    initial_json = initial_json.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    edit_json = "true" if args.edit else "false"
    bootstrap = f"<script>window.__ZHIXUN_INITIAL_CONFIG__={initial_json};window.__ZHIXUN_EDIT_MODE__={edit_json};</script>"
    page_body = asset_text.replace("</head>", bootstrap + "</head>", 1).encode("utf-8")

    token = secrets.token_urlsafe(24)
    state = {
        "config": None,
        "save_warning": None,
        "automation_request": None,
        "pending_file": None,
        "pending_warning": None,
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:
            return

        def send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def authorized(self) -> bool:
            query = parse_qs(urlparse(self.path).query)
            return query.get("token", [""])[0] == token

        def do_GET(self) -> None:  # noqa: N802
            if not self.authorized():
                self.send_json(403, {"ok": False, "error": "invalid token"})
                return
            body = page_body
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/submit" or not self.authorized():
                self.send_json(403, {"ok": False, "error": "invalid request"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                self.send_json(413, {"ok": False, "error": "invalid body size"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                config = validate_submission(payload, initial_config, force_update=args.edit)
                submitted_at = isoformat_seconds(datetime.now(SHANGHAI_TZ))
                config["configuration_effective_at"] = submitted_at
                config["config_fingerprint"] = compute_config_fingerprint(config)
                try:
                    save_state(args.state_file, config)
                except OSError as exc:
                    state["save_warning"] = str(exc)
                automation_request = build_automation_request(config)
                state["automation_request"] = automation_request
                pending_path = args.state_file.parent / f"pending-deployment-{config['subscription_id']}.json"
                pending = {
                    "subscription_id": config["subscription_id"],
                    "submitted_at": submitted_at,
                    "config": config,
                    "automation_request": automation_request,
                    "consumed": False,
                }
                try:
                    temp_path = pending_path.with_suffix(".tmp")
                    temp_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
                    temp_path.replace(pending_path)
                    state["pending_file"] = pending_path.resolve()
                except OSError as exc:
                    state["pending_warning"] = str(exc)
                state["config"] = config
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                self.send_json(400, {"ok": False, "error": str(exc)})
                return
            self.send_json(200, {"ok": True, "saved": state["save_warning"] is None})

    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 0.2
    url = f"http://127.0.0.1:{server.server_port}/?token={token}"
    print(f"ZHIXUN_SELECTOR_MODE={'update' if initial_config or args.edit else 'create'}", flush=True)
    print(f"ZHIXUN_SELECTOR_INTENT={'edit' if args.edit else 'setup'}", flush=True)
    print(f"ZHIXUN_SELECTOR_URL={url}", flush=True)
    if not args.no_open:
        webbrowser.open(url, new=1)

    deadline = time.monotonic() + max(30, args.timeout)
    while state["config"] is None and time.monotonic() < deadline:
        server.handle_request()

    config = state["config"]
    if config is None:
        server.server_close()
        print("selector timed out before confirmation", file=sys.stderr)
        return 3
    if args.output:
        args.output.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    if state["save_warning"]:
        print(f"ZHIXUN_STATE_WARNING=could not persist preferences: {state['save_warning']}", file=sys.stderr)
    else:
        print(f"ZHIXUN_STATE_FILE={args.state_file}", flush=True)
    if state["pending_warning"]:
        print(f"ZHIXUN_STATE_WARNING=could not persist pending deployment: {state['pending_warning']}", file=sys.stderr)
    elif state["pending_file"] is not None:
        print(f"ZHIXUN_PENDING_FILE={state['pending_file']}", flush=True)
    print("ZHIXUN_CONFIG=" + json.dumps(config, ensure_ascii=True, separators=(",", ":")), flush=True)
    automation_request = state["automation_request"]
    if automation_request is None:
        automation_request = build_automation_request(config)
    print(
        "ZHIXUN_AUTOMATION_REQUEST="
        + json.dumps(automation_request, ensure_ascii=True, separators=(",", ":")),
        flush=True,
    )
    server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
