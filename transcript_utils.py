import re
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator

def get_enhanced_transcript(video_id):
    transcript_api = YouTubeTranscriptApi()
    transcript_list, detected_language = get_smart_transcript(video_id, transcript_api)
    if not transcript_list:
        return None, None

    total_duration = transcript_list[-1].start + transcript_list[-1].duration
    strategy = determine_length_strategy(total_duration)

    if strategy == "long_video":
        transcript_list = select_optimal_sections(transcript_list, total_duration)

    translator = GoogleTranslator()
    formatted_transcript = ""
    current_section_start = 0
    last_text = ""

    for i, transcript in enumerate(transcript_list):
        if not hasattr(transcript, 'text'): continue

        text = transcript.text
        start_time = transcript.start
        cleaned_text = clean_transcript_text(text)

        if detected_language == "tr":
            translated_text = cleaned_text
        else:
            try:
                translated = translator.translate(cleaned_text, dest='tr')
                translated_text = improve_translation(cleaned_text, translated.text)
            except:
                translated_text = cleaned_text

        if check_semantic_break_with_strategy(last_text, cleaned_text, start_time, current_section_start, strategy):
            section_header = f"\n**🕒 {int(current_section_start//60):02d}:{int(current_section_start%60):02d} – {int(start_time//60):02d}:{int(start_time%60):02d}**\n"
            formatted_transcript += section_header
            current_section_start = start_time

        time_stamp = f"`{int(start_time//60):02d}:{int(start_time%60):02d}`"
        formatted_transcript += f"{time_stamp} {translated_text}\n"
        last_text = cleaned_text

    return check_and_truncate_transcript(formatted_transcript), strategy


def get_smart_transcript(video_id, transcript_api):
    for lang in [['tr'], ['en', 'en-US'], ['en-US'], ['auto']]:
        try:
            transcripts = transcript_api.fetch(video_id, languages=lang)
            if transcripts:
                return transcripts, lang[0]
        except: pass
    return None, None


def determine_length_strategy(duration_seconds):
    return "normal" if duration_seconds/60 <= 30 else "long_video"


def select_optimal_sections(transcripts, total_duration):
    target = 1800
    start_time = 0 if total_duration/60 <= 60 else (total_duration - target) / 2
    end_time = start_time + target
    selected = [t for t in transcripts if start_time <= t.start <= end_time]
    return selected[::4] if len(selected) > 100 else selected


def check_semantic_break_with_strategy(last_text, current_text, now, start, strategy):
    min_d = 180 if strategy == "normal" else 300
    max_d = 600 if strategy == "normal" else 900
    if now - start < min_d: return False
    if now - start > max_d: return True
    if not last_text or not current_text: return False
    return any(w in current_text.lower() and w in last_text.lower() for w in ['now', 'next', 'finally', 'so', 'okay', 'right'])


def clean_transcript_text(text):
    text = re.sub(r'\b(um+|uh+|ah+|hmm+|huh+)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(like|you know|i mean|basically|actually)\b', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()


def improve_translation(original, translated):
    corrections = {"I'm": "Ben", "I am": "Ben", "So": "Yani", "Now": "Şimdi", "Okay": "Tamam"}
    for eng, tr in corrections.items():
        if eng.lower() in original.lower():
            translated = translated.replace(eng, tr)
    return translated


def check_and_truncate_transcript(transcript, max_tokens=800000):
    estimated = len(transcript.split()) * 1.3
    if estimated <= max_tokens:
        return transcript
    target = int(len(transcript) * (0.5 if estimated < 2 * max_tokens else 0.3))
    return transcript[:target] + "\n\n... (Transkript kısaltıldı)"
