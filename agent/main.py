import json
import sys
import threading
import time

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from agent.nuclei import NucleiScanner
from agent.telemetry import get_server_stats, send_telemetry, send_scan_telemetry
scanner = NucleiScanner()
app = FastAPI()


class TargetModel(BaseModel):
    target: str


@app.post("/start_scan/")
def start_scan(target: TargetModel):
    task_id = scanner.start_scan(target.target)
    return {"task_id": task_id}


@app.get("/status/{task_id}")
def get_status(task_id: str):
    status = scanner.get_status(task_id)
    return status


@app.get("/results/{task_id}")
def get_results(task_id: str):
    results = scanner.get_results(task_id)
    return results


def telemetry_thread():
    while True:
        # check is macos
        if sys.platform == 'darwin':
            return
        server_stats = get_server_stats()
        json_stats = json.dumps(server_stats, indent=4)
        send_telemetry(json_stats)
        time.sleep(10)  # 30 Sec interval


def send_scan_results():
    while True:
        nuclei_online = scanner.check_nuclei_is_installed()
        print("Nuclei Online: ", nuclei_online)
        if nuclei_online:
            send_scan_telemetry()
        time.sleep(15)  # 15 Sec interval

if __name__ == "__main__":
    print("init")
    threading.Thread(target=telemetry_thread, daemon=True).start()
    threading.Thread(target=send_scan_results, daemon=True).start()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8011)
