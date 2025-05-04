import os
import json
import pickle
from pathlib import Path
from preprocess.extract_audio import extract_audio
from preprocess.transcribe import transcribe_audio
from preprocess.keyframes import extract_keyframes
from preprocess.keyframe_analysis import summarize_keyframe, consolidate_user_journey
from agent.generate_doc import generate_folder_structure, generate_markdown_skeletons, populate_markdown_files
from agent.create_presentation import create_feature_presentation
from tqdm import tqdm
import argparse

# Define cache directory
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_path(name, video_path):
    # Create a cache filename based on the video path
    video_hash = str(abs(hash(video_path)))[-8:]
    return CACHE_DIR / f"{name}_{video_hash}.pkl"

def load_from_cache(cache_path):
    """Load data from cache if it exists"""
    if cache_path.exists():
        print(f"Loading from cache: {cache_path}")
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return None

def save_to_cache(data, cache_path):
    """Save data to cache"""
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"Saved to cache: {cache_path}")

def process_audio(video_path, force=False):
    """Extract audio from video"""
    cache_path = get_cache_path("audio", video_path)
    
    if not force:
        cached = load_from_cache(cache_path)
        if cached:
            return cached
    
    print("Extracting audio...")
    audio_path = extract_audio(video_path)
    save_to_cache(audio_path, cache_path)
    return audio_path

def process_transcript(audio_path, force=False):
    """Transcribe audio"""
    cache_path = get_cache_path("transcript", audio_path)
    
    if not force:
        cached = load_from_cache(cache_path)
        if cached:
            return cached
    
    print("Transcribing...")
    transcript = transcribe_audio(audio_path)
    save_to_cache(transcript, cache_path)
    return transcript

def process_keyframes(video_path, force=False):
    """Extract keyframes from video"""
    cache_path = get_cache_path("keyframes", video_path)
    
    if not force:
        cached = load_from_cache(cache_path)
        if cached:
            return cached
    
    print("Extracting keyframes...")
    keyframes = extract_keyframes(video_path)
    save_to_cache(keyframes, cache_path)
    return keyframes

def process_keyframe_summaries(keyframes, force=False):
    """Analyze keyframes and generate summaries"""
    # Create a unique identifier for the keyframes
    keyframes_id = str(len(keyframes)) + "_" + str(hash(str(keyframes[0]) if keyframes else ""))
    cache_path = get_cache_path(f"keyframe_summaries_{keyframes_id}", str(keyframes_id))
    
    if not force:
        cached = load_from_cache(cache_path)
        if cached:
            return cached
    
    print("Analyzing keyframes...")
    keyframe_summaries = []
    prev_context = None
    for kf in tqdm(keyframes):
        summary = summarize_keyframe(kf['path'], kf['timestamp'], previous_context=prev_context)
        keyframe_summaries.append(summary)
        # Use first 2 lines of this summary as context for the next keyframe
        prev_context = '\n'.join(summary.splitlines()[:2])
    
    save_to_cache(keyframe_summaries, cache_path)
    return keyframe_summaries

def process_user_journey(keyframe_summaries, force=False):
    """Consolidate keyframe summaries into a user journey"""
    cache_path = get_cache_path("user_journey", str(len(keyframe_summaries)))
    
    if not force:
        cached = load_from_cache(cache_path)
        if cached:
            return cached
    
    print("Consolidating user journey...")
    user_journey_flow = consolidate_user_journey(keyframe_summaries)
    save_to_cache(user_journey_flow, cache_path)
    return user_journey_flow

def process_documentation(transcript, user_journey_flow, base_path="output/docs", force=False, language=None):
    """Generate documentation from transcript and user journey"""
    cache_path = get_cache_path("folder_structure", str(hash(str(user_journey_flow))))
    
    if not force:
        cached = load_from_cache(cache_path)
        if cached and not force:
            folder_structure = cached
        else:
            print("Generating documentation folder structure...")
            folder_structure = generate_folder_structure(transcript, user_journey_flow, language=language)
            save_to_cache(folder_structure, cache_path)
    else:
        print("Generating documentation folder structure...")
        folder_structure = generate_folder_structure(transcript, user_journey_flow, language=language)
        save_to_cache(folder_structure, cache_path)
    
    print("Creating markdown skeletons...")
    generate_markdown_skeletons(folder_structure, user_journey_flow, base_path=base_path)
    
    print("Populating documentation files...")
    populate_markdown_files(folder_structure, transcript, user_journey_flow, base_path=base_path, language=language)
    
    return base_path

