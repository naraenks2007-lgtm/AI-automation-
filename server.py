import os
import threading
import queue
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from main import run_agent

app = FastAPI(title="Local AI Automation Agent Dashboard")

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

# Global variables for agent state tracking
is_agent_running = False
agent_history = []
log_queue = queue.Queue()
abort_event = threading.Event()
current_thread = None

class RunRequest(BaseModel):
    task: str
    model: str = "qwen2.5:7b"

# Agent step callback
def agent_callback(data):
    global agent_history, log_queue
    step_info = {
        "step": data["step"],
        "thoughts": data["thoughts"],
        "action": data["action"],
        "result": data["result"],
        "timestamp": time.time()
    }
    agent_history.append(step_info)
    log_queue.put(step_info)

def thread_runner(task, model):
    global is_agent_running, abort_event
    try:
        run_agent(task, model_name=model, callback=agent_callback, abort_event=abort_event)
    finally:
        is_agent_running = False
        log_queue.put({"type": "status", "status": "completed"})

@app.post("/api/run")
def api_run(req: RunRequest):
    global is_agent_running, abort_event, current_thread, agent_history, log_queue
    if is_agent_running:
        raise HTTPException(status_code=400, detail="Agent is already running.")
        
    is_agent_running = True
    agent_history = []
    log_queue = queue.Queue()
    abort_event.clear()
    
    # Notify queue that agent has started
    log_queue.put({
        "type": "status", 
        "status": "started", 
        "task": req.task, 
        "model": req.model
    })
    
    current_thread = threading.Thread(target=thread_runner, args=(req.task, req.model), daemon=True)
    current_thread.start()
    return {"status": "started", "task": req.task, "model": req.model}

@app.post("/api/stop")
def api_stop():
    global abort_event, is_agent_running
    if not is_agent_running:
        return {"status": "not_running"}
    abort_event.set()
    return {"status": "stopping"}

@app.get("/api/history")
def api_history():
    return {"history": agent_history, "running": is_agent_running}

@app.get("/api/screenshot")
def api_screenshot():
    screenshot_path = "static/screenshot.png"
    if os.path.exists(screenshot_path):
        # We add aggressive caching headers to make sure the client always pulls the latest image
        return FileResponse(
            screenshot_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    # Default tiny grey PNG placeholder
    import base64
    placeholder_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    from fastapi.responses import Response
    return Response(content=placeholder_png, media_type="image/png")

@app.get("/api/stream")
def api_stream(request: Request):
    """Streams agent steps using Server-Sent Events (SSE)."""
    def event_generator():
        while True:
            try:
                # wait for item in log_queue with timeout to prevent thread blocking
                data = log_queue.get(timeout=2.0)
                import json
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                # send heartbeat comment to keep client connection alive
                yield ": heartbeat\n\n"
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve index.html on root
@app.get("/")
def read_root():
    html_path = "static/index.html"
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("static/index.html not found. Please create the frontend assets.")

# Mount static folder for assets
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    print("Starting FastAPI Local Agent Server on http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
