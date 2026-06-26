import streamlit as st
import requests

# ==============================
# Config
# ==============================

BACKEND_URL = "http://127.0.0.1:8000/ask"  # FastAPI /ask endpoint

st.set_page_config(
    page_title="TrustMed AI – Medical Info Assistant",
    page_icon="🩺",
    layout="centered",
)

# ==============================
# Helpers
# ==============================

def call_trustmed_backend(question: str) -> str:
    """
    Call the FastAPI backend /ask endpoint with the user's question.
    Expects JSON: { "question": "..."} and returns the "answer" string.
    """
    try:
        resp = requests.post(
            BACKEND_URL,
            json={"question": question},
            timeout=120,  # Increased timeout for first request (model loading)
        )
        if resp.status_code != 200:
            return f"⚠️ Backend error (HTTP {resp.status_code}): {resp.text}"

        data = resp.json()
        if not data.get("success", True) and "error" in data:
            return f"⚠️ Backend reported an error: {data['error']}"

        answer = data.get("answer")
        if not answer:
            return "⚠️ No answer returned from backend."
        return answer

    except Exception as e:
        return f"⚠️ Failed to contact backend: {e}"


# ==============================
# Streamlit UI
# ==============================

st.title("🩺 TrustMed AI")
st.markdown(
    """
A **medical information assistant** that combines:

- ✅ Trusted disease & treatment information (Mayo-style knowledge graph)  
- 💊 Drug & supplement monographs (side effects, warnings, interactions)  
- 🧩 Key Recurring Themes (KRTs) from real patient/community discussions  
- 🔗 Optional links to similar Reddit threads (for human stories)  
- 🤖 Llama-based answer synthesis, broken into **Trusted info**, **Community**, and **Safety**  

> ⚠️ This is **not** a diagnostic tool and does **not** replace a clinician.
"""
)

# Initialize chat history in session_state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi, I'm **TrustMed** 👋\n\n"
                "I use a medical knowledge graph + community data to explain conditions and treatments.\n\n"
                "You can ask things like:\n"
                "- *“What are the symptoms and treatments for asthma?”*\n"
                "- *“How is type 2 diabetes treated and what side effects do common meds have?”*\n"
                "- *“What should I know about hypertension medications and long-term risks?”*\n"
                "- *“I was recently diagnosed with GERD – what does that mean and how do people cope?”*\n\n"
                "I'll try to:\n"
                "- Separate **trusted medical information** from **anecdotal community experiences**, and\n"
                "- End with a **Safety / Next Steps** section."
            ),
        }
    ]

# Show chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# User input box at bottom
user_input = st.chat_input("Ask about a condition, symptom, or treatment (e.g., “What are treatments for GERD?”)...")

if user_input:
    # 1) Add user message to history
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # 2) Show it immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # 3) Call backend and show assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking with the knowledge graph + community data..."):
            answer = call_trustmed_backend(user_input)
        st.markdown(answer)

    # 4) Save assistant answer in history
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

# Sidebar info
with st.sidebar:
    st.subheader("ℹ️ About this demo")
    st.markdown(
        """
**TrustMed AI** (course project):

- **Backend:** FastAPI `/ask` → `trustmed_agent.py`  
- **Knowledge Graph:** Neo4j  
  - Diseases from Mayo-style webpages  
  - Drugs & supplements (side effects, warnings, interactions, usage)  
  - Reddit posts clustered into Key Recurring Themes (KRTs)  
- **LLM:** `meta-llama/Llama-3.1-8B-Instruct` via HuggingFace  
- **UI:** Streamlit chat

What it tries to do:
- Pull **trusted medical context** for the disease it detects in your question,  
- Pull **relevant drugs** linked to that disease in the graph,  
- Summarize **community themes** (fears, stigma, lifestyle struggles),  
- Optionally show **example Reddit threads** for human stories,  
- Always end with a **Safety / Next Steps** section.

Limitations:
- Not all diseases in the world are in the knowledge graph yet.  
- Sometimes disease detection may be imperfect for very vague questions.  
- This does **not** give personal medical advice or emergency guidance.

Always discuss your own situation with a licensed clinician.
"""
    )
