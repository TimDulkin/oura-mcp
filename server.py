#!/usr/bin/env python3
"""
Oura MCP server — all Oura Ring API v2 endpoints exposed as Claude tools.

Pure Python stdlib. No pip, no venv, no dependencies — runs on any
macOS/Linux python3 (3.9+). Implements the MCP stdio transport directly:
newline-delimited JSON-RPC 2.0 over stdin/stdout.

Token: OURA_TOKEN env var (preferred, set it in the Claude config snippet)
or ~/.config/oura-mcp/token.
"""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from client import OuraClient

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "oura", "version": "2.0.0"}

# ---------------------------------------------------------------------------
# Client (lazy — so tools/list works even before the token is configured,
# and a missing token surfaces as a readable error in chat, not a dead server)
# ---------------------------------------------------------------------------

_client: Optional[OuraClient] = None


def client() -> OuraClient:
    global _client
    if _client is None:
        _client = OuraClient()
    return _client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_or_none(payload: dict) -> Optional[dict]:
    """Oura returns {"data": [<one item>]} for single-day queries."""
    items = payload.get("data") or []
    return items[0] if items else None


def _resolve_date(d: Optional[str]) -> str:
    return d or client().yesterday()


DATE_PARAM = {
    "type": "object",
    "properties": {
        "date": {
            "type": "string",
            "description": "Date in YYYY-MM-DD format. Defaults to yesterday.",
        }
    },
    "required": [],
}


