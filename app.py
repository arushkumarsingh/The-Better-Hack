from preprocess.extract_audio import extract_audio
from preprocess.transcribe import transcribe_audio
from preprocess.keyframes import extract_keyframes
from agent.generate_doc import generate_markdown

def main(video_path):
    print("Extracting audio...")
    audio_path = extract_audio(video_path)

    print("Transcribing...")
    transcript = transcribe_audio(audio_path)

    print("Extracting keyframes...")
    extract_keyframes(video_path)

    print("Generating documentation...")
    keyframe_text = "Screenshots from key parts of the demo have been extracted."
    markdown = generate_markdown(transcript, keyframe_text)

    with open("output/demo_doc.md", "w") as f:
        f.write(markdown)

    print("Documentation saved to output/demo_doc.md")

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
