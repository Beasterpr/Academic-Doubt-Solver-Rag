import os

from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

import streamlit as st

# ENV

load_dotenv()

groq_api = os.getenv("GROQ_API_KEY")

# MODELS

@st.cache_resource
def embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


@st.cache_resource
def llm_model():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=groq_api,
        temperature=0,
    )
