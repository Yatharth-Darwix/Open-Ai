from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from monitor import OpenAIMonitor
import os

app = FastAPI(title="OpenAI Credit Monitor")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

monitor = OpenAIMonitor()

# Scheduler
scheduler = BackgroundScheduler()
# Run the check every 2 minutes
scheduler.add_job(monitor.check_and_alert, 'interval', minutes=2)
scheduler.start()

class DepositRequest(BaseModel):
    amount: float

@app.get("/api/status")
def get_status():
    status = monitor.get_balance()
    # Include the configured threshold in the response
    status["threshold"] = monitor.threshold
    return status

@app.post("/api/deposit")
def add_deposit(deposit: DepositRequest):
    return monitor.add_deposit(deposit.amount)

@app.post("/api/sync")
def sync_balance(sync_request: DepositRequest):
    return monitor.sync_balance(sync_request.amount)

@app.post("/api/check-now")
def check_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(monitor.check_and_alert)
    return {"message": "Check triggered"}

# Serve Frontend (Production Mode)
# We assume the frontend build is in ../frontend/build
frontend_build_path = os.path.join(os.path.dirname(__file__), "../frontend/build")
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")
else:
    print("Frontend build not found. Running in API-only mode.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
