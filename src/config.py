from __future__ import annotations
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class Feed:
    court: str
    url: str


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_feeds(cfg: Dict[str, Any]) -> List[Feed]:
    return [Feed(court=x["court"], url=x["url"]) for x in cfg["feeds"]]
