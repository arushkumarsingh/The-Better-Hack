import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from preprocess.extract_audio import extract_audio
from preprocess.transcribe import transcribe_audio
from preprocess.keyframes import extract_keyframes
from preprocess.keyframe_analysis import summarize_keyframe, consolidate_user_journey
from agent.generate_doc import generate_folder_structure, generate_markdown_skeletons, populate_markdown_files
from agent.generate_persona_doc import extract_personas_usecases, select_lucrative_features

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
REALTIME_SESSIONS = {}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from fastapi.responses import JSONResponse

@app.get("/fetch_api/docs-folders")
def list_docs_folders():
    docs_path = os.path.abspath(OUTPUT_DIR)
    folders = []
    if os.path.exists(docs_path):
        for name in os.listdir(docs_path):
            folder_path = os.path.join(docs_path, name)
            if os.path.isdir(folder_path):
                folders.append({
                    "id": name,
                    "title": name.replace("_", " ").title(),
                    "preview": "/placeholder.svg",
                    "status": "completed",
                    "date": ""
                })
    return JSONResponse(content=folders)

@app.get("/docs-list/{video_id}/{dir_path:path}")
def list_docs_directory(video_id: str, dir_path: str = ""):
    base_dir = os.path.abspath(os.path.join(OUTPUT_DIR, video_id))
    target_dir = os.path.abspath(os.path.join(base_dir, dir_path))
    if not target_dir.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Directory not found")
    def build_tree(path, rel_path=""):
        items = []
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            entry_rel_path = os.path.join(rel_path, entry) if rel_path else entry
            if os.path.isdir(full_path):
                children = build_tree(full_path, entry_rel_path)
                items.append({
                    "name": entry,
                    "path": entry_rel_path,
                    "type": "folder",
                    "children": children
                })
            elif entry.endswith(".md"):
                items.append({
                    "name": entry,
                    "path": entry_rel_path,
                    "type": "file"
                })
        return items
    return JSONResponse(build_tree(target_dir, dir_path))

@app.get("/docs/{video_id}/{file_path:path}")
def get_markdown_file(video_id: str, file_path: str):
    base_dir = os.path.abspath(os.path.join(OUTPUT_DIR, video_id))
    target_file = os.path.abspath(os.path.join(base_dir, file_path))
    if not target_file.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(target_file) or not target_file.endswith(".md"):
        raise HTTPException(status_code=404, detail="Markdown file not found")
    return FileResponse(target_file, media_type="text/markdown")

@app.get("/document/{video_id}/{file_path:path}")
def get_markdown_file_compat(video_id: str, file_path: str):
    base_dir = os.path.abspath(os.path.join(OUTPUT_DIR, video_id))
    target_file = os.path.abspath(os.path.join(base_dir, file_path))
    if not target_file.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(target_file) or not target_file.endswith(".md"):
        raise HTTPException(status_code=404, detail="Markdown file not found")
    return FileResponse(target_file, media_type="text/markdown")

@app.get("/download/{video_id}")
def download_docs_zip(video_id: str):
    import zipfile
    from io import BytesIO
    base_dir = os.path.abspath(os.path.join(OUTPUT_DIR, video_id))
    if not os.path.exists(base_dir):
        raise HTTPException(status_code=404, detail="Documentation folder not found")
    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, base_dir)
                zf.write(abs_path, rel_path)
    mem_zip.seek(0)
    return FileResponse(mem_zip, filename=f"docs_{video_id}.zip", media_type="application/zip")

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

from fastapi import Request
from typing import Dict

@app.post("/realtime-upload/start")
def realtime_upload_start():
    """
    Starts a new real-time upload session. Returns a session_id.
    """
    import uuid
    session_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"realtime_{session_id}.webm")
    f = open(video_path, "wb")
    REALTIME_SESSIONS[session_id] = {"file": f, "video_path": video_path}
    STATUS[session_id] = "recording"
    return {"session_id": session_id}

@app.post("/realtime-upload/chunk/{session_id}")
async def realtime_upload_chunk(session_id: str, request: Request):
    """
    Receives a video chunk and appends it to the session file.
    """
    if session_id not in REALTIME_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    f = REALTIME_SESSIONS[session_id]["file"]
    chunk = await request.body()
    f.write(chunk)
    f.flush()
    return {"status": "chunk received"}

@app.post("/realtime-upload/finish/{session_id}")
def realtime_upload_finish(session_id: str):
    """
    Finishes the real-time upload, closes the file, and starts processing.
    """
    if session_id not in REALTIME_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    f = REALTIME_SESSIONS[session_id]["file"]
    video_path = REALTIME_SESSIONS[session_id]["video_path"]
    f.close()
    del REALTIME_SESSIONS[session_id]
    # Start normal processing in background
    from fastapi import BackgroundTasks
    background_tasks = BackgroundTasks()
    background_tasks.add_task(process_video, session_id, video_path)
    STATUS[session_id] = "processing"
    return {"status": "processing started", "video_id": session_id}

@app.post("/persona-analysis/{video_id}")
def persona_analysis(video_id: str, persona: str = None):
    """
    Analyze applications, use cases, and personas for a given video. Optionally, if a persona is provided, select the most lucrative features for that persona.
    """
    # Load transcript
    audio_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(video_id+"_")]
    if not audio_files:
        raise HTTPException(status_code=404, detail="Video not found")
    video_path = os.path.join(UPLOAD_DIR, audio_files[0])
    audio_path = None
    for ext in [".wav", ".mp3", ".m4a"]:
        candidate = os.path.splitext(video_path)[0] + ext
        if os.path.exists(candidate):
            audio_path = candidate
            break
    if not audio_path:
        audio_path = None
    # Use transcript from process_video output if available
    transcript_file = os.path.join(OUTPUT_DIR, video_id, "transcript.txt")
    if os.path.exists(transcript_file):
        with open(transcript_file) as f:
            transcript = f.read()
    else:
        from preprocess.transcribe import transcribe_audio
        transcript = transcribe_audio(audio_path) if audio_path else ""
    # Load keyframe summaries
    keyframes_json = os.path.join(OUTPUT_DIR, video_id, "keyframe_summaries.json")
    if os.path.exists(keyframes_json):
        with open(keyframes_json) as f:
            keyframe_summaries = f.read()
    else:
        from preprocess.keyframes import extract_keyframes
        from preprocess.keyframe_analysis import summarize_keyframe
        keyframes = extract_keyframes(video_path)
        keyframe_summaries_list = []
        prev_context = None
        for kf in keyframes:
            summary = summarize_keyframe(kf['path'], kf['timestamp'], previous_context=prev_context)
            keyframe_summaries_list.append(summary)
            prev_context = '\n'.join(summary.splitlines()[:2])
        keyframe_summaries = "\n".join(keyframe_summaries_list)
    # Run persona/use-case extraction
    result = extract_personas_usecases(transcript, keyframe_summaries)
    # If a persona is specified, select top features for that persona
    if persona:
        persona_obj = None
        for p in result.get("personas", []):
            if p["name"].lower() == persona.lower():
                persona_obj = p
                break
        if not persona_obj:
            return {"error": f"Persona '{persona}' not found. Available: {[p['name'] for p in result.get('personas',[])]}"}
        top_features = select_lucrative_features(transcript, keyframe_summaries, persona_obj)
        result["top_features_for_persona"] = top_features
    return result

@app.get("/status/{video_id}")
def get_status(video_id: str):
    return {"status": STATUS.get(video_id, "not_found")}
