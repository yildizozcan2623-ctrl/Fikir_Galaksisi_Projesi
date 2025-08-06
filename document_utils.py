import os
import json
import streamlit as st
from pdf_utils import generate_pdf_download_button
from datetime import datetime

def render_documents_page(get_saved_notes_list):
    st.header("🗂️ Dokümanlar")
    st.markdown(
        """
        <div style="background-color:#f7f3ff; padding: 20px; border-radius: 10px; border-left: 5px solid #9b59b6;">
            <p><strong>Tüm analizlerinizi</strong> bu bölümde listeleyebilir, başlığa, içeriğe veya tarihe göre arama yapabilirsiniz.</p>
            <p>🧾 İsterseniz geçmiş analizlerinizi PDF olarak indirebilir veya tamamen silebilirsiniz.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    saved_notes = get_saved_notes_list()

    if not saved_notes:
        st.info("📊 Henüz kaydedilmiş analiz bulunmuyor. Detaylı video analizi yaptıktan sonra analizleriniz burada görünecek.")
        return
    st.write("\n")
    type_filter = st.radio("📁 Doküman Türü:", ["Tümü", "Hızlı Bakış", "Detaylı Analiz"], horizontal=True)
    search_option, search_term, search_btn = _render_search_box()

    filtered_by_type = _filter_by_type(saved_notes, type_filter)
    display_notes = _filter_notes(filtered_by_type, search_option, search_term) if search_btn and search_term else [(note, None) for note in filtered_by_type]

    st.markdown("---")
    st.subheader("📚 Tüm Analizler")
    st.caption(f"🧾 {len(display_notes)} kayıt bulundu")

    if not display_notes:
        st.info("📊 Gösterilecek analiz bulunmuyor.")
        return

    _render_notes_list(display_notes)


def _render_search_box():
    col1, col2, col3 = st.columns([2, 4, 1])
    with col1:
        search_option = st.selectbox("🔍 Arama türü:", ["Video başlığına göre", "Analiz içeriğine göre", "Tarihe göre"])
    with col2:
        if search_option == "Video başlığına göre":
            search_term = st.text_input("📝 Video başlığında ara:", placeholder="Örnek: LangChain, Python, AI...")
        elif search_option == "Analiz içeriğine göre":
            search_term = st.text_input("📝 Analiz içeriğinde ara:", placeholder="Örnek: önemli, hatırla, araştır...")
        else:
            search_term = st.date_input("📅 Tarih seçin:")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍", help="Ara")
    return search_option, search_term, search_btn


def _filter_by_type(notes, selected_type):
    if selected_type == "Tümü":
        return notes
    elif selected_type == "Hızlı Bakış":
        return [note for note in notes if note['analysis_type'] != 'detailed']
    else:
        return [note for note in notes if note['analysis_type'] == 'detailed']


def _filter_notes(saved_notes, search_option, search_term):
    filtered_notes = []
    for note in saved_notes:
        try:
            with open(note['filepath'], 'r', encoding='utf-8') as f:
                note_data = json.load(f)
            if search_option == "Video başlığına göre":
                if search_term.lower() in note_data.get('video_title', '').lower() or search_term.lower() in note_data.get('title', '').lower():
                    filtered_notes.append((note, note_data))
            elif search_option == "Analiz içeriğine göre":
                if search_term.lower() in note_data.get('analysis_result', '').lower():
                    filtered_notes.append((note, note_data))
            else:
                if str(search_term) in note_data.get('created_at', '')[:10]:
                    filtered_notes.append((note, note_data))
        except:
            continue
    if not filtered_notes:
        st.warning("🔍 Arama kriterlerinize uygun analiz bulunamadı.")
    return filtered_notes


def _render_notes_list(display_notes):
    for i, (note, note_data) in enumerate(display_notes):
        if note_data is None:
            try:
                with open(note['filepath'], 'r', encoding='utf-8') as f:
                    note_data = json.load(f)
            except:
                continue

        with st.expander(f"{note['title']} - {note['updated_at'][:10]}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(note_data.get('combined_document', 'Analiz bulunamadı'))
            with col2:
                _render_note_metadata(note_data)
                generate_pdf_download_button(note_data, i)
                if st.button(f"🗑️ Sil", key=f"delete_note_{i}"):
                    try:
                        os.remove(note['filepath'])
                        st.success("✅ Analiz silindi!")
                        st.rerun()
                    except:
                        st.error("❌ Analiz silinirken hata oluştu.")


def _render_note_metadata(note_data):
    created_date = note_data.get('created_at', '')[:10]
    st.markdown(f"**📅 Tarih:** {created_date}")
    analysis_type = note_data.get('analysis_type', 'detailed')

    if analysis_type == 'detailed':
        video_id = note_data.get('video_id', '')
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            st.markdown(f"**🎥 Video:** [🔗 YouTube'da İzle]({url})")
            st.video(url, start_time=0)
    elif analysis_type == 'youtube_preliminary':
        identifier = note_data.get('identifier', '')
        if identifier:
            url = f"https://www.youtube.com/watch?v={identifier}"
            st.markdown(f"**🎥 Video:** [🔗 YouTube'da İzle]({url})")
            st.video(url, start_time=0)
    elif analysis_type == 'github_preliminary':
        identifier = note_data.get('identifier', '')
        if identifier:
            url = identifier if 'github.com' in identifier else f"https://github.com/{identifier}"
            st.markdown(f"**🔗 GitHub:** [📂 Repository'yi Görüntüle]({url})")
            _render_github_preview(identifier)
    else:
        st.markdown(f"**🔍 Analiz Türü:** {analysis_type.replace('_', ' ').title()}")
        st.markdown(f"**🆔 Tanımlayıcı:** {note_data.get('identifier', '')}")


def _render_github_preview(identifier):
    if '/' in identifier and 'github.com' not in identifier:
        owner, repo = identifier.split('/', 1)
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                repo_data = response.json()
                st.markdown(f"**📊 Stars:** {repo_data.get('stargazers_count', 0)}")
                st.markdown(f"**🌿 Forks:** {repo_data.get('forks_count', 0)}")
                st.markdown(f"**💻 Language:** {repo_data.get('language', 'N/A')}")
        except:
            pass

def save_user_notes(video_id, video_title, analysis_result, source_url=None):
    import os, json
    from datetime import datetime

    os.makedirs("notes", exist_ok=True)
    filename = f"notes/{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    combined_document = f"""# 📊 Video Analizi: {video_title}\n\n{analysis_result}\n\n---\n*Kaynak: {source_url if source_url else "Bilinmeyen"}*\n*Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}*"""

    notes_data = {
        "video_id": video_id,
        "video_title": video_title,
        "analysis_result": analysis_result,
        "source_url": source_url,
        "combined_document": combined_document,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "filepath": filename
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, ensure_ascii=False, indent=2)
        return filename if os.path.exists(filename) else None
    except Exception:
        return None


def save_preliminary_analysis(analysis_type, identifier, title, analysis_result, source_url=None):
    os.makedirs("notes", exist_ok=True)
    filename = f"notes/{analysis_type}_{identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    combined_document = f"""# 🚀 Hızlı Bakış: {title}

{analysis_result}

"""
    notes_data = {
        "analysis_type": analysis_type,
        "identifier": identifier,
        "title": title,
        "analysis_result": analysis_result,
        "source_url": source_url,
        "combined_document": combined_document,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "filepath": filename
    }
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, ensure_ascii=False, indent=2)
        return filename if os.path.exists(filename) else None
    except:
        return None


def get_saved_notes_list():
    try:
        if not os.path.exists("notes"):
            return []

        notes_list = []
        for filename in os.listdir("notes"):
            if filename.endswith(".json"):
                filepath = os.path.join("notes", filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        title = data.get('title', data.get('video_title', 'Bilinmeyen'))
                        analysis_type = data.get('analysis_type', 'detailed')
                        if analysis_type == 'youtube_preliminary':
                            title = f"🚀 Hızlı Bakış: {title}"
                        elif analysis_type == 'github_preliminary':
                            title = f"🚀 Hızlı Bakış: {title}"
                        else:
                            title = f"📊 Detaylı Analiz: {title}"

                        notes_list.append({
                            "filename": filename,
                            "title": title,
                            "created_at": data.get("created_at", ""),
                            "updated_at": data.get("updated_at", ""),
                            "filepath": filepath,
                            "analysis_type": analysis_type
                        })
                except:
                    continue

        return sorted(notes_list, key=lambda x: x["updated_at"], reverse=True)
    except:
        return []