def _range_param(default_desc: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "YYYY-MM-DD"},
        },
        "required": [],
        "description": default_desc,
    }


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def oura_today(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {
        "date": d,
        "sleep": _first_or_none(client().request("daily_sleep", {"start_date": d, "end_date": d})),
        "readiness": _first_or_none(client().request("daily_readiness", {"start_date": d, "end_date": d})),
        "activity": _first_or_none(client().request("daily_activity", {"start_date": d, "end_date": d})),
    }


def oura_sleep(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "sessions": client().request("sleep", {"start_date": d, "end_date": d}).get("data", [])}


def oura_readiness(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "readiness": _first_or_none(client().request("daily_readiness", {"start_date": d, "end_date": d}))}


def oura_activity(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "activity": _first_or_none(client().request("daily_activity", {"start_date": d, "end_date": d}))}


def oura_stress(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "stress": _first_or_none(client().request("daily_stress", {"start_date": d, "end_date": d}))}


def oura_resilience(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "resilience": _first_or_none(client().request("daily_resilience", {"start_date": d, "end_date": d}))}


def oura_spo2(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "spo2": _first_or_none(client().request("daily_spo2", {"start_date": d, "end_date": d}))}


def oura_cardiovascular_age(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "cardiovascular_age": _first_or_none(client().request("daily_cardiovascular_age", {"start_date": d, "end_date": d}))}


def oura_vo2_max(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "vo2_max": _first_or_none(client().request("vo2_max", {"start_date": d, "end_date": d}))}


def oura_workouts(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    s = start_date or _resolve_date(None)
    e = end_date or s
    return {"range": [s, e], "workouts": client().request("workout", {"start_date": s, "end_date": e}).get("data", [])}


def oura_sessions(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    s = start_date or _resolve_date(None)
    e = end_date or s
    return {"range": [s, e], "sessions": client().request("session", {"start_date": s, "end_date": e}).get("data", [])}


def oura_heart_rate(start_datetime: Optional[str] = None, end_datetime: Optional[str] = None) -> dict:
    if not end_datetime:
        end_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if not start_datetime:
        start_datetime = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "range": [start_datetime, end_datetime],
        "samples": client().request("heartrate", {"start_datetime": start_datetime, "end_datetime": end_datetime}).get("data", []),
    }


def oura_tags(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    s = start_date or client().days_ago(6)
    e = end_date or client().days_ago(0)
    return {"range": [s, e], "tags": client().request("enhanced_tag", {"start_date": s, "end_date": e}).get("data", [])}


def oura_sleep_time(date: Optional[str] = None) -> dict:
    d = _resolve_date(date)
    return {"date": d, "sleep_time": _first_or_none(client().request("sleep_time", {"start_date": d, "end_date": d}))}


def oura_rest_mode(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    s = start_date or client().days_ago(6)
    e = end_date or client().days_ago(0)
    return {"range": [s, e], "periods": client().request("rest_mode_period", {"start_date": s, "end_date": e}).get("data", [])}


def oura_trends(days: int = 7) -> dict:
    days = int(days)
    if days < 1 or days > 60:
        raise ValueError("days must be between 1 and 60")
    start, end = client().days_ago(days - 1), client().days_ago(0)
    sleep = client().request("daily_sleep", {"start_date": start, "end_date": end}).get("data", [])
    readiness = client().request("daily_readiness", {"start_date": start, "end_date": end}).get("data", [])
    sleep_by_day = {row["day"]: row["score"] for row in sleep if "day" in row}
    rdy_by_day = {row["day"]: row["score"] for row in readiness if "day" in row}
    days_set = sorted(set(sleep_by_day) | set(rdy_by_day))
    return {
        "range": [start, end],
        "rows": [
            {"date": d, "sleep_score": sleep_by_day.get(d), "readiness_score": rdy_by_day.get(d)}
            for d in days_set
        ],
    }


def oura_temp_trend(days: int = 14) -> dict:
    days = int(days)
    if days < 1 or days > 60:
        raise ValueError("days must be between 1 and 60")
    start, end = client().days_ago(days - 1), client().days_ago(0)
    rows = client().request("daily_readiness", {"start_date": start, "end_date": end}).get("data", [])
    return {
        "range": [start, end],
        "rows": sorted(
            (
                {
                    "date": r.get("day"),
                    "temperature_deviation": r.get("temperature_deviation"),
                    "temperature_trend_deviation": r.get("temperature_trend_deviation"),
                }
                for r in rows if r.get("day")
            ),
            key=lambda x: x["date"],
        ),
    }


def oura_personal_info() -> dict:
    return client().request("personal_info")


def oura_ring_configuration() -> dict:
    return {"rings": client().request("ring_configuration").get("data", [])}


# ---------------------------------------------------------------------------
# Tool registry: name -> (function, description, input schema)
# ---------------------------------------------------------------------------

TOOLS: dict[str, tuple[Callable[..., dict], str, dict]] = {
    "oura_today": (
        oura_today,
        "Snapshot for one day: sleep score, readiness score, temperature deviation, "
        "and basic activity. Defaults to yesterday. Use this for the morning check-in.",
        DATE_PARAM,
    ),
    "oura_sleep": (
        oura_sleep,
        "Detailed sleep session for a date: total/REM/deep/light durations, latency, "
        "efficiency, average HR, lowest HR, average HRV, breath rate. Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_readiness": (
        oura_readiness,
        "Readiness for a date: score, contributors (HRV balance, recovery index, "
        "sleep balance, body temperature), and temperature_deviation in Celsius. "
        "Useful for catching early illness or cycle effects. Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_activity": (
        oura_activity,
        "Daily activity summary: score, active calories, steps, total calories, "
        "contributors (meet_daily_targets, move_every_hour, recovery_time, stay_active, "
        "training_frequency, training_volume). Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_stress": (
        oura_stress,
        "Daytime stress and recovery levels for a date. stress_high_seconds = total time "
        "at high stress, recovery_high_seconds = time at high recovery. Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_resilience": (
        oura_resilience,
        "Long-term resilience score for a date — multi-week capacity to handle stress. "
        "Returns level (exceptional/strong/solid/adequate/limited) and contributors "
        "(sleep_recovery, daytime_recovery, stress). Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_spo2": (
        oura_spo2,
        "Average overnight blood oxygen (SpO2) percentage for a date. "
        "Useful for sleep apnea / hypoxia signals. Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_cardiovascular_age": (
        oura_cardiovascular_age,
        "Daily cardiovascular age — Oura's predicted vascular age (18-100). "
        "Compare with biological age to gauge heart health. Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_vo2_max": (
        oura_vo2_max,
        "VO2 max estimate for a date. Higher is better — elite athletes are 60+, "
        "average adults 30-40. Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_workouts": (
        oura_workouts,
        "Auto-detected workouts for a date range. Includes type (running, cycling, gym...), "
        "HR average/max, calories, distance, intensity. Defaults to yesterday.",
        _range_param("Date range, defaults to yesterday."),
    ),
    "oura_sessions": (
        oura_sessions,
        "Guided sessions (meditation, breathing, nap, relaxation, rest, body_status) "
        "for a date range. Includes HR, HRV, mood, motion count. Defaults to yesterday.",
        _range_param("Date range, defaults to yesterday."),
    ),
    "oura_heart_rate": (
        oura_heart_rate,
        "5-minute heart rate samples for a datetime window. Each sample has bpm and source "
        "(awake/rest/sleep/session/workout). NOTE: uses start_datetime/end_datetime "
        "(ISO 8601), not dates. Defaults to the last 24 hours.",
        {
            "type": "object",
            "properties": {
                "start_datetime": {"type": "string", "description": "ISO 8601 datetime"},
                "end_datetime": {"type": "string", "description": "ISO 8601 datetime"},
            },
            "required": [],
        },
    ),
    "oura_tags": (
        oura_tags,
        "Enhanced tags for a date range — user-created tags with optional comments "
        "and duration. Defaults to last 7 days.",
        _range_param("Date range, defaults to last 7 days."),
    ),
    "oura_sleep_time": (
        oura_sleep_time,
        "Sleep time recommendation for a date: optimal bedtime window and status "
        "(optimal_found, not_enough_nights, etc.). Defaults to yesterday.",
        DATE_PARAM,
    ),
    "oura_rest_mode": (
        oura_rest_mode,
        "Rest mode periods for a date range — when the user activated rest mode "
        "(e.g. sick days, recovery). Includes episodes with tags. Defaults to last 7 days.",
        _range_param("Date range, defaults to last 7 days."),
    ),
    "oura_trends": (
        oura_trends,
        "Sleep score and readiness score for the last N days (default 7). "
        "Returns a list ordered oldest to newest. Useful for weekly review.",
        {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "1-60, default 7"}},
            "required": [],
        },
    ),
    "oura_temp_trend": (
        oura_temp_trend,
        "Temperature deviation for the last N days (default 14). Useful for tracking "
        "cycle phase, illness onset, or post-training recovery. Celsius, oldest to newest.",
        {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "1-60, default 14"}},
            "required": [],
        },
    ),
    "oura_personal_info": (
        oura_personal_info,
        "Personal info: age, weight, height, biological sex, email. "
        "No date parameter — returns current profile.",
        {"type": "object", "properties": {}, "required": []},
    ),
    "oura_ring_configuration": (
        oura_ring_configuration,
        "Ring configuration: model (gen2/gen3/gen4), color, size, firmware version.",
        {"type": "object", "properties": {}, "required": []},
    ),
}


# ---------------------------------------------------------------------------
# MCP stdio transport: newline-delimited JSON-RPC 2.0
# ---------------------------------------------------------------------------

def _send(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def _result(req_id: Any, result: dict) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _error(req_id: Any, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _handle(request: dict) -> None:
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params") or {}

    is_notification = "id" not in request

    if method == "initialize":
        _result(req_id, {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    elif method == "notifications/initialized":
        pass  # notification, no response
    elif method == "ping":
        _result(req_id, {})
    elif method == "tools/list":
        _result(req_id, {
            "tools": [
                {"name": name, "description": desc, "inputSchema": schema}
                for name, (_, desc, schema) in TOOLS.items()
            ]
        })
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in TOOLS:
            _error(req_id, -32602, f"Unknown tool: {name}")
            return
        fn = TOOLS[name][0]
        try:
            output = fn(**arguments)
            _result(req_id, {
                "content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False, default=str)}],
                "isError": False,
            })
        except Exception as exc:  # noqa: BLE001 — error goes to the model as text
            _result(req_id, {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            })
    elif is_notification:
        pass  # ignore unknown notifications
    else:
        _error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _error(None, -32700, "Parse error")
            continue
        try:
            _handle(request)
        except Exception:  # noqa: BLE001 — never let one request kill the server
            traceback.print_exc(file=sys.stderr)
            if "id" in request:
                _error(request.get("id"), -32603, "Internal error")


if __name__ == "__main__":
    main()
