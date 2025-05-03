import whisper

def format_timestamp(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"[{m:02d}:{s:02d}]"

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    transcript = []
    for seg in result.get('segments', []):
        start = format_timestamp(seg['start'])
        end = format_timestamp(seg['end'])
        text = seg['text'].strip()
        transcript.append({
            'start': start,
            'end': end,
            'text': text
        })
    return transcript
