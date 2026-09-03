import streamlit as st
from src.retriever import retrieve_full_drug_context
from src.guardrails import apply_fda_guardrails, evaluate_clinical_decision
from src.llm_generator import generate_grounded_answer

st.set_page_config(page_title="LiverGuard", page_icon="🛡️", layout="wide")

st.title("🛡️ LiverGuard")
st.caption("Clinical Drug Safety Assessment for Hepatic Patients")
st.divider()

col_input1, col_input2 = st.columns([2, 1])
with col_input1:
    drug_input = st.text_input("Enter drug name or active ingredient", "").strip()
with col_input2:
    patient_condition = st.selectbox(
        "Patient Condition Severity",
        ["Mild hepatic impairment", "Moderate hepatic impairment", "Severe cirrhosis"]
    )

search_clicked = st.button("🔍 Evaluate Drug Safety", type="primary")

if search_clicked:
    if not drug_input:
        st.warning("⚠️ Please enter a drug name or active ingredient first.")
    else:
        try:
            with st.spinner("🔬 Analyzing drug safety profile..."):
                context = retrieve_full_drug_context(drug_input)
        except Exception as e:
            st.error(f"System error during retrieval: {e}")
            st.stop()

        # Safe Refusal Check
        active_ing = context.get("active_ingredient")
        if not context or not active_ing or active_ing.lower() == "unknown":
            st.error(
                "### 🚫 Verdict: SAFE REFUSAL\n"
                "**Message:** Unable to find verified guidelines for this query.\n\n"
                "_This tool cannot generate advice without grounded, sourced evidence. "
                "Please verify the drug name or consult a physician._"
            )
            st.stop()

        # Evaluate Unified Verdict
        decision = evaluate_clinical_decision(context, patient_condition)
        
        drug_info = {
            "drug_name": context.get("query_drug", drug_input),
            "active_ingredient": active_ing,
        }
        guardrails = apply_fda_guardrails(patient_condition, drug_info)

        # Verdict Banner
        drug_name = context.get("query_drug") or drug_input
        banner_lines = [
            f"### Verdict: {decision['status']}",
            f"**Drug:** {drug_name}",
            f"**Active Ingredient:** {active_ing}",
            f"**Assessment:** {decision['verdict']}",
            f"**Action:** {decision['action']}"
        ]
        
        if guardrails.get("requires_physician_approval"):
            banner_lines.append("⚠️ **Physician approval required before use.**")

        banner_text = "  \n".join(banner_lines)

        if decision["ui_type"] == "error":
            st.error(banner_text)
        elif decision["ui_type"] == "warning":
            st.warning(banner_text)
        else:
            st.success(banner_text)

        st.divider()

        # === CLINICAL SUMMARY (LLM Narrative) ===
        st.subheader("📋 Clinical Summary")
        
        with st.spinner("🧠 Generating clinical summary..."):
            clinical_summary = generate_grounded_answer(context, guardrails)
        
        st.markdown(clinical_summary)
        st.caption("_Generated from FDA + LiverTox evidence. Not a substitute for professional medical advice._")
        
        st.divider()

        # === CLINICAL METRICS (Source printed here) ===
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Ingredient", context.get("active_ingredient", "N/A"))
            st.metric("Hepatotoxicity Score", context.get("livertox_score", "N/A"))
        
        with col2:
            st.metric("Risk Level", guardrails.get("risk_level", "unknown").upper())
            if guardrails.get("dose_adjustment"):
                st.metric("Dose Limit", guardrails["dose_adjustment"])
        
        with col3:
            source_url = context.get("source_url")
            if source_url:
                st.markdown(f"**Source:** [{source_url}]({source_url})")
            else:
                st.markdown("**Source:** FDA openFDA")
            
            # Show retrieval errors if any
            errors = context.get("errors", [])
            if errors:
                st.markdown("**⚠️ Notes:**")
                for err in errors:
                    st.caption(f"- {err}")

        st.divider()

        # === DETAILED EVIDENCE ===
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🔬 FDA & LiverTox Data")
            with st.container():
                fda_warn = context.get("fda_warnings")
                fda_hep = context.get("fda_hepatic_guidance")
                lvtox_sum = context.get("livertox_summary")
                
                if fda_warn:
                    st.markdown(f"**FDA Warnings:** {fda_warn}")
                if fda_hep:
                    st.markdown(f"**FDA Hepatic Guidance:** {fda_hep}")
                if lvtox_sum:
                    st.markdown(f"**LiverTox Summary:** {lvtox_sum}")
                
                if not any([fda_warn, fda_hep, lvtox_sum]):
                    st.info("No detailed clinical data available for this drug.")

        with col_right:
            st.subheader("📚 Evidence Metadata")
            with st.container():
                st.markdown("**Evidence Source:** LiverTox / FDA openFDA")
                st.markdown(f"**Queried Drug:** {drug_name}")
                st.markdown(f"**Resolved Ingredient:** {active_ing}")
                
                if guardrails.get("specific_warnings"):
                    st.markdown("**Specific Warnings:**")
                    for warning in guardrails["specific_warnings"]:
                        st.markdown(f"- ⚠️ {warning}")

st.divider()
st.markdown("**⚕️ Clinical Disclaimer**")
st.caption(
    "This tool is intended for clinical decision support only and is not a "
    "substitute for professional medical judgment. Verify all information with "
    "a qualified healthcare professional before clinical use."
)