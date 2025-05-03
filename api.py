import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from preprocess.extract_audio import extract_audio
from preprocess.transcribe import transcribe_audio
from preprocess.keyframes import extract_keyframes
from agent.generate_doc import generate_markdown

app = FastAPI()
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
STATUS = {}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_video(video_id: str, video_path: str):
    try:
        STATUS[video_id] = "extracting_audio"
        audio_path = extract_audio(video_path)

        STATUS[video_id] = "transcribing"
        transcript = transcribe_audio(audio_path)

        STATUS[video_id] = "extracting_keyframes"
        extract_keyframes(video_path, threshold=25)

        STATUS[video_id] = "generating_documentation"
        keyframe_text = "Screenshots from key parts of the demo have been extracted."
        markdown = generate_markdown(transcript, keyframe_text)

        doc_path = os.path.join(OUTPUT_DIR, f"{video_id}.md")
        with open(doc_path, "w") as f:
            f.write(markdown)
        STATUS[video_id] = "done"
    except Exception as e:
        STATUS[video_id] = f"error: {str(e)}"

@app.post("/upload")
def upload_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    STATUS[video_id] = "uploaded"
    return {"video_id": video_id, "filename": file.filename}

@app.post("/process/{video_id}")
def process_endpoint(video_id: str, background_tasks: BackgroundTasks):
    video_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(video_id+"_")]
    if not video_files:
        raise HTTPException(status_code=404, detail="Video not found")
    video_path = os.path.join(UPLOAD_DIR, video_files[0])
    background_tasks.add_task(process_video, video_id, video_path)
    STATUS[video_id] = "processing"
    return {"status": "processing started"}

@app.get("/download/{video_id}")
def download_doc(video_id: str):
    doc_path = os.path.join(OUTPUT_DIR, f"{video_id}.md")
    if not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Documentation not found")
    return FileResponse(doc_path, filename=f"{video_id}.md")

@app.get("/status/{video_id}")
def get_status(video_id: str):
    return {"status": STATUS.get(video_id, "not_found")}
