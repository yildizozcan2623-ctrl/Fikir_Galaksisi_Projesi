import os
import io
import re
import json
import emoji
import streamlit as st
import requests
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def remove_emojis(text):
    return emoji.replace_emoji(text, replace='')


def clean_text_for_title(text):
    return ''.join(c for c in remove_emojis(text) if c.isprintable())


def register_font():
    font_name = "Helvetica"
    try:
        arial_path = r'C:\Windows\Fonts\arial.ttf'
        if os.path.exists(arial_path):
            pdfmetrics.registerFont(TTFont("Arial", arial_path))
            font_name = "Arial"
    except:
        pass
    return font_name


def get_styles(font_name):
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=30, alignment=TA_CENTER,
            textColor=colors.darkblue, fontName=font_name, encoding='utf-8'
        ),
        "subtitle": ParagraphStyle(
            'CustomSubtitle', parent=styles['Heading2'],
            fontSize=13, spaceBefore=16, spaceAfter=12, leading=16,
            alignment=TA_LEFT, textColor=colors.HexColor("#2c3e50"),
            fontName=font_name, encoding='utf-8'
        ),
        "normal": ParagraphStyle(
            'CustomNormal', parent=styles['Normal'],
            fontSize=11, spaceAfter=12, alignment=TA_JUSTIFY,
            fontName=font_name, encoding='utf-8'
        ),
        "small": ParagraphStyle(
            'CustomSmall', parent=styles['Normal'],
            fontSize=9, spaceAfter=6, textColor=colors.grey,
            fontName=font_name, encoding='utf-8'
        ),
    }


def add_title_section(story, note_data, styles):
    title_text = note_data.get("video_title") or note_data.get("title") or "Analiz Dokümanı"
    if "video_title" in note_data:
        title = "Video Analizi: " + clean_text_for_title(title_text.strip())
    elif "title" in note_data:
        title = "Ön Analiz: " + clean_text_for_title(title_text.strip())
    else:
        title = title_text
    story.append(Paragraph(title, styles["title"]))
    story.append(Spacer(1, 20))


def add_metadata_section(story, note_data, styles):
    if created := note_data.get("created_at"):
        story.append(Paragraph(f"Tarih: {created[:10]}", styles["small"]))
        story.append(Spacer(1, 15))


def add_analysis_section(story, note_data, styles):
    if analysis := note_data.get("analysis_result"):
        for para in analysis.split('\n\n'):
            clean_para = remove_emojis(re.sub(r"[`*]", "", para.strip()))
            if clean_para:
                story.append(Paragraph(clean_para, styles["normal"]))
                story.append(Spacer(1, 10))


def add_notes_section(story, note_data, styles):
    if notes := note_data.get("user_notes"):
        story.append(PageBreak())
        story.append(Paragraph("Benim Notlarım", styles["subtitle"]))
        story.append(Spacer(1, 15))
        for para in notes.split('\n\n'):
            clean_para = remove_emojis(para.strip())
            if clean_para:
                story.append(Paragraph(clean_para, styles["normal"]))
                story.append(Spacer(1, 10))


def add_source_section(story, note_data, styles):
    if source := note_data.get("source_url"):
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Kaynak: {source}", styles["small"]))


def create_pdf_from_analysis(note_data, filename):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        font_name = register_font()
        styles = get_styles(font_name)
        story = []

        add_title_section(story, note_data, styles)
        add_metadata_section(story, note_data, styles)
        add_analysis_section(story, note_data, styles)
        add_notes_section(story, note_data, styles)
        add_source_section(story, note_data, styles)

        doc.build(story)
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"PDF oluşturma hatası: {e}")
        return None


def send_pdf_to_email(note_data):
    try:
        title = note_data.get("video_title") or note_data.get("title") or "Analiz Dokümanı"
        created = note_data.get("created_at", "")[:10]
        analysis = note_data.get("analysis_result", "")
        source = note_data.get("source_url", "")

        def clean_analysis(analysis):
            cleaned = []
            for para in analysis.split("\n\n"):
                para = re.sub(r"`?\d{1,2}[:.]\d{2}`?", "", para).strip()

                if para.startswith("**") and para.endswith("**") and len(para) < 80:
                    content = para.strip("* ")
                    para = f"<h3 style='color:#2c3e50;'>{content}</h3>"
                else:
                    para = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", para)
                    para = f"<p style='font-size:15px; line-height:1.8; margin-bottom:14px; color:#333;'>{para}</p>"

                cleaned.append(para)
            return "\n".join(cleaned)

        html_parts = [f"""
        <div style="font-family:Segoe UI, sans-serif; background:#ffffff; padding:24px; border-radius:10px; max-width:700px; margin:auto; color:#2c3e50;">
            <h2 style="color:#2c3e50; font-size:24px; margin-bottom:10px;">📊 {title}</h2>
            <p style="margin:0; font-size:14px; color:#555;"><strong>📅 Tarih:</strong> {created}</p>
        """]

        if analysis:
            html_parts.append("""
            <h3 style="color:#e74c3c; margin-top:30px; font-size:18px;">📌 Analiz</h3>
            """)
            html_parts.append(clean_analysis(analysis))

        if source:
            html_parts.append(f"""
            <hr style="margin:30px 0;">
            <p style="font-size:14px; color:#555;">
                <strong>🔗 Kaynak:</strong> <a href="{source}" style="color:#1abc9c; text-decoration:none;">{source}</a>
            </p>
            """)

        html_parts.append("</div>")
        html_content = "".join(html_parts)

        payload = {
            "subject": f"📩 {title}",
            "html": html_content
        }

        webhook_url = "your_n8n_url"
        response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"})

        if response.status_code == 200:
            st.success("📤 İçerik başarıyla e-posta ile gönderildi!")
        else:
            st.error(f"❌ Gönderim hatası: {response.status_code}")

    except Exception as e:
        st.error(f"⚠️ Hata: {e}")

def generate_pdf_download_button(note_data, index):
    try:
        pdf_buffer = create_pdf_from_analysis(note_data, f"analiz_{index}")
        if not pdf_buffer:
            st.error("❌ PDF oluşturulamadı")
            return

        raw_name = note_data.get("video_title") or note_data.get("title") or "analiz"
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', raw_name[:50])
        date_suffix = note_data.get("created_at", "")[:10]
        filename = f"{clean_name}_{date_suffix}.pdf"

        st.download_button(
            label="📄 PDF İndir",
            data=pdf_buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            key=f"download_pdf_file_{index}"
        )

        if st.button("📧 PDF'yi Mail Gönder", key=f"email_pdf_file_{index}"):
            send_pdf_to_email(note_data)

    except Exception as e:
        st.error(f"❌ PDF hatası: {e}")
