"""Project memory — persistent design state (cahier des charges §7.1).

Goal: never re-describe the project across sessions. The AI reads a compact
state at session start and updates it after each *validated* step. Stored as a
single JSON file under /project_state so it is versionable and diff-friendly.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import project_dir

STATE_VERSION = 1


def _state_path() -> Path:
    d = project_dir() / "project_state"
    d.mkdir(parents=True, exist_ok=True)
    return d / "state.json"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _empty(project: str = "untitled") -> Dict[str, Any]:
    return {
        "state_version": STATE_VERSION,
        "project": project,
        "updated": _now(),
        "intent": "",
        "constraints": [],
        "parameters": {},
        "features": [],   # [{name, type, params, at}]
        "decisions": [],  # [{text, at}]
        "checkpoints": [],  # [{name, file, at, note}] — maintained by checkpoint.py
    }


def load() -> Dict[str, Any]:
    """Load state, or a fresh empty state if none exists yet."""
    p = _state_path()
    if not p.exists():
        return _empty()
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save(state: Dict[str, Any]) -> None:
    """Atomic write: a crash mid-write must never corrupt the project memory
    (NF2 — the memory IS the recovery mechanism). Write to a temp file in the
    same directory, then replace."""
    state["updated"] = _now()
    p = _state_path()
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    import os
    os.replace(tmp, p)


# -- convenience mutators (load -> change -> save) --------------------------

def init_project(name: str, intent: str = "") -> Dict[str, Any]:
    s = _empty(name)
    s["intent"] = intent
    save(s)
    return s


def set_intent(intent: str) -> None:
    s = load()
    s["intent"] = intent
    save(s)


def add_constraint(text: str) -> None:
    s = load()
    if text not in s["constraints"]:
        s["constraints"].append(text)
    save(s)


def set_parameter(key: str, value: Any) -> None:
    s = load()
    s["parameters"][key] = value
    save(s)


def record_feature(name: str, ftype: str, params: Optional[Dict[str, Any]] = None) -> None:
    """Record a validated feature. Replaces any prior entry with the same name."""
    s = load()
    s["features"] = [f for f in s["features"] if f.get("name") != name]
    s["features"].append({"name": name, "type": ftype, "params": params or {}, "at": _now()})
    save(s)


def add_decision(text: str) -> None:
    s = load()
    s["decisions"].append({"text": text, "at": _now()})
    save(s)


# -- token-efficient read ---------------------------------------------------

def summary() -> str:
    """Compact text digest for reading at session start (token-minimal)."""
    s = load()
    lines: List[str] = [f"Project: {s['project']} (updated {s['updated']})"]
    if s.get("intent"):
        lines.append(f"Intent: {s['intent']}")
    if s.get("constraints"):
        lines.append("Constraints: " + "; ".join(s["constraints"]))
    if s.get("parameters"):
        lines.append("Params: " + ", ".join(f"{k}={v}" for k, v in s["parameters"].items()))
    if s.get("features"):
        feats = ", ".join(f"{f['name']}({f['type']})" for f in s["features"])
        lines.append(f"Features ({len(s['features'])}): {feats}")
    if s.get("checkpoints"):
        lines.append("Checkpoints: " + ", ".join(c["name"] for c in s["checkpoints"]))
    if s.get("decisions"):
        lines.append(f"Decisions logged: {len(s['decisions'])} (latest: {s['decisions'][-1]['text']})")
    return "\n".join(lines)
