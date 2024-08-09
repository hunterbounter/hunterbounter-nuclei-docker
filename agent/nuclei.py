import subprocess
import json
import threading
import time
import uuid
from fastapi import FastAPI, HTTPException
from typing import Dict

tasks: Dict[str, Dict] = {}
running_tasks: Dict[str, threading.Thread] = {}


class NucleiScanner:
    def __init__(self):
        global tasks, running_tasks
        self.tasks = tasks
        self.running_tasks = running_tasks

        # ilk kurulum için template kurması için nuclei komutunu calistirip bitmesini bekliyoruz
        self.first_run()
        print("Nuclei scanner initialized")

    def first_run(self):
        print("Updating nuclei templates...")
        result = subprocess.run(
            ['nuclei', '-update-templates'],
            capture_output=True,
            text=True
        )
        print(result.stdout)

    def active_scans_count(self):
        total = 0
        for task_id in self.tasks:
            if self.tasks[task_id]["status"] == "running":
                total += 1

        return total

    def check_nuclei_is_installed(self) -> bool:
        try:
            result = subprocess.run(
                ['which', 'nuclei'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False
            return True
        except Exception as e:
            print(f"Error checking nuclei installation: {e}")
            return False

    def run_nuclei(self, task_id, target):
        result = subprocess.run(
            ['nuclei', '-u', target, '-mhe', '3000', '-json-export', f'{task_id}.json'],
            capture_output=True,
            text=True
        )
        self.tasks[task_id]["results"] = result.stdout
        self.tasks[task_id]["status"] = "completed"

    def start_scan(self, target):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"target": target, "status": "running", "results": ""}

        nuclei_thread = threading.Thread(target=self.run_nuclei, args=(task_id, target))
        self.running_tasks[task_id] = nuclei_thread
        nuclei_thread.start()

        return task_id

    def get_status(self, task_id):
        if task_id in self.tasks:
            return self.tasks[task_id]
        else:
            raise HTTPException(status_code=404, detail="Task not found")

    def get_results(self, task_id):
        # append f72df2f9-aa7f-4cc7-be0f-ff00c55a470e
        if task_id in self.tasks and self.tasks[task_id]["status"] == "completed":
            try:
                with open(f'{task_id}.json', 'r') as file:
                    results = json.load(file)
                    # add every record uuid
                    for record in results:
                        record["task_id"] = str(task_id)
                    # print(results)
                return results
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading results: {e}")
        else:
            raise HTTPException(status_code=404, detail="Results not found or task not completed")

    def get_all_results(self):
        all_results = []
        print("Tasks: ", self.tasks)
        for task_id in self.tasks:
            if self.tasks[task_id]["status"] == "completed":
                try:
                    print(f"Reading results for {task_id}")
                    result = self.get_results(task_id)
                    print(f"Appending results for {task_id}")
                    # Append all results directly to the all_results list
                    all_results.extend(result if isinstance(result, list) else [result])
                except Exception as e:
                    print(f"Error reading results: {e}")
        return all_results
