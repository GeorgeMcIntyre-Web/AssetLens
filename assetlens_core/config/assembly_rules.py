from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AssemblyRule:
    category: str
    exact: list[str]
    regex: list[re.Pattern[str]]


@dataclass(frozen=True)
class AssemblyRules:
    rules: list[AssemblyRule]
    fallback_category: str = "unknown"
    subassembly_categories: list[str] = ()


def default_assembly_rules() -> AssemblyRules:
    rules: list[AssemblyRule] = [
        AssemblyRule(category="clamp", exact=["clamp"], regex=[re.compile(r"clamp")]),
        AssemblyRule(category="finger", exact=["finger"], regex=[re.compile(r"finger")]),
        AssemblyRule(category="cylinder", exact=["cylinder"], regex=[re.compile(r"cyl")]),
        AssemblyRule(category="frame", exact=["frame"], regex=[re.compile(r"frame")]),
        AssemblyRule(category="bracket", exact=["bracket"], regex=[re.compile(r"bracket")]),
        AssemblyRule(category="sensor", exact=["sensor"], regex=[re.compile(r"sensor")]),
        AssemblyRule(category="pin", exact=["pin"], regex=[re.compile(r"pin")]),
        AssemblyRule(category="bolt", exact=["bolt", "screw"], regex=[re.compile(r"bolt|screw")]),
    ]
    return AssemblyRules(rules=rules, fallback_category="unknown", subassembly_categories=["assembly"])


def normalize_part_name(name: str) -> str:
    if name is None:
        raise ValueError("name must not be None.")

    norm = name.strip().lower()
    suffixes = ["_left", "_right", "-left", "-right", "_l", "_r"]
    for s in suffixes:
        if norm.endswith(s):
            norm = norm[: -len(s)]
            norm = norm.rstrip("_- ")

    norm = re.sub(r"(?:[._-]\d+)$", "", norm)
    norm = norm.strip()
    return norm


def classify_part(name: str, rules: AssemblyRules) -> str:
    if name is None:
        raise ValueError("name must not be None.")
    if rules is None:
        raise ValueError("rules must not be None.")

    norm = normalize_part_name(name)

    for rule in rules.rules:
        for ex in rule.exact:
            if ex == norm:
                return rule.category
            if ex in norm:
                return rule.category
        for pat in rule.regex:
            if pat.search(norm):
                return rule.category

    return rules.fallback_category

