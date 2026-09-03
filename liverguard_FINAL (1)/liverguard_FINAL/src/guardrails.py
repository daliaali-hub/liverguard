from typing import Literal, Optional, Dict, Any

HEPATOTOXIC_DRUGS = {
    "acetaminophen": {"risk": "caution", "max_dose_liver": "2g/day", "note": "Reduce max dose in liver disease"},
    "methotrexate": {"risk": "contraindicated", "note": "Contraindicated in severe hepatic impairment"},
    "isoniazid": {"risk": "caution", "note": "Hepatotoxic - monitor LFTs closely"},
    "amoxicillin-clavulanate": {"risk": "caution", "note": "Risk of drug-induced liver injury"},
    "statins": {"risk": "caution", "note": "Use lowest effective dose in liver disease"},
    "ketoconazole": {"risk": "contraindicated", "note": "Severe hepatotoxicity risk"},
}

RiskLevel = Literal["safe", "caution", "contraindicated", "unknown"]


def evaluate_clinical_decision(context: Dict[str, Any], patient_status: str = "moderate hepatic impairment") -> Dict[str, Any]:
    """Single Source of Truth for safety verdict across CLI and Streamlit."""
    active_ingredient = (context.get("active_ingredient") or "").lower()
    score = str(context.get("livertox_score") or "").upper()
    warnings = (context.get("fda_warnings") or "").lower()

    # Rule 1: Safe Refusal if missing ingredient
    if not active_ingredient or active_ingredient == "unknown":
        return {
            "status": "NOT FOUND",
            "risk_level": "unknown",
            "verdict": "No specific local record was found for this query.",
            "action": "Verify drug name or consult a physician.",
            "confidence": "LOW",
            "ui_type": "warning"
        }

    # Rule 2: Explicit Acetaminophen rule
    if "acetaminophen" in active_ingredient:
        return {
            "status": "CAUTION",
            "risk_level": "caution",
            "verdict": "Safe ONLY with strict dose reduction (Max 2g/day).",
            "action": "Avoid concurrent acetaminophen-containing products.",
            "confidence": "HIGH",
            "ui_type": "warning"
        }

    # Rule 3: High Risk / Contraindicated (Category A/B per LiverTox severe scale or FDA severe warning)
    if "CATEGORY A" in score or "CATEGORY B" in score or "severe liver damage" in warnings:
        return {
            "status": "HIGH RISK",
            "risk_level": "contraindicated",
            "verdict": "Hepatotoxicity risk (Category A/B) - Unsafe for hepatic patients.",
            "action": "Discontinue use or seek immediate safer alternatives.",
            "confidence": "HIGH",
            "ui_type": "error"
        }

    # Rule 4: Moderate Risk / Caution
    if "CATEGORY C" in score or "CATEGORY D" in score:
        return {
            "status": "CAUTION",
            "risk_level": "caution",
            "verdict": "Hepatotoxicity risk (Category C/D). Periodic LFT monitoring required.",
            "action": "Adjust dosage based on baseline impairment.",
            "confidence": "MEDIUM",
            "ui_type": "warning"
        }

    # Rule 5: Fail-Safe Default (Avoid defaulting to Safe)
    return {
        "status": "CAUTION",
        "risk_level": "caution",
        "verdict": "Limited hepatotoxicity data available. Exercise clinical caution.",
        "action": "Consult physician for explicit clearance.",
        "confidence": "LOW",
        "ui_type": "warning"
    }


def apply_fda_guardrails(patient_status: str, drug_info: dict) -> dict:
    """Apply FDA hepatic guidance safety logic programmatically."""
    drug_name = drug_info.get("drug_name", "").strip().lower()
    active_ingredient = drug_info.get("active_ingredient", drug_name).strip().lower()
    
    risk_level: RiskLevel = "caution"
    specific_warnings: list[str] = []
    dose_adjustment: Optional[str] = None
    
    drug_risk = HEPATOTOXIC_DRUGS.get(active_ingredient)
    if drug_risk:
        risk_level = drug_risk["risk"]  # type: ignore
        specific_warnings.append(drug_risk["note"])
        if "max_dose_liver" in drug_risk:
            dose_adjustment = drug_risk["max_dose_liver"]
    
    patient_lower = patient_status.lower()
    if "cirrhosis" in patient_lower or "severe" in patient_lower:
        if risk_level == "caution":
            risk_level = "contraindicated"
            specific_warnings.append("Severe liver disease elevates risk to contraindicated.")

    system_instructions = f"""
    You are a clinical assistant evaluating drug safety for liver disease patients.
    PATIENT CONTEXT: {patient_status}
    DRUG: {drug_info.get('drug_name', 'Unknown')}
    ACTIVE INGREDIENT: {active_ingredient}
    
    ENFORCED SAFETY ASSESSMENT:
    - Risk Level: {risk_level.upper()}
    - Dose Adjustment: {dose_adjustment or "None required"}
    
    STRICT GUARDRAILS:
    1. You MUST classify the drug as: Safe, Caution, or Contraindicated.
    2. Cite FDA labels and clinical sources in your response.
    3. Include a clinical disclaimer.
    """
    
    return {
        "system_instructions": system_instructions,
        "risk_level": risk_level,
        "dose_adjustment": dose_adjustment,
        "specific_warnings": specific_warnings,
        "requires_physician_approval": risk_level in ("caution", "contraindicated"),
    }