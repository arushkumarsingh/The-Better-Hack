import subprocess

def extract_audio(video_path, audio_path="temp_audio.wav"):
    subprocess.run(["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"])
    return audio_path
