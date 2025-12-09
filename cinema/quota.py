from __future__ import annotations

"""Pricing tier and quota configuration.

This module loads a simple JSON config that defines concurrency limits per
pricing tier. It is intentionally static and file-based so deployments can
change tiers without code changes, while runtime accounting/enforcement uses
the jobs database.

Default config file (relative to this package):
- pricing_tiers.json

Structure:
{
  "default_tier": "superman",
  "tiers": {
    "free": {"max_concurrent_chapters": 1},
    "superman": {"max_concurrent_chapters": 3}
  }
}
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def _default_config_path() -> Path:
    """Return the default pricing tier config path.

    The path is resolved relative to this module so that the config can be
    shipped with the package. Deployments can override via the
    CINEMA_TIER_CONFIG_PATH environment variable if needed.
    """

    return Path(__file__).resolve().parent / "pricing_tiers.json"


def load_pricing_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the pricing tier configuration.

    If `config_path` is not provided, the loader will first look at the
    CINEMA_TIER_CONFIG_PATH environment variable, then fall back to the
    default JSON file living next to this module.
    """

    if config_path is None:
        env_path = os.getenv("CINEMA_TIER_CONFIG_PATH")
        if env_path:
            config_path = env_path
        else:
            config_path = str(_default_config_path())

    path = Path(config_path)
    if not path.exists():
        # Hard-coded safe fallback to avoid crashes if the file is missing.
        return {
            "default_tier": "superman",
            "tiers": {
                "free": {"max_concurrent_chapters": 1},
                "superman": {"max_concurrent_chapters": 3},
            },
        }

    with path.open("r") as f:
        data = json.load(f)

    # Basic validation with sane fallbacks
    tiers = data.get("tiers") or {}
    if not isinstance(tiers, dict):
        tiers = {}

    default_tier = data.get("default_tier") or "superman"
    if default_tier not in tiers:
        # Ensure default exists
        tiers.setdefault("superman", {"max_concurrent_chapters": 3})
        default_tier = "superman"

    return {"default_tier": default_tier, "tiers": tiers}


def get_max_concurrent_chapters(tier: Optional[str] = None) -> int:
    """Return the max concurrent chapter jobs for the given pricing tier.

    If `tier` is None, the active tier is resolved as:
    - CINEMA_PRICING_TIER env var if set, else
    - `default_tier` from the pricing config.
    """

    cfg = load_pricing_config()
    tiers: Dict[str, Dict[str, Any]] = cfg["tiers"]  # type: ignore[assignment]

    if tier is None:
        tier = os.getenv("CINEMA_PRICING_TIER") or cfg["default_tier"]

    tier_cfg = tiers.get(tier) or {}
    try:
        value = int(tier_cfg.get("max_concurrent_chapters", 3))
    except Exception:
        value = 3

    if value < 1:
        value = 1

    return value
