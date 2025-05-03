import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from preprocess.extract_audio import extract_audio
from preprocess.transcribe import transcribe_audio
from preprocess.keyframes import extract_keyframes
from preprocess.keyframe_analysis import summarize_keyframe, consolidate_user_journey
from agent.generate_doc import generate_folder_structure, generate_markdown_skeletons, populate_markdown_files

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output/docs"
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
        keyframes = extract_keyframes(video_path)

        STATUS[video_id] = "analyzing_keyframes"
        keyframe_summaries = []
        prev_context = None
        for kf in keyframes:
            summary = summarize_keyframe(kf['path'], kf['timestamp'], previous_context=prev_context)
            keyframe_summaries.append(summary)
            prev_context = '\n'.join(summary.splitlines()[:2])

        STATUS[video_id] = "consolidating_user_journey"
        user_journey_flow = consolidate_user_journey(keyframe_summaries)

        STATUS[video_id] = "generating_documentation_folder_structure"
        folder_structure = generate_folder_structure(transcript, user_journey_flow)

        STATUS[video_id] = "creating_markdown_skeletons"
        doc_base = os.path.join(OUTPUT_DIR, video_id)
        generate_markdown_skeletons(folder_structure, user_journey_flow, base_path=doc_base)

        STATUS[video_id] = "populating_documentation_files"
        populate_markdown_files(folder_structure, transcript, user_journey_flow, base_path=doc_base)

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
