#!/usr/bin/env python3
"""Compute Gophish dashboard and event-derived stats from a saved results JSON."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


MODE_SNAPSHOT = "snapshot"
MODE_RANGE = "range"


@dataclass
class Stats:
    total: int = 0
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    submitted_data: int = 0
    email_reported: int = 0
    error: int = 0

    def as_dict(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "sent": self.sent,
            "opened": self.opened,
            "clicked": self.clicked,
            "submitted_data": self.submitted_data,
            "email_reported": self.email_reported,
            "error": self.error,
        }


@dataclass
class EventState:
    sent: Optional[datetime] = None
    opened: Optional[datetime] = None
    clicked: Optional[datetime] = None
    submitted: Optional[datetime] = None
    reported: Optional[datetime] = None
    error: Optional[datetime] = None


def parse_datetime(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def set_if_earlier(current: Optional[datetime], candidate: Optional[datetime]) -> Optional[datetime]:
    if candidate is None:
        return current
    if current is None or candidate < current:
        return candidate
    return current


def load_payload(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text())
    if "results" not in payload or "timeline" not in payload:
        raise ValueError("input must contain 'results' and 'timeline'")
    return payload


def dashboard_stats(results: list[dict]) -> Stats:
    stats = Stats(total=len(results))
    for result in results:
        status = result.get("status")
        if status == "Submitted Data":
            stats.submitted_data += 1
            stats.clicked += 1
            stats.opened += 1
            stats.sent += 1
        elif status == "Clicked Link":
            stats.clicked += 1
            stats.opened += 1
            stats.sent += 1
        elif status == "Email Opened":
            stats.opened += 1
            stats.sent += 1
        elif status == "Email Sent":
            stats.sent += 1
        elif status == "Error":
            stats.error += 1
        if result.get("reported"):
            stats.email_reported += 1
    return stats


def event_states(results: list[dict], timeline: list[dict]) -> Dict[str, EventState]:
    states: Dict[str, EventState] = {result["email"]: EventState() for result in results if result.get("email")}
    for event in timeline:
        email = event.get("email")
        if not email or email not in states:
            continue
        when = parse_datetime(event.get("time"))
        if when is None:
            continue
        state = states[email]
        message = event.get("message")
        if message == "Email Sent":
            state.sent = set_if_earlier(state.sent, when)
        elif message == "Email Opened":
            state.opened = set_if_earlier(state.opened, when)
        elif message == "Clicked Link":
            state.opened = set_if_earlier(state.opened, when)
            state.clicked = set_if_earlier(state.clicked, when)
        elif message == "Submitted Data":
            state.opened = set_if_earlier(state.opened, when)
            state.clicked = set_if_earlier(state.clicked, when)
            state.submitted = set_if_earlier(state.submitted, when)
        elif message == "Email Reported":
            state.reported = set_if_earlier(state.reported, when)
        elif message == "Error Sending Email":
            state.error = set_if_earlier(state.error, when)
    return states


def in_window(stage_time: Optional[datetime], start: Optional[datetime], end: Optional[datetime], mode: str) -> bool:
    if stage_time is None or end is None:
        return False
    if mode == MODE_RANGE:
        if start is None:
            return False
        return start <= stage_time <= end
    return stage_time <= end


def actual_stats(results: list[dict], timeline: list[dict], start: Optional[datetime], end: Optional[datetime], mode: str) -> Stats:
    stats = Stats(total=len(results))
    states = event_states(results, timeline)
    for state in states.values():
        if in_window(state.sent, start, end, mode):
            stats.sent += 1
        if in_window(state.opened, start, end, mode):
            stats.opened += 1
        if in_window(state.clicked, start, end, mode):
            stats.clicked += 1
        if in_window(state.submitted, start, end, mode):
            stats.submitted_data += 1
        if in_window(state.reported, start, end, mode):
            stats.email_reported += 1
        if in_window(state.error, start, end, mode):
            stats.error += 1
    return stats


def render_table(stats_map: Dict[str, Stats]) -> str:
    headers = ["view", "total", "sent", "opened", "clicked", "submitted", "reported", "error"]
    rows = [headers]
    for label, stats in stats_map.items():
        rows.append([
            label,
            str(stats.total),
            str(stats.sent),
            str(stats.opened),
            str(stats.clicked),
            str(stats.submitted_data),
            str(stats.email_reported),
            str(stats.error),
        ])
    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    return "\n".join("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="saved /api/campaigns/:id/results JSON")
    parser.add_argument("--mode", choices=[MODE_SNAPSHOT, MODE_RANGE], default=MODE_SNAPSHOT)
    parser.add_argument("--start", help="RFC3339 start timestamp for range mode")
    parser.add_argument("--end", help="RFC3339 end timestamp")
    parser.add_argument("--view", choices=["actual", "dashboard", "compare"], default="compare")
    parser.add_argument("--output", choices=["table", "json"], default="table")
    args = parser.parse_args()

    start = parse_datetime(args.start)
    end = parse_datetime(args.end)
    if args.mode == MODE_RANGE and start is None:
        parser.error("--start is required for range mode")
    if args.mode == MODE_RANGE and end is None:
        parser.error("--end is required for range mode")
    if args.mode == MODE_SNAPSHOT and end is None:
        end = datetime.now(timezone.utc)
    if start and end and start > end:
        parser.error("--start must be before --end")

    payload = load_payload(args.input)
    results = payload["results"]
    timeline = payload["timeline"]

    output: Dict[str, Stats] = {}
    if args.view in {"dashboard", "compare"}:
        output["dashboard"] = dashboard_stats(results)
    if args.view in {"actual", "compare"}:
        output["actual"] = actual_stats(results, timeline, start, end, args.mode)

    if args.output == "json":
        print(json.dumps({key: value.as_dict() for key, value in output.items()}, indent=2))
        return
    print(render_table(output))


if __name__ == "__main__":
    main()
