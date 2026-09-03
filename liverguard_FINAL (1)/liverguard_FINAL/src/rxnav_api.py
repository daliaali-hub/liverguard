import urllib.parse
import requests

# Local mapping for instant resolution during hackathon demo
LOCAL_DRUG_MAP = {
    "panadol": "Acetaminophen",
    "tylenol": "Acetaminophen",
    "brufen": "Ibuprofen",
    "advil": "Ibuprofen",
    "voltaren": "Diclofenac",
    "augmentin": "Amoxicillin-Clavulanate",
    "flagyl": "Metronidazole",
}


def get_active_ingredient(drug_name: str) -> str | None:
    """
    Normalize brand drug name to active ingredient using local dictionary 
    fallback & RxNav API.
    
    Returns None if resolution fails (so caller knows it's unresolved).
    """
    if not drug_name or not isinstance(drug_name, str):
        return None
    
    cleaned_name = drug_name.strip().lower()

    # Check local dictionary first for instant performance
    if cleaned_name in LOCAL_DRUG_MAP:
        return LOCAL_DRUG_MAP[cleaned_name]

    # ✅ FIX #2: URL-encode the drug name
    encoded_name = urllib.parse.quote(drug_name.strip())
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={encoded_name}"

    try:
        # ✅ FIX #1: verify=True (default, secure)
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        id_group = data.get("idGroup", {})
        rxnorm_ids = id_group.get("rxnormId", [])

        if not rxnorm_ids:
            # ✅ FIX #3: Return None to signal unresolved, not the brand name
            return None

        rxnorm_id = rxnorm_ids[0]
        prop_url = (
            f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxnorm_id}/properties.json"
        )
        prop_response = requests.get(prop_url, timeout=5)
        prop_response.raise_for_status()

        prop_data = prop_response.json()
        ingredient = prop_data.get("properties", {}).get("name")
        
        return ingredient if ingredient else None

    except requests.exceptions.RequestException:
        # Network/API failure -> return None so caller can handle gracefully
        return None
    except Exception:
        return None


if __name__ == "__main__":
    test_drugs = ["Panadol", "Augmentin", "UnknownDrug123", ""]
    for test_drug in test_drugs:
        ingredient = get_active_ingredient(test_drug)
        status = "✅" if ingredient else "❌"
        print(f"{status} Brand: '{test_drug}' -> Active Ingredient: {ingredient}")