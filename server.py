#!/usr/bin/env python3
"""
Oura MCP server — all Oura Ring API v2 endpoints exposed as Claude tools.

Runs as stdio MCP server. Designed to be launched by Claude Desktop / Claude Code.
Token is read from OURA_TOKEN env var or ~/.config/oura-mcp/token at startup.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from client import OuraClient

mcp = FastMCP("oura")
client = OuraClient()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_or_none(payload: dict) -> dict | None:
    """Oura returns {"data": [<one item>]} for single-day queries."""
    items = payload.get("data") or []
    return items[0] if items else None


def _resolve_date(date: str | None) -> str:
    return date or client.yesterday()


# ---------------------------------------------------------------------------
# Daily summaries
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Snapshot for one day: sleep score, readiness score, temperature deviation, "
        "and basic activity. Defaults to yesterday. Use this for the morning check-in."
    )
)
def oura_today(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {
        "date": d,
        "sleep": _first_or_none(client.request("daily_sleep", {"start_date": d, "end_date": d})),
        "readiness": _first_or_none(client.request("daily_readiness", {"start_date": d, "end_date": d})),
        "activity": _first_or_none(client.request("daily_activity", {"start_date": d, "end_date": d})),
    }


@mcp.tool(
    description=(
        "Detailed sleep session for a date: total/REM/deep/light durations, latency, "
        "efficiency, average HR, lowest HR, average HRV, breath rate. Defaults to yesterday."
    )
)
def oura_sleep(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "sessions": client.request("sleep", {"start_date": d, "end_date": d}).get("data", [])}


@mcp.tool(
    description=(
        "Readiness for a date: score, contributors (HRV balance, recovery index, "
        "sleep balance, body temperature), and temperature_deviation in Celsius. "
        "Useful for catching early illness or cycle effects. Defaults to yesterday."
    )
)
def oura_readiness(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "readiness": _first_or_none(client.request("daily_readiness", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "Daily activity summary: score, active calories, steps, total calories, "
        "contributors (meet_daily_targets, move_every_hour, recovery_time, stay_active, "
        "training_frequency, training_volume). Defaults to yesterday."
    )
)
def oura_activity(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "activity": _first_or_none(client.request("daily_activity", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "Daytime stress and recovery levels for a date. "
        "stress_high_seconds = total time at high stress, recovery_high_seconds = time at high recovery. "
        "Defaults to yesterday."
    )
)
def oura_stress(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "stress": _first_or_none(client.request("daily_stress", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "Long-term resilience score for a date — multi-week capacity to handle stress. "
        "Returns level (exceptional/strong/solid/adequate/limited) and contributors "
        "(sleep_recovery, daytime_recovery, stress). Defaults to yesterday."
    )
)
def oura_resilience(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "resilience": _first_or_none(client.request("daily_resilience", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "Average overnight blood oxygen (SpO2) percentage for a date. "
        "Useful for sleep apnea / hypoxia signals. Defaults to yesterday."
    )
)
def oura_spo2(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "spo2": _first_or_none(client.request("daily_spo2", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "Daily cardiovascular age — Oura's predicted vascular age (18–100). "
        "Compare with biological age to gauge heart health. Defaults to yesterday."
    )
)
def oura_cardiovascular_age(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "cardiovascular_age": _first_or_none(client.request("daily_cardiovascular_age", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "VO2 max estimate for a date. Higher is better — elite athletes are 60+, "
        "average adults 30–40. Defaults to yesterday."
    )
)
def oura_vo2_max(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "vo2_max": _first_or_none(client.request("vo2_max", {"start_date": d, "end_date": d}))}


# ---------------------------------------------------------------------------
# Detailed / session data
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Auto-detected workouts for a date range. "
        "Includes type (running, cycling, gym…), HR average/max, calories, distance, intensity. "
        "Defaults to yesterday."
    )
)
def oura_workouts(start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    s = start_date or _resolve_date(None)
    e = end_date or s
    return {"range": [s, e], "workouts": client.request("workout", {"start_date": s, "end_date": e}).get("data", [])}


@mcp.tool(
    description=(
        "Guided sessions (meditation, breathing, nap, relaxation, rest, body_status) "
        "for a date range. Includes HR, HRV, mood, motion count. Defaults to yesterday."
    )
)
def oura_sessions(start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    s = start_date or _resolve_date(None)
    e = end_date or s
    return {"range": [s, e], "sessions": client.request("session", {"start_date": s, "end_date": e}).get("data", [])}


@mcp.tool(
    description=(
        "5-minute heart rate samples for a datetime window. "
        "Each sample has bpm and source (awake/rest/sleep/session/workout). "
        "NOTE: uses start_datetime/end_datetime (ISO 8601), not dates. "
        "Defaults to the last 24 hours."
    )
)
def oura_heart_rate(start_datetime: str | None = None, end_datetime: str | None = None) -> dict[str, Any]:
    if not end_datetime:
        end_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if not start_datetime:
        start_datetime = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "range": [start_datetime, end_datetime],
        "samples": client.request("heartrate", {"start_datetime": start_datetime, "end_datetime": end_datetime}).get("data", []),
    }


@mcp.tool(
    description=(
        "Enhanced tags for a date range — user-created tags with optional comments "
        "and duration. Replaces the deprecated tag endpoint. Defaults to last 7 days."
    )
)
def oura_tags(start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    s = start_date or client.days_ago(6)
    e = end_date or client.days_ago(0)
    return {"range": [s, e], "tags": client.request("enhanced_tag", {"start_date": s, "end_date": e}).get("data", [])}


@mcp.tool(
    description=(
        "Sleep time recommendation for a date: optimal bedtime window and status "
        "(optimal_found, not_enough_nights, etc.). Defaults to yesterday."
    )
)
def oura_sleep_time(date: str | None = None) -> dict[str, Any]:
    d = _resolve_date(date)
    return {"date": d, "sleep_time": _first_or_none(client.request("sleep_time", {"start_date": d, "end_date": d}))}


@mcp.tool(
    description=(
        "Rest mode periods for a date range — when the user activated rest mode "
        "(e.g. sick days, recovery). Includes episodes with tags. Defaults to last 7 days."
    )
)
def oura_rest_mode(start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    s = start_date or client.days_ago(6)
    e = end_date or client.days_ago(0)
    return {"range": [s, e], "periods": client.request("rest_mode_period", {"start_date": s, "end_date": e}).get("data", [])}


# ---------------------------------------------------------------------------
# Trends (multi-day)
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Sleep score and readiness score for the last N days (default 7). "
        "Returns a list ordered oldest → newest. Useful for weekly review."
    )
)
def oura_trends(days: int = 7) -> dict[str, Any]:
    if days < 1 or days > 60:
        raise ValueError("days must be between 1 and 60")
    start, end = client.days_ago(days - 1), client.days_ago(0)
    sleep = client.request("daily_sleep", {"start_date": start, "end_date": end}).get("data", [])
    readiness = client.request("daily_readiness", {"start_date": start, "end_date": end}).get("data", [])
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


@mcp.tool(
    description=(
        "Temperature deviation for the last N days (default 14). "
        "Useful for tracking cycle phase, illness onset, or post-training recovery. "
        "Returned in Celsius, ordered oldest → newest."
    )
)
def oura_temp_trend(days: int = 14) -> dict[str, Any]:
    if days < 1 or days > 60:
        raise ValueError("days must be between 1 and 60")
    start, end = client.days_ago(days - 1), client.days_ago(0)
    rows = client.request("daily_readiness", {"start_date": start, "end_date": end}).get("data", [])
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


# ---------------------------------------------------------------------------
# Account / device info
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Personal info: age, weight, height, biological sex, email. "
        "No date parameter — returns current profile."
    )
)
def oura_personal_info() -> dict[str, Any]:
    return client.request("personal_info")


@mcp.tool(
    description=(
        "Ring configuration: model (gen2/gen3/gen4), color, size, firmware version. "
        "Defaults to all known configurations."
    )
)
def oura_ring_configuration() -> dict[str, Any]:
    return {"rings": client.request("ring_configuration").get("data", [])}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
