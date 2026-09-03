import json
import os
from functools import lru_cache
from typing import Any

from src.fda_api import get_fda_drug_label
from src.rxnav_api import get_active_ingredient


@lru_cache(maxsize=1)
def _load_livertox_db() -> list[dict[str, Any]]:
    """Load and cache the LiverTox database in memory."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, "data", "livertox_data.json")

    if not os.path.exists(file_path):
        return [{"_error": "LiverTox local database file not found."}]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        return [{"_error": f"Invalid JSON in LiverTox database: {e}"}]
    except Exception as e:
        return [{"_error": str(e)}]


def _normalize(value) -> str:
    """Safely normalize any value to lowercase string."""
    if value is None:
        return ""
    return str(value).strip().lower()


def get_livertox_info(drug_name: str, active_ingredient: str) -> dict[str, Any]:
    """Fetch liver toxicity info from data/livertox_data.json by trade name or active ingredient."""
    livertox_db = _load_livertox_db()

    # Check if database loading failed
    if livertox_db and "_error" in livertox_db[0]:
        return {
            "hepatotoxicity_score": "Unknown",
            "summary": f"Database error: {livertox_db[0]['_error']}",
            "source_url": None,
        }

    query_name = _normalize(drug_name)
    query_ingredient = _normalize(active_ingredient)

    # Priority 1: exact normalized trade-name match
    for entry in livertox_db:
        if _normalize(entry.get("drug_name")) == query_name:
            return entry

    # Priority 2: exact normalized active-ingredient match
    for entry in livertox_db:
        if _normalize(entry.get("active_ingredient")) == query_ingredient:
            return entry

    return {
        "hepatotoxicity_score": "Unknown",
        "summary": "No specific LiverTox record found.",
        "source_url": None,
    }


def retrieve_full_drug_context(drug_name: str) -> dict[str, Any]:
    """Aggregate all retrieved data into a single structured context object."""
    # ✅ FIX #2: Ensure active_ingredient is always a string
    active_ingredient = get_active_ingredient(drug_name) or "Unknown"
    
    fda_data = get_fda_drug_label(active_ingredient)
    livertox_data = get_livertox_info(drug_name, active_ingredient)

    context = {
        "query_drug": drug_name,
        "active_ingredient": active_ingredient,
        "fda_warnings": fda_data.get("warnings"),
        "fda_hepatic_guidance": fda_data.get("hepatic_warnings"),
        "livertox_score": livertox_data.get("hepatotoxicity_score"),
        "livertox_summary": livertox_data.get("summary"),
        "source_url": livertox_data.get("source_url") or "https://open.fda.gov/",
        # ✅ FIX #1: Pass through any errors for transparency
        "errors": [],
    }

    # Collect any errors from subsystems
    if "error" in fda_data:
        context["errors"].append(f"FDA API: {fda_data['error']}")
    if "error" in livertox_data:
        context["errors"].append(f"LiverTox: {livertox_data['error']}")

    return context


if __name__ == "__main__":
    context_data = retrieve_full_drug_context("Panadol")
    print("\n--- Final Aggregated Context ---")
    print(json.dumps(context_data, indent=2, ensure_ascii=False))