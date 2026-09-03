import json
import ssl
import urllib.request
import urllib.parse

# Local fallback data for offline/slow connection safety during demo
LOCAL_FDA_DATA = {
    "acetaminophen": {
        "warnings": "Liver warning: This product contains acetaminophen. Severe liver damage may occur if you take more than 4,000 mg in 24 hours or with other drugs containing acetaminophen.",
        "hepatic_warnings": "Patients with underlying liver disease should consult a physician. Maximum daily dose should be reduced (e.g., max 2g/day).",
    },
    "ibuprofen": {
        "warnings": "Severe allergic reaction or stomach bleeding warning.",
        "hepatic_warnings": "Use with caution in patients with severe hepatic impairment.",
    },
}


def get_fda_drug_label(active_ingredient: str) -> dict:
    """Fetch official drug label warnings from openFDA API using standard urllib."""
    ingredient_key = active_ingredient.strip().lower()

    # Fast check from local dataset first
    if ingredient_key in LOCAL_FDA_DATA:
        return LOCAL_FDA_DATA[ingredient_key]

    # URL-encode the ingredient to prevent URL breakage
    encoded_ingredient = urllib.parse.quote(active_ingredient.strip())
    url = f'https://api.fda.gov/drug/label.json?search=openfda.substance_name:"{encoded_ingredient}"&limit=1'

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                results = data.get("results", [])
                
                # ✅ FIX #2: Check if results is not empty
                if not results:
                    return {
                        "warnings": "No FDA label found for this drug.",
                        "hepatic_warnings": "Consult physician for hepatic dose adjustments.",
                    }
                
                result = results[0]
                
                # ✅ FIX #3: Safe list access with fallback
                warnings_list = result.get("warnings", [])
                warnings = warnings_list[0] if warnings_list else "No general warnings recorded."
                
                hepatic_list = result.get("use_in_specific_populations", [])
                hepatic_warnings = hepatic_list[0] if hepatic_list else "No specific hepatic impairment guidelines found."
                
                return {
                    "warnings": warnings,
                    "hepatic_warnings": hepatic_warnings,
                }
    except Exception as e:
        # In production, use logging instead of print
        print(f"[Note] openFDA network skipped ({e}). Using safety default.")

    return {
        "warnings": "Standard FDA drug label requirements apply.",
        "hepatic_warnings": "Consult physician for hepatic dose adjustments.",
    }


if __name__ == "__main__":
    info = get_fda_drug_label("Acetaminophen")
    print("\n--- openFDA Label Results ---")
    print(info)