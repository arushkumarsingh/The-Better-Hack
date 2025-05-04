import cv2
import numpy as np
import sounddevice as sd
import threading
import queue
import time
import imageio
import subprocess

# For camera overlay

def record_screen_with_audio_and_camera(output_path="output_recording.mp4", duration=30, fps=20, camera_pos=(0.02, 0.75), camera_size=0.2):
    """
    Records the screen and system audio, overlays webcam in a circle at the bottom left, and saves as mp4.
    - output_path: where to save the final mp4
    - duration: seconds to record
    - fps: frames per second
    - camera_pos: (x, y) relative position of camera overlay (bottom left default)
    - camera_size: relative diameter of camera overlay
    """
    import mss
    import sounddevice as sd
    import soundfile as sf
    import tempfile
    import os

    # Screen capture setup
    sct = mss.mss()
    monitor = sct.monitors[1]
    screen_width, screen_height = monitor["width"], monitor["height"]

    # Camera setup
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    # Audio setup
    audio_q = queue.Queue()
    samplerate = 44100
    channels = 2
    audio_file = tempfile.mktemp(suffix=".wav")

    def audio_callback(indata, frames, time, status):
        audio_q.put(indata.copy())

    audio_stream = sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback)

    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_file = tempfile.mktemp(suffix=".mp4")
    out = cv2.VideoWriter(video_file, fourcc, fps, (screen_width, screen_height))

    # Start audio
    audio_stream.start()
    audio_frames = []

    start_time = time.time()
    frame_count = 0
    try:
        while time.time() - start_time < duration:
            # Screen frame
            img = np.array(sct.grab(monitor))[:, :, :3]
            # Camera frame
            ret, cam_frame = cam.read()
            if ret:
                # Make camera frame circular
                mask = np.zeros(cam_frame.shape[:2], dtype=np.uint8)
                center = (cam_frame.shape[1] // 2, cam_frame.shape[0] // 2)
                radius = min(center) - 2
                cv2.circle(mask, center, radius, 255, -1)
                cam_circ = cv2.bitwise_and(cam_frame, cam_frame, mask=mask)
                # Resize
                cam_diam = int(min(screen_width, screen_height) * camera_size)
                cam_circ = cv2.resize(cam_circ, (cam_diam, cam_diam))
                # Overlay
                x = int(screen_width * camera_pos[0])
                y = int(screen_height * camera_pos[1])
                roi = img[y:y+cam_diam, x:x+cam_diam]
                # Alpha blend circle
                gray_mask = cv2.resize(mask, (cam_diam, cam_diam))
                for c in range(3):
                    roi[..., c] = np.where(gray_mask == 255, cam_circ[..., c], roi[..., c])
                img[y:y+cam_diam, x:x+cam_diam] = roi
            # Write video
            out.write(img)
            frame_count += 1
            # Collect audio
            while not audio_q.empty():
                audio_frames.append(audio_q.get())
            # Sleep to maintain FPS
            time.sleep(max(0, 1/fps - (time.time() - start_time - frame_count/fps)))
    finally:
        audio_stream.stop()
        cam.release()
        out.release()
        sct.close()

    # Save audio
    audio_np = np.concatenate(audio_frames, axis=0)
    sf.write(audio_file, audio_np, samplerate)

    # Combine video and audio with ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-strict", "experimental",
        output_path
    ]
    subprocess.run(cmd, check=True)
    # Cleanup temp files
    os.remove(video_file)
    os.remove(audio_file)
    print(f"Screen recording saved to {output_path}")

if __name__ == "__main__":
    record_screen_with_audio_and_camera("output_recording.mp4", duration=15)
