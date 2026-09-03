import os
from typing import Optional

# Import at module level for performance; gracefully handle missing package
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


def _build_prompt(context: dict, risk_level: Optional[str] = None) -> str:
    """Build a strictly-grounded prompt using only fields already present in context."""
    risk_line = f"FDA Risk Classification: {risk_level.upper()}\n" if risk_level else ""
    
    return (
        f"Drug queried: {context.get('query_drug')}\n"
        f"Active ingredient: {context.get('active_ingredient')}\n"
        f"LiverTox hepatotoxicity score: {context.get('livertox_score')}\n"
        f"LiverTox summary: {context.get('livertox_summary')}\n"
        f"FDA general warnings: {context.get('fda_warnings')}\n"
        f"FDA hepatic-specific guidance: {context.get('fda_hepatic_guidance')}\n"
        f"{risk_line}"
        f"Source: {context.get('source_url')}\n\n"
        "Using ONLY the information above, write a short (3-5 sentence) grounded "
        "clinical summary of this drug's liver-safety profile for a patient with "
        "hepatic impairment. Do not add any medical fact that is not present above. "
        "If a field says 'Unknown', is empty, or indicates no record was found, "
        "explicitly say that this information is not available rather than guessing."
    )


def _fallback_answer(context: dict, risk_level: Optional[str] = None) -> str:
    """Deterministic, template-based answer built only from retrieved context.
    Used when no valid API key is configured or the LLM call fails, so the
    Streamlit app never breaks."""
    # ✅ FIX #3: Validate context is a dict
    if not isinstance(context, dict):
        return "Error: Invalid context provided. Please provide a valid drug query."
    
    drug = context.get("query_drug") or "the queried drug"
    ingredient = context.get("active_ingredient") or "Unknown"
    score = context.get("livertox_score")
    summary = context.get("livertox_summary")
    fda_warn = context.get("fda_warnings") or "No FDA warning data available."
    fda_hep = context.get("fda_hepatic_guidance") or "No FDA hepatic guidance available."
    
    # ✅ FIX #4: Include risk classification in fallback
    risk_banner = ""
    if risk_level:
        emoji = {"safe": "✅", "caution": "⚠️", "contraindicated": "🚫"}.get(risk_level, "ℹ️")
        risk_banner = f"\n\n**Risk Classification: {emoji} {risk_level.upper()}**\n"

    if not score or str(score).strip().upper() == "UNKNOWN":
        return (
            f"No specific LiverTox hepatotoxicity record was found locally for "
            f"'{drug}' (active ingredient resolved to: {ingredient}). "
            "A grounded liver-safety statement cannot be generated without a "
            "matching local record. Please verify with a licensed physician or "
            "an official LiverTox lookup."
        )

    return (
        f"**{drug}** (active ingredient: {ingredient}) has a LiverTox "
        f"hepatotoxicity category of **{score}**."
        f"{risk_banner}\n\n"
        f"LiverTox summary: {summary or 'Not available.'}\n\n"
        f"FDA general warning: {fda_warn}\n\n"
        f"FDA hepatic-specific guidance: {fda_hep}\n\n"
        "_This summary is grounded strictly in the retrieved local records above; "
        "no external medical knowledge was used to generate it._"
    )


def generate_grounded_answer(context: dict, guardrails_result: Optional[dict] = None) -> str:
    """
    Generate a natural-language, evidence-grounded answer using ONLY the
    already-retrieved FDA + LiverTox context.

    Falls back to a deterministic, context-only template if:
      - no valid OPENAI_API_KEY is configured, or
      - the OpenAI API call fails for any reason, or
      - the openai package is not installed

    This function never raises — it always returns a usable string.
    """
    # ✅ FIX #3: Validate context
    if not isinstance(context, dict):
        return "Error: Invalid context provided. Please provide a valid drug query."
    
    # Extract risk info from guardrails if provided
    risk_level = None
    system_instructions = (
        "You are a clinical decision-support assistant. Use ONLY the "
        "information given to you in the user message. Never introduce "
        "outside medical facts. If information is missing or marked "
        "Unknown, say so explicitly."
    )
    
    # ✅ FIX #2: Integrate guardrails if available
    if guardrails_result and isinstance(guardrails_result, dict):
        risk_level = guardrails_result.get("risk_level")
        if guardrails_result.get("system_instructions"):
            system_instructions = guardrails_result["system_instructions"]
    
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    # No key, or placeholder -> fallback immediately
    if not api_key or api_key == "dummy_key_for_demo" or not _OPENAI_AVAILABLE:
        return _fallback_answer(context, risk_level)

    try:
        client = OpenAI(api_key=api_key)
        prompt = _build_prompt(context, risk_level)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,  # ✅ FIX #5: Increased for complex drugs
            temperature=0.1,  # Even lower for clinical precision
        )

        text = (response.choices[0].message.content or "").strip()
        return text if text else _fallback_answer(context, risk_level)

    except Exception as e:
        # Log error in production; here we silently fallback for demo stability
        return _fallback_answer(context, risk_level)


if __name__ == "__main__":
    # Test with mock context
    test_context = {
        "query_drug": "Acetaminophen",
        "active_ingredient": "acetaminophen",
        "livertox_score": "A",
        "livertox_summary": "Well-known hepatotoxic agent at high doses.",
        "fda_warnings": "Liver damage risk above 4g/day.",
        "fda_hepatic_guidance": "Max 2g/day in liver disease.",
        "source_url": "https://livertox.nih.gov/acetaminophen.htm"
    }
    
    test_guardrails = {
        "risk_level": "caution",
        "system_instructions": "You are a clinical assistant... [guardrails text]"
    }
    
    print(generate_grounded_answer(test_context, test_guardrails))