def create_presentation(keyframe_summaries, user_journey_flow, keyframe_paths, output_path="output/presentation", force=False, language=None):
    """Create a presentation from keyframes and user journey"""
    print("Generating feature presentation...")
    presentation_path = create_feature_presentation(
        keyframe_summaries,
        user_journey_flow,
        keyframe_paths,
        output_path=output_path,
        language=language
    )
    return presentation_path

def main():
    parser = argparse.ArgumentParser(description='Process a video and generate documentation.')
    parser.add_argument('video_path', help='Path to the video file')
    parser.add_argument('--steps', nargs='+', default=['all'], 
                        choices=['audio', 'transcript', 'keyframes', 'summaries', 'journey', 'docs', 'presentation', 'all'],
                        help='Specify which steps to run')
    parser.add_argument('--force', action='store_true', help='Force regeneration of cached data')
    parser.add_argument('--output', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    # Create output directories
    output_dir = Path(args.output)
    docs_dir = output_dir / "docs"
    presentation_dir = output_dir / "presentation"
    docs_dir.mkdir(exist_ok=True, parents=True)
    presentation_dir.mkdir(exist_ok=True, parents=True)
    
    # Track what we've processed for use in later steps
    results = {}
    
    # Run selected steps
    steps = args.steps
    if 'all' in steps:
        steps = ['audio', 'transcript', 'keyframes', 'summaries', 'journey', 'docs', 'presentation']
    
    for step in steps:
        if step == 'audio':
            results['audio_path'] = process_audio(args.video_path, force=args.force)
        
        elif step == 'transcript':
            if 'audio_path' not in results:
                results['audio_path'] = process_audio(args.video_path, force=args.force)
            results['transcript'] = process_transcript(results['audio_path'], force=args.force)
        
        elif step == 'keyframes':
            results['keyframes'] = process_keyframes(args.video_path, force=args.force)
        
        elif step == 'summaries':
            if 'keyframes' not in results:
                results['keyframes'] = process_keyframes(args.video_path, force=args.force)
            results['keyframe_summaries'] = process_keyframe_summaries(results['keyframes'], force=args.force)
        
        elif step == 'journey':
            if 'keyframe_summaries' not in results:
                if 'keyframes' not in results:
                    results['keyframes'] = process_keyframes(args.video_path, force=args.force)
                results['keyframe_summaries'] = process_keyframe_summaries(results['keyframes'], force=args.force)
            results['user_journey'] = process_user_journey(results['keyframe_summaries'], force=args.force)
        
        elif step == 'docs':
            if 'transcript' not in results:
                if 'audio_path' not in results:
                    results['audio_path'] = process_audio(args.video_path, force=args.force)
                results['transcript'] = process_transcript(results['audio_path'], force=args.force)
            
            if 'user_journey' not in results:
                if 'keyframe_summaries' not in results:
                    if 'keyframes' not in results:
                        results['keyframes'] = process_keyframes(args.video_path, force=args.force)
                    results['keyframe_summaries'] = process_keyframe_summaries(results['keyframes'], force=args.force)
                results['user_journey'] = process_user_journey(results['keyframe_summaries'], force=args.force)
            
            docs_path = process_documentation(
                results['transcript'], 
                results['user_journey'],
                base_path=str(docs_dir),
                force=args.force
            )
            results['docs_path'] = docs_path
            print(f"Documentation saved to {docs_path}")
        
        elif step == 'presentation':
            if 'keyframe_summaries' not in results:
                if 'keyframes' not in results:
                    results['keyframes'] = process_keyframes(args.video_path, force=args.force)
                results['keyframe_summaries'] = process_keyframe_summaries(results['keyframes'], force=args.force)
            
            if 'user_journey' not in results:
                results['user_journey'] = process_user_journey(results['keyframe_summaries'], force=args.force)
            
            if 'keyframes' not in results:
                results['keyframes'] = process_keyframes(args.video_path, force=args.force)
            
            keyframe_paths = [kf['path'] for kf in results['keyframes']]
            presentation_path = create_presentation(
                results['keyframe_summaries'],
                results['user_journey'],
                keyframe_paths,
                output_path=str(presentation_dir),
                force=args.force
            )
            results['presentation_path'] = presentation_path
            print(f"Presentation saved to {presentation_path}")
    
    # Save a summary of what was processed
    with open(output_dir / "process_summary.json", 'w') as f:
        summary = {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v 
                  for k, v in results.items()}
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()