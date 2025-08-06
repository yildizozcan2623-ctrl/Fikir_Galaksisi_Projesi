import streamlit as st

def ask_user_profile():
    default = st.session_state.get("user_profile", {})

    with st.container():
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #7b1fa2, #1e88e5);
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                color: white;
                font-family: 'Segoe UI', sans-serif;
                margin-bottom: 20px;
            ">
                <h2 style="margin-top: 0;">🪐 Fikir Galaksisi'ne Hoş Geldiniz!</h2>
                <p style="font-size: 16px; line-height: 1.6;">
                    Yapay zeka destekli bu uygulama, dijital içerikleri sizin için analiz eder, anlamlandırır, sorularınızı yanıtlar, arşivler ve dilediğiniz zaman tekrar erişilebilir hale getirir.<br>
                    Kişisel öğrenme yolculuğunuzu yapay zeka ile daha akıllı ve anlamlı hale getirmeye ne dersiniz?<br><br>
                    🚀 Hazırsanız, sizi daha yakından tanıyalım!
                </p>
            </div>
            """, unsafe_allow_html=True)

    max_selections = 5
    interests = st.multiselect(
        f"📚 Hangi alanlardaki videolar ilginizi çeker? (en fazla {max_selections})",
        ["Yazılım", "Yapay Zeka", "Dil Öğrenme", "Psikoloji", "Tarih", "Kişisel Gelişim", "Girişimcilik", "Felsefe",
         "Teknoloji", "Bilim", "Eğitim"],
        default=default.get("interests", [])
    )

    if len(interests) > max_selections:
        st.warning(f"⚠️ En fazla {max_selections} alan seçebilirsiniz.")
        st.stop()

    levels = {}
    st.markdown("##### 🔍 Seçtiğiniz alanlar için bilgi seviyenizi belirtin:")
    for area in interests:
        levels[area] = st.radio(
            f"🎓 {area} için seviyeniz nedir?",
            ["Yeni Başlayan", "Orta Düzey", "İleri Düzey"],
            horizontal=True,
            index=["Yeni Başlayan", "Orta Düzey", "İleri Düzey"].index(
                default.get("levels", {}).get(area, "Orta Düzey")
            )
        )

    style = st.selectbox(
        "🧠 Hangi tarz anlatımı tercih edersiniz?",
        ["Kod örnekleriyle açıklanan", "Anlatım ağırlıklı", "Görsel / grafik destekli", "Kısa özet odaklı", "Fark etmez"],
        index=["Kod örnekleriyle açıklanan", "Anlatım ağırlıklı", "Görsel / grafik destekli", "Kısa özet odaklı", "Fark etmez"].index(default.get("style", "Fark etmez"))
    )

    intent = st.selectbox(
        "📺 Bu videoları genellikle ne amaçla izliyorsunuz?",
        ["Yeni şeyler öğrenmek", "Uzmanlaşmak", "İlham almak", "Proje araştırması", "Vakit geçirmek / Eğlenmek"],
        index=["Yeni şeyler öğrenmek", "Uzmanlaşmak", "İlham almak", "Proje araştırması", "Vakit geçirmek / Eğlenmek"].index(default.get("intent", "Yeni şeyler öğrenmek"))
    )

    duration = st.selectbox(
        "⏱️ Tercih ettiğiniz video uzunluğu nedir?",
        ["0–5 dk", "5–15 dk", "15+ dk", "Fark etmez"],
        index=["0–5 dk", "5–15 dk", "15+ dk", "Fark etmez"].index(default.get("duration", "Fark etmez"))
    )

    if st.button("✅ Kaydet ve Başla"):
        st.session_state.user_profile = {
            "interests": interests,
            "levels": levels,
            "style": style,
            "intent": intent,
            "duration": duration
        }
        st.success("🎉 Profiliniz kaydedildi!")
        st.session_state.selected_menu = "📊 Detaylı Analiz"
        st.rerun()
