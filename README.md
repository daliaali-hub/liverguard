🛡️ LiverGuard

A clinical drug-safety assistant for patients with liver disease. Enter a drug name (brand or generic) and LiverGuard returns a safety verdict, a grounded clinical summary, and the sources behind it.


⚠️ Disclaimer: This is a prototype for educational purposes. It is not a substitute for professional medical advice.

What it does
Resolves the drug name: converts a brand name (e.g. Panadol) to its active ingredient (Acetaminophen) using a local map plus the RxNav API.
Retrieves evidence: pulls label warnings from the openFDA API and hepatotoxicity data from a local LiverTox dataset.
Applies guardrails: a rule-based layer classifies risk (Caution / High Risk / Contraindicated) and raises the risk level for severe cirrhosis.
Generates a grounded summary: GPT-4o-mini writes a short summary using only the retrieved evidence. If no API key is set or the call fails, a deterministic template is used instead.
Shows the evidence: the Streamlit UI displays the verdict, the sources, and the raw FDA / LiverTox text.
Safety design
Safe refusal: if no verified record is found, the app refuses instead of guessing.
Fail-safe default: unknown drugs are never labeled "Safe"; they default to Caution.
Grounded generation: the LLM is instructed not to add facts that are not in the retrieved context.
Fallback mode: the app keeps working without an API key or without internet.

Python · Streamlit · OpenAI API (GPT-4o-mini) · openFDA API · RxNav API · requests

Limitations
Prototype scale: the local FDA fallback covers only a few drugs, and the rule list is small.
Retrieval is name-based lookup, not semantic search.
The patient severity selector currently affects the guardrail risk level only.
Not clinically validated.
Future work
Expand the LiverTox dataset and drug coverage.
Add semantic retrieval (embeddings + vector store).
Use the patient severity level in the final verdict.
Wrap the pipeline in a FastAPI service and containerize it with Docker.
