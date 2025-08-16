#!/usr/bin/env python3
import json
import sys
from typing import Any, List, Tuple

IGNORE_NO_OP = True  # skip ["no-op"] entries found in resource_changes

def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_disallowed_action(actions: List[str]) -> Tuple[bool, str]:
    """
    Allowed:
      - ["create"]
      - ["update"]
      - ["no-op"] (ignored if IGNORE_NO_OP=True)

    Disallowed:
      - anything containing "delete" (destroy)
      - replacements like ["delete","create"] or ["create","delete"]
      - any other unexpected sequence
    """
    norm = [a.lower() for a in actions]
    if "delete" in norm:
        return True, f"Plan contains destroy/replace action"
    if norm in (["create"], ["update"]):
        return False, ""
    if norm == ["no-op"]:
        # Treat as allowed (and skip later) if ignoring no-op; otherwise mark unsupported.
        return (False if IGNORE_NO_OP else True), ("" if IGNORE_NO_OP else "Plan contains unsupported action sequence: ['no-op']")
    return True, f"Plan contains unsupported action sequence: {actions}"

def diff_paths(before: Any, after: Any, base: List[str] = None) -> List[List[str]]:
    if base is None:
        base = []
    if type(before) != type(after):
        return [base]
    if isinstance(before, dict):
        paths = []
        keys = set(before.keys()) | set(after.keys())
        for k in keys:
            b = before.get(k, None)
            a = after.get(k, None)
            if type(b) != type(a):
                paths.append(base + [k])
            elif isinstance(a, dict):
                paths.extend(diff_paths(b, a, base + [k]))
            elif isinstance(a, list):
                if b != a:
                    paths.append(base + [k])
            else:
                if b != a:
                    paths.append(base + [k])
        return paths
    if isinstance(before, list):
        return [base] if before != after else []
    return [base] if before != after else []

def only_git_hash_tag_changed(change: dict) -> Tuple[bool, List[str]]:
    """Return (allowed, offending_paths)."""
    before = change.get("before") or {}
    after  = change.get("after") or {}
    changed = diff_paths(before, after, [])

    if not changed:
        return False, ["<no-diff>"]

    offending: List[str] = []
    for path in changed:
        # If entire tags changed, dive to ensure only tags.GitCommitHash changed.
        if len(path) == 1 and path[0] == "tags":
            btags = before.get("tags", {}) if isinstance(before.get("tags", {}), dict) else {}
            atags = after.get("tags", {}) if isinstance(after.get("tags", {}), dict) else {}
            inner_diffs = diff_paths(btags, atags, ["tags"])
            for ip in inner_diffs:
                if len(ip) != 2 or ip[0] != "tags" or ip[1] != "GitCommitHash":
                    offending.append(".".join(ip))
        elif not (len(path) == 2 and path[0] == "tags" and path[1] == "GitCommitHash"):
            offending.append(".".join(path))

    return (len(offending) == 0), offending

def validate_plan(plan: dict) -> Tuple[bool, List[str]]:
    """
    Validate every resource change in the plan.
    Returns (ok, messages). If not ok, messages contains ALL violations with actions.
    """
    violations: List[str] = []
    changes = plan.get("resource_changes", [])

    for rc in changes:
        addr = rc.get("address", "<unknown>")
        actions = rc.get("change", {}).get("actions", [])
        norm = [a.lower() for a in actions]

        if IGNORE_NO_OP and norm == ["no-op"]:
            continue

        dis, reason = is_disallowed_action(actions)
        if dis:
            violations.append(f"{addr}: {reason} (actions={actions})")
            continue

        if norm == ["update"]:
            allowed, offending_paths = only_git_hash_tag_changed(rc.get("change", {}))
            if not allowed:
                if offending_paths:
                    for p in offending_paths:
                        violations.append(f"{addr}: update modifies forbidden path: {p} (actions={actions})")
                else:
                    violations.append(f"{addr}: update violates policy (actions={actions})")

    return (len(violations) == 0), violations

def main():
    if len(sys.argv) != 2:
        print("Usage: script.py <tfplan.json>", file=sys.stderr)
        sys.exit(2)

    try:
        plan = load_plan(sys.argv[1])
    except Exception as e:
        print(f"Failed to read plan: {e}", file=sys.stderr)
        sys.exit(2)

    ok, msgs = validate_plan(plan)
    if ok:
        print("SAFE_TO_APPLY")
        sys.exit(0)
    else:
        print("BLOCKED:")
        for m in msgs:
            print(f"- {m}")
        sys.exit(1)

if __name__ == "__main__":
    main()
