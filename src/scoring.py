from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import re


def _contains_any(text: str, terms: List[str]) -> List[str]:
    hits = []
    low = text.lower()
    for t in terms:
        if t.lower() in low:
            hits.append(t)
    return hits


def detect_doc_types(text: str, cfg: Dict[str, Any]) -> List[str]:
    ot = cfg["opinion_type"]
    low = text.lower()

    types = []
    if any(k in low for k in ot.get("dissent_indicators", [])):
        types.append("Dissent")
    if any(k in low for k in ot.get("concurrence_indicators", [])):
        types.append("Concurrence")
    if any(k in low for k in ot.get("per_curiam_indicators", ["per curiam"])):
        types.append("Per Curiam")
    if any(k in low for k in ot.get("memorandum_indicators", [])):
        types.append("Memorandum")
    if any(k in low for k in ot.get("non_opinion_indicators", [])):
        types.append("Order/Non-opinion")
    if any(k in low for k in ot.get("opinion_indicators", [])):
        types.append("Opinion")

    # clean up: if Opinion present, drop Order/Non-opinion unless also clearly order
    if "Opinion" in types and "Order/Non-opinion" in types:
        types = [t for t in types if t != "Order/Non-opinion"]

    # de-dupe preserve order
    out = []
    seen = set()
    for t in types:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out or ["Unknown"]


def score_item(court: str, text: str, cfg: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    reasons: Dict[str, Any] = {"flags": [], "place_hits": [], "special_hits": []}
    score = 0

    places = cfg["places"]
    counties = places.get("counties", [])
    cities = places.get("cities", [])
    place_hits = _contains_any(text, counties + cities)
    if place_hits:
        score += cfg["scoring"]["place_match_points"]
        reasons["flags"].append("PLACE")
        reasons["place_hits"] = place_hits

    # special terms
    for sp in places.get("special", []):
        term = sp["term"]
        if term.lower() in text.lower():
            pts = int(sp["points"])
            score += pts
            reasons["flags"].append(f"SPECIAL:{term}")
            reasons["special_hits"].append(term)

    # precedential
    prec_cfg = cfg["precedential"]
    low = text.lower()
    is_precedential = False
    if prec_cfg.get("supreme_always_precedential", False) and court == "Pennsylvania Supreme Court":
        is_precedential = True
    else:
        if any(ind.lower() in low for ind in prec_cfg.get("indicators", [])):
            is_precedential = True

    if is_precedential:
        score += cfg["scoring"]["precedential_points"]
        reasons["flags"].append("PRECEDENTIAL")

    # opinion vs other
    doc_types = detect_doc_types(text, cfg)
    reasons["doc_types"] = doc_types
    if "Opinion" in doc_types:
        score += cfg["scoring"]["opinion_points"]
        reasons["flags"].append("OPINION")

    # reversal/remand
    rev_hits = _contains_any(text, cfg.get("reversal_indicators", []))
    if rev_hits:
        score += cfg["scoring"]["reversal_points"]
        reasons["flags"].append("REVERSAL/REMAND")
        reasons["reversal_hits"] = rev_hits

    return score, reasons
