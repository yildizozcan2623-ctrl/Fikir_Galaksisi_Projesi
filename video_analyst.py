def generate_quick_preview_prompt(title, description, comments, user_language="tr"):
    short_comments = []
    for comment in comments[:1]:
        if len(comment) > 80:
            short_comments.append(comment[:80] + "...")
        else:
            short_comments.append(comment)
    
    joined_comments = "\n".join([f"- {c}" for c in short_comments]) if short_comments else "Yorum bulunamadı"

    prompt = f"""
Bu video hakkında metadata analizi yap:

📌 Başlık: {title}
📝 Açıklama: {description[:200]}...
💬 Yorumlar: {joined_comments}

Video gerçekten ne anlatıyor?
Neleri kullanıyor, ne hedefleniyor?
Ben ne için bu videoyu izlemeli ve zaman ayırmalıyım?

Hadi başlayalım, iyi talep vb. başlangıçlar yapma. Doğrudan analiz içeriğine başla! Başlık ve açıklamadaki anahtar kelimeleri analiz ederek akıcı bir şekilde cevap ver. Her başlık altında maksimum 1-2 cümle olsun. 
"""
    return prompt


def generate_detailed_analysis_prompt(title, description, comments, transcript, user_language="tr"):
    prompt = f"""
Bu video transkriptini temiz ve anlamlı bir dokümana dönüştür:

📌 Video: {title}
📄 Transkript: {transcript}

Kurallar:
1. **Doğrudan içeriğe başla** - Video başlığı, Giriş cümleleri, açıklama veya chatbot tarzı ifadeler kullanma
2. **Orijinal Anlatım Düzenini Koru:**
   - Video nasıl anlatıyorsa o şekilde yaz
   - Video'nun doğal akışını bozma
3. **Temizle ve Düzenle:**
   - Gereksiz sesleri çıkar (ummm, ahh)
   - Devrik cümleleri düzelt
   - Anlamsız tekrarları temizle
   - Akıcı ve anlaşılır yap
4. **Teknik İçeriği Koru:**
   - Teknik terimleri açıkla
   - Kod örneklerini düzgün formatla
   - Önemli noktaları vurgula
5. **Zaman Damgalarını Kullan:**
   - Video akışını takip et
   - Bölümleri belirt
   - Önemli geçişleri göster

ÖNEMLİ: Doğrudan video içeriğini yazmaya başla. "Harika bir fikir!", "İşte...", "Bu video..." gibi giriş cümleleri kullanma.
"""
    return prompt




