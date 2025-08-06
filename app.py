import streamlit as st
import re
import json
import os
from datetime import datetime
from utils import is_valid_url, is_safe_url, extract_video_id, is_valid_github_url, extract_github_repo_info
from video_analyst import generate_quick_preview_prompt, generate_detailed_analysis_prompt
from rag_chatbot import render_chatbot_page
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_api import get_video_details, get_top_comments
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import requests
from urllib.parse import urlparse
from pdf_utils import create_pdf_from_analysis, generate_pdf_download_button
from quick_look import render_quick_look
from detailed_analysis import render_detailed_analysis
from document_utils import render_documents_page, save_user_notes, save_preliminary_analysis, get_saved_notes_list
from transcript_utils import get_enhanced_transcript
from github_utils import extract_github_repo_info, generate_github_analysis_prompt
from user_profile import ask_user_profile


st.set_page_config(page_title="Fikir Galaksisi", layout="wide")
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")

st.sidebar.markdown("# **🪐 Fikir Galaksisi**")
st.sidebar.markdown("---")
st.sidebar.markdown("**☑️ Menü Seçin:**")

menu_options = ["🚀 Hızlı Bakış", "📊 Detaylı Analiz", "🗂️ Dokümanlar", "🤖 AI Asistan", "👤 Profil"]

if st.sidebar.button("**🚀 Hızlı Bakış**", use_container_width=True, key="menu_quick"):
    st.session_state.selected_menu = "🚀 Hızlı Bakış"

if st.sidebar.button("**📊 Detaylı Analiz**", use_container_width=True, key="menu_detailed"):
    st.session_state.selected_menu = "📊 Detaylı Analiz"

if st.sidebar.button("**🗂️ Dokümanlar**", use_container_width=True, key="menu_collection"):
    st.session_state.selected_menu = "🗂️ Dokümanlar"

if st.sidebar.button("**🤖 AI Asistan**", use_container_width=True, key="menu_chatbot"):
    st.session_state.selected_menu = "🤖 AI Asistan"

st.sidebar.markdown("---")
if st.sidebar.button("**👤 Profil**", use_container_width=True, key="menu_profile"):
    st.session_state.selected_menu = "👤 Profil"

if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = "👤 Profil"

menu = st.session_state.selected_menu

if menu == "🚀 Hızlı Bakış":
    render_quick_look(
        model=model,
        save_fn=save_preliminary_analysis,
        github_info_fn=extract_github_repo_info,
        github_prompt_fn=generate_github_analysis_prompt
    )

elif menu == "📊 Detaylı Analiz":
    render_detailed_analysis(
        model=model,
        get_transcript_fn=get_enhanced_transcript,
        save_fn=save_user_notes
    )

elif menu == "🗂️ Dokümanlar":
    render_documents_page(get_saved_notes_list)

elif menu == "🤖 AI Asistan":
    render_chatbot_page(get_saved_notes_list, model)

elif menu == "👤 Profil":
    ask_user_profile()

