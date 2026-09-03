from src.guardrails import apply_fda_guardrails, evaluate_clinical_decision
from src.retriever import retrieve_full_drug_context

def format_evidence_panel(context):
    return {
        "source_name": "LiverTox / FDA openFDA",
        "drug_reference": context.get("query_drug", "Unknown"),
        "active_ingredient": context.get("active_ingredient", "Unknown"),
        "source_url": context.get("source_url", "https://open.fda.gov/"),
        "quoted_excerpt": context.get("fda_hepatic_guidance", "No raw excerpt available."),
    }

def run_liverguard_pipeline(drug_name, patient_condition="moderate hepatic impairment"):
    context = retrieve_full_drug_context(drug_name)

    active_ing = context.get("active_ingredient")
    if not context or not active_ing or active_ing.lower() == "unknown":
        print("\n" + "=" * 55)
        print("      LIVERGUARD CLINICAL ASSESSMENT REPORT      ")
        print("=" * 55)
        print("Status: 🛑 SAFE REFUSAL (Insufficient Evidence)")
        print("Message: Unable to find verified guidelines for the requested query.")
        print("=" * 55 + "\n")
        return

    guardrails = apply_fda_guardrails(patient_condition, {"drug_name": drug_name, "active_ingredient": active_ing})
    decision = evaluate_clinical_decision(context, patient_condition)
    evidence = format_evidence_panel(context)

    print("\n" + "=" * 60)
    print("      LIVERGUARD CLINICAL ASSESSMENT & EVIDENCE PANEL      ")
    print("=" * 60)
    print(f"Target Query/Drug : {drug_name}")
    print(f"Active Ingredient : {active_ing}")
    print(f"LiverTox Category : {context.get('livertox_score')}")
    print(f"Safety Verdict    : {decision['status']}")
    print(f"Clinical Decision : {decision['verdict']}")
    print(f"Action Required   : {decision['action']}")
    print(f"Confidence Level  : {decision['confidence']}")
    print("-" * 60)
    print("                      EVIDENCE PANEL                       ")
    print("-" * 60)
    print(f"Source            : {evidence['source_name']}")
    print(f"Official Reference: {evidence['source_url']}")
    print(f"Supporting Excerpt: \"{evidence['quoted_excerpt']}\"")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_liverguard_pipeline("Panadol")