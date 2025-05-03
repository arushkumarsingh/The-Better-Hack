from preprocess.extract_audio import extract_audio
from preprocess.transcribe import transcribe_audio
from preprocess.keyframes import extract_keyframes
from preprocess.keyframe_analysis import summarize_keyframe, consolidate_user_journey
from agent.generate_doc import generate_folder_structure, generate_markdown_skeletons, populate_markdown_files
from tqdm import tqdm

def main(video_path):
    print("Extracting audio...")
    audio_path = extract_audio(video_path)

    print("Transcribing...")
    transcript = transcribe_audio(audio_path)

    print("Extracting keyframes...")
    keyframes = extract_keyframes(video_path)

    print("Analyzing keyframes...")
    keyframe_summaries = []
    prev_context = None
    for kf in tqdm(keyframes):
        summary = summarize_keyframe(kf['path'], kf['timestamp'], previous_context=prev_context)
        keyframe_summaries.append(summary)
        # Use first 2 lines of this summary as context for the next keyframe
        prev_context = '\n'.join(summary.splitlines()[:2])

    print("Consolidating user journey...")
    user_journey_flow = consolidate_user_journey(keyframe_summaries)

    print("Generating documentation folder structure...")
    folder_structure = generate_folder_structure(transcript, user_journey_flow)

    print("Creating markdown skeletons...")
    generate_markdown_skeletons(folder_structure, user_journey_flow, base_path="output/docs")

    print("Populating documentation files...")
    populate_markdown_files(folder_structure, transcript, user_journey_flow, base_path="output/docs")

    print("Documentation saved to output/docs/")

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
