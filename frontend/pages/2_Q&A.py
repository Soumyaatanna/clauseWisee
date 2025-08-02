import streamlit as st
import requests
import time
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Document Q&A", page_icon="❓", layout="wide")

st.title("Document Q&A")
st.markdown("Ask questions about your legal documents and get instant, context-aware answers.")

# --- Helper function to fetch document list ---
def get_active_docs():
    try:
        response = requests.get(f"{BACKEND_URL}/documents/")
        if response.status_code == 200:
            return [doc['name'] for doc in response.json().get('documents', [])]
    except requests.exceptions.RequestException:
        return [] # Return empty list if backend is not reachable
    return []

# --- Sidebar ---
with st.sidebar:
    st.header("Active Documents")
    st.markdown("Documents available for querying:")
    active_docs = get_active_docs()
    if not active_docs:
        st.info("No documents have been processed yet. Please go to the Upload page.")
    else:
        for doc in active_docs:
            st.success(f"📄 {doc}")

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your legal document assistant. How can I help you understand and analyze your uploaded documents?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What are the key obligations in my service agreement?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        try:
            response = requests.post(f"{BACKEND_URL}/query/", json={"question": prompt})
            if response.status_code == 200:
                answer = response.json().get("answer")
                message_placeholder.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                 message_placeholder.error(f"Failed to get an answer: {response.text}")
                 st.session_state.messages.append({"role": "assistant", "content": f"Failed to get an answer: {response.text}"})

        except requests.exceptions.RequestException as e:
            message_placeholder.error("Connection error: Could not reach the backend.")
            st.session_state.messages.append({"role": "assistant", "content": "Connection error: Could not reach the backend."})