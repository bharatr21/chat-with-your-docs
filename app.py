import streamlit as st

# ChromaDB monkey patching
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from process_document import upload_file, cleanup
from embed_and_retrieve import create_query_engine, validate_api_key

import openai
import requests
import logging

logger = logging.getLogger()

def validate_api_key(provider, api_key):
    if provider == "OpenAI":
        try:
            url = "https://api.openai.com/v1/engines"
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except openai.OpenAIError as e:
            return False
    elif provider == "HuggingFace":
        if not api_key:
            return True
        try:
            response = requests.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            return response.status_code == 200
        except:
            return False

# Initialize session state variables
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Streamlit app
st.title("Chat with Your Documents")

# Sidebar
st.sidebar.header("Configuration")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload a document (Max size 25MB)", type=["pdf", "docx", "pptx", "csv"])

# Validate file upload and ensure it is a supported file type less than or equal to 25MB
if uploaded_file:
    if uploaded_file.size > 25 * 1024 * 1024:
        st.sidebar.error("File size exceeds 25MB limit!")
        uploaded_file = None
    elif uploaded_file.type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "text/csv"]:
        st.sidebar.error("Unsupported file type!")
        uploaded_file = None

# Provider selection
provider = st.sidebar.selectbox("Select Provider", ["OpenAI", "HuggingFace"])

# API key input
api_key = st.sidebar.text_input("Enter API Key", type="password")

# Validate API key when entered
if api_key:
    if validate_api_key(provider, api_key):
        st.sidebar.success("API key is valid!")
    else:
        st.sidebar.error("Invalid API key!")

# Enable/disable embed button
embed_button = st.sidebar.button("Embed", disabled=not (uploaded_file and (validate_api_key(provider, api_key) or (provider == "HuggingFace" and not api_key))))

# Embed document when button is clicked
if embed_button and uploaded_file:
    with st.spinner("Embedding document..."):
        file_path = upload_file(uploaded_file)
        st.session_state.query_engine = create_query_engine(file_path, provider, api_key)
        st.session_state.messages = []  # Clear chat history
    
    st.sidebar.success("Document embedded successfully!")

# Chat interface
st.subheader("Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your document", disabled=not st.session_state.query_engine):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        if st.session_state.query_engine:
            response = st.session_state.query_engine.query(prompt)
            full_response = response.response
            message_placeholder.markdown(full_response)
        else:
            full_response = "Please upload and embed a document first."
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Register cleanup function
import atexit
atexit.register(cleanup)