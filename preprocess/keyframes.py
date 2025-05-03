import cv2
import os

def extract_keyframes(video_path, output_dir="output/keyframes", threshold=30.0):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    prev_frame = None
    frame_id = 0
    saved = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray)
            score = diff.mean()
            if score > threshold:
                filename = f"{output_dir}/frame_{frame_id}.jpg"
                cv2.imwrite(filename, frame)
                saved += 1
        prev_frame = gray
        frame_id += 1

    cap.release()
    return saved
