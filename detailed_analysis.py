import streamlit as st
from youtube_api import get_video_details, get_top_comments
from utils import is_valid_url, is_safe_url, extract_video_id
from video_analyst import generate_detailed_analysis_prompt

def detailed_analysis_introduction():
    st.header("📊 Detaylı Analiz")
    st.markdown(
        """
        <div style="background-color:#f7f3ff; padding: 20px; border-radius: 10px; border-left: 5px solid #9b59b6;">
            <p><strong>Detaylı Analiz</strong> modülü, özellikle İngilizce gibi yabancı dillerde sunulan YouTube eğitim videolarını Türkçe ve anlaşılır bir şekilde takip edebilmek için geliştirilmiştir.<br>
            YouTube altyazıları çoğu zaman hızlı üretildiği için yer yer eksik ya da dil bilgisel olarak yetersiz kalabilir.<br>
            Bu araç, videolardaki transkriptleri yapay zekâ desteğiyle temizleyip düzenleyerek anlamlı, bölümlenmiş ve okunabilir dokümanlara dönüştürür.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
        [![YouTube](https://img.shields.io/badge/-YouTube-red?logo=youtube&logoColor=white&style=flat-square)](https://www.youtube.com)
        """, unsafe_allow_html=True)


def render_detailed_analysis(model, get_transcript_fn, save_fn):
    detailed_analysis_introduction()

    if "detailed_analysis_result" in st.session_state:
        st.markdown(st.session_state.detailed_analysis_result)
        st.success("✅ Detaylı analiz tamamlandı!")
        st.markdown("---")

    col1, col2 = st.columns([9, 1])
    with col1:
        video_url_detailed = st.text_input("", placeholder="🎥 YouTube video linkini gir...", key="detailed_analysis_url", label_visibility="collapsed")
    with col2:
        detailed_btn = st.button("➤", key="detailed_analysis_btn", help="Detaylı Analiz Yap")

    if detailed_btn:
        if not is_valid_url(video_url_detailed):
            st.error("❌ Bu geçerli bir YouTube linki değil.")
        elif not is_safe_url(video_url_detailed):
            st.error("🚨 Güvenli olmayan bir link algılandı.")
        else:
            video_id = extract_video_id(video_url_detailed)
            if video_id:
                details = get_video_details([video_id])
                if details:
                    video_info = details[0]
                    comments = get_top_comments(video_id)

                    st.session_state.video_info = video_info
                    st.session_state.video_id = video_id
                    st.session_state.current_video_id = video_id

                    for key in ["detailed_analysis_result", "detailed_analysis_video_title"]:
                        st.session_state.pop(key, None)

                    try:
                        with st.spinner("⏳ Analiz süreci başladı. Birkaç dakika sürebilir, dilediğiniz gibi arka planda başka işlerinize devam edebilirsiniz."):
                            result = get_transcript_fn(video_id)

                            if result and result[0]:
                                transcript, strategy = result
                                if strategy == "long_video":
                                    st.warning("⚠️ Bu video 45+ dakika uzunluğunda. En anlamlı 45 dakikalık kısım seçildi.")
                            else:
                                st.warning("⚠️ Transkript bulunamadı, video açıklaması kullanılıyor...")
                                st.info("💡 Bu durum şu nedenlerle olabilir:\n• Video'da konuşma yok\n• Video sahibi transkript özelliğini kapatmış\n• Video çok yeni (transkript henüz oluşturulmamış)")
                                transcript = video_info.get("description", "")

                            detailed_prompt = generate_detailed_analysis_prompt(
                                title=video_info["title"],
                                description=video_info.get("description", ""),
                                comments=[],
                                transcript=transcript,
                                user_language="tr"
                            )

                            detailed_response = model.generate_content(detailed_prompt)
                            st.session_state.detailed_analysis_result = detailed_response.text
                            st.session_state.detailed_analysis_video_title = video_info["title"]

                        st.markdown(st.session_state.detailed_analysis_result)
                        st.success("✅ Detaylı analiz tamamlandı!")

                        saved_file = save_fn(
                            video_id=video_id,
                            video_title=video_info["title"],
                            analysis_result=st.session_state.detailed_analysis_result,
                            source_url=video_url_detailed
                        )

                        if saved_file:
                            st.markdown("---")
                            st.info("💡 Bu analiz otomatik olarak kaydedildi. Tüm analizlerinize '🗂️ Dokümanlar' menüsünden ulaşabilirsiniz.")
                        else:
                            st.error("❌ Analiz kaydedilirken hata oluştu.")

                    except Exception as e:
                        if "500" in str(e) or "internal error" in str(e).lower():
                            st.error("❌ API hatası: Video çok uzun veya transkript çok büyük. Lütfen daha kısa bir video deneyin.")
                            st.info("💡 Öneriler: 30 dakikadan kısa videolar daha iyi sonuç verir.")
                        else:
                            st.error(f"❌ Detaylı analiz hatası: {e}")
            else:
                st.error("⚠️ Video ID çıkarılamadı.")