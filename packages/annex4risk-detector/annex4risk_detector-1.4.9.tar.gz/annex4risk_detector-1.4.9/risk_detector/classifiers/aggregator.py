"""Aggregate matched rules to a final category."""
from . import __init__  # noqa: F401

PRIORITY = ["prohibited", "out_of_scope", "high_risk", "not_high_risk"]

def classify(rules, answers):
    matched = []
    for rule in rules:
        if rule.get("matched"):
            r = dict(rule)
            # normalize legacy value
            if r.get("category") == "limited_risk":
                r["category"] = "not_high_risk"
            # normalize deprecated minimal_risk to not_high_risk for legal alignment
            if r.get("category") == "minimal_risk":
                r["category"] = "not_high_risk"
            matched.append(r)
    category = "not_high_risk"
    for cat in PRIORITY:
        if any(r["category"] == cat for r in matched):
            category = cat
            break
    score = sum(r.get("weight", 1.0) for r in matched if r["category"] == category)
    legal_refs = sorted({ref for r in matched for ref in r.get("legal_refs", [])})
    # Исключение по ст. 6(3): либо явно присутствует ссылка, либо итоговая категория снижена
    has_a63_ref = any(isinstance(ref, str) and "Article 6(3)" in ref for ref in legal_refs)
    exception = has_a63_ref or category == "not_high_risk"
    return {
        "category": category,
        "score": score,
        "legal_refs": legal_refs,
        "exception_applied": exception,
        "matched_rules": [r["id"] for r in matched],
    }
