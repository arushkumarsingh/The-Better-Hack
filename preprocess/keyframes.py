import cv2
import os
from PIL import Image
import imagehash

def format_timestamp(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"[{m:02d}:{s:02d}]"

def extract_keyframes(video_path, output_dir="output/keyframes", phash_thresh=8, max_per_5s=1):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    prev_hash = None
    frame_id = 0
    saved = 0
    last_saved_sec = -5
    keyframes = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        sec = frame_id / fps
        if sec - last_saved_sec < 5:
            frame_id += 1
            continue
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        curr_hash = imagehash.phash(pil_img)
        if prev_hash is None or (curr_hash - prev_hash) > phash_thresh:
            filename = f"{output_dir}/frame_{frame_id}.jpg"
            cv2.imwrite(filename, frame)
            keyframes.append({
                "path": filename,
                "timestamp": format_timestamp(sec)
            })
            saved += 1
            last_saved_sec = sec
            prev_hash = curr_hash
        frame_id += 1
    cap.release()
    return keyframes
