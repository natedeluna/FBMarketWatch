import subprocess
import time
import logging
import random
import datetime
from datetime import datetime
import uvicorn
import requests
import asyncio
from fastapi import HTTPException, FastAPI, WebSocket
import pytz
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from termcolor import colored

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

scraping_process = None
should_terminate = False

@app.get("/")
def root():
    return FileResponse('home.html')

active_websockets = set()

async def send_to_all(message: str):
    for websocket in list(active_websockets):
        await websocket.send_text(message)

def run_scraping_process():
    global should_terminate
    while not should_terminate:
        start_time = time.time()
        venv_python = '/Users/samrussell/Scraper/facebook-marketplace-scraper/venv/bin/python'
        try:
            process = subprocess.run([venv_python, 'app.py'], check=True)
            end_time = time.time()

            dur = end_time - start_time
            minutes, seconds = divmod(dur, 60)
            
            message = f"Completed scrape in {int(minutes)} minutes and {int(seconds)} seconds."
        except subprocess.CalledProcessError as e:
            end_time = time.time()
            dur = end_time - start_time
            minutes, seconds = divmod(dur, 60)
            message = f"Process errored with return code {e.returncode}. Duration: {int(minutes)} minutes and {int(seconds)} seconds."
        
        asyncio.run(send_to_all(message))
        if should_terminate:
            asyncio.run(send_to_all("ensure_ui_update"))
            

    should_terminate = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Keep connection open
            # You can also process incoming messages here
    except Exception as e:
        # Handle exceptions, which occur when the client disconnects
        pass
    finally:
        active_websockets.remove(websocket)

@app.get("/start")
def start_main():
    global scraping_process, should_terminate
    try:
        if scraping_process is None or not scraping_process.is_alive():
            from threading import Thread
            should_terminate = False
            scraping_process = Thread(target=run_scraping_process)
            scraping_process.start()
            
            return JSONResponse(status_code=202, content={"status": "ok", "message": "Scraping started"})
        else:
            raise HTTPException(status_code=409, detail="Scraping is already running")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start the scraping process: {str(e)}")
        
@app.get("/status")
def get_status():
    global should_terminate
    if scraping_process and scraping_process.is_alive() and should_terminate == False:
        content = {"status": "active"}
    elif scraping_process and scraping_process.is_alive() and should_terminate == True:
        content = {"status": "terminating"}
    else:
        content = {"status": "inactive"}
    
    return JSONResponse(status_code=200, content=content)

@app.get("/terminate")
def terminate_main():
    global scraping_process, should_terminate
    try:
        if scraping_process and scraping_process.is_alive():
            should_terminate = True
            scraping_process.join()
            scraping_process = None
            return JSONResponse(status_code=200, content={"status": "ok", "message": "Scraping terminated"})
        else:
            raise HTTPException(status_code=409, detail="Scraping is already stopped")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop the scraping process: {str(e)}")
        
if __name__ == "__main__":
    print(colored('Starting api server','cyan'))
    uvicorn.run(
        'entry:app',
        host='0.0.0.0',
        port=4000,
        reload=True,
    )
