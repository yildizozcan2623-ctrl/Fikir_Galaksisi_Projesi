import streamlit as st
from utils import is_valid_url, is_safe_url, extract_video_id, is_valid_github_url
from youtube_api import get_video_details, get_top_comments
from video_analyst import generate_quick_preview_prompt


def quick_introduction():
    st.header("🚀 Hızlı Bakış")
    st.markdown(
        """
        <div style="background-color:#f7f3ff; padding: 20px; border-radius: 10px; border-left: 5px solid #9b59b6;">
            <p><strong>Hızlı Bakış</strong> bölümü, bir içerik hakkında hızlı şekilde fikir edinmeni sağlar. YouTube videoları veya GitHub projeleri hakkında özet bilgi, amaç, içerik ve fayda değerlendirmesi alırsın.</p>
            <p>🎥 Video izlemeye değer mi?<br>
            🐙 Bu proje bana uygun mu?
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
        [![YouTube](https://img.shields.io/badge/-YouTube-red?logo=youtube&logoColor=white&style=flat-square)](https://www.youtube.com)
        [![GitHub](https://img.shields.io/badge/-GitHub-black?logo=github&logoColor=white&style=flat-square)](https://github.com)
        """, unsafe_allow_html=True)


def render_quick_look(model, save_fn, github_info_fn, github_prompt_fn):
    quick_introduction()

    col1, col2 = st.columns([9, 1])
    with col1:
        analysis_url = st.text_input("", placeholder="🎥 YouTube video linki veya 🐙 GitHub repository linki gir...", key="quick_analysis_url", label_visibility="collapsed")
    with col2:
        quick_btn = st.button("➤", key="quick_analysis_btn", help="Hızlı Bakış At")

    if quick_btn:
        if not is_valid_url(analysis_url) and not is_valid_github_url(analysis_url):
            st.error("❌ Bu geçerli bir YouTube veya GitHub linki değil.")
        elif not is_safe_url(analysis_url):
            st.error("🚨 Güvenli olmayan bir link algılandı.")
        else:
            if "youtube.com" in analysis_url or "youtu.be" in analysis_url:
                _handle_youtube_analysis(analysis_url, model, save_fn)
            elif "github.com" in analysis_url:
                _handle_github_analysis(analysis_url, model, github_info_fn, github_prompt_fn, save_fn)
            else:
                st.error("❌ Desteklenmeyen link türü. YouTube veya GitHub linki girin.")

    _render_quick_analysis_results()


def _handle_youtube_analysis(analysis_url, model, save_fn):
    video_id = extract_video_id(analysis_url)
    if not video_id:
        st.error("⚠️ Video ID çıkarılamadı.")
        return

    details = get_video_details([video_id])
    if not details:
        st.error("❌ Video detayları alınamadı.")
        return

    video_info = details[0]
    comments = get_top_comments(video_id)

    for key in ["quick_analysis_result", "github_analysis_result"]:
        st.session_state.pop(key, None)

    with st.spinner("🔄 YouTube ön analiz yapılıyor..."):
        try:
            quick_prompt = generate_quick_preview_prompt(
                title=video_info["title"],
                description=video_info.get("description", ""),
                comments=comments,
                user_language="tr"
            )
            quick_response = model.generate_content(quick_prompt)

            if quick_response and quick_response.text:
                st.session_state.quick_analysis_result = quick_response.text
                st.session_state.quick_analysis_video_title = video_info["title"]
                save_fn(
                    analysis_type="youtube_preliminary",
                    identifier=video_id,
                    title=video_info["title"],
                    analysis_result=quick_response.text,
                    source_url=analysis_url
                )
            else:
                st.error("❌ API'den yanıt alınamadı.")
        except Exception as e:
            st.error(f"❌ YouTube analiz hatası: {e}")

def _handle_github_analysis(analysis_url, model, github_info_fn, github_prompt_fn, save_fn):
    with st.spinner("🔄 GitHub repository analiz ediliyor..."):
        repo_info, error = github_info_fn(analysis_url)
        if error:
            st.error(f"❌ {error}")
            return

        for key in ["quick_analysis_result", "github_analysis_result"]:
            st.session_state.pop(key, None)

        github_prompt = github_prompt_fn(repo_info)
        github_response = model.generate_content(github_prompt)
        st.session_state.github_analysis_result = github_response.text
        st.session_state.github_analysis_repo = f"{repo_info['owner']}/{repo_info['repo']}"

        save_fn(
            analysis_type="github_preliminary",
            identifier=f"{repo_info['owner']}_{repo_info['repo']}",
            title=f"{repo_info['owner']}/{repo_info['repo']}",
            analysis_result=github_response.text,
            source_url=analysis_url
        )

def _render_quick_analysis_results():
    if "quick_analysis_result" in st.session_state:
        st.markdown(st.session_state.quick_analysis_result)
        st.success("✅ YouTube ön analiz tamamlandı!")
        st.info("💡 Bu analiz otomatik olarak kaydedildi.")
    if "github_analysis_result" in st.session_state:
        st.markdown(st.session_state.github_analysis_result)
        st.success("✅ GitHub analizi tamamlandı!")
        st.info("💡 Bu analiz otomatik olarak kaydedildi.")