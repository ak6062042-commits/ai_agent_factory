import datetime
from time import time, perf_counter
from typing import Any, Dict, Optional
from pathlib import Path
from sys import exit
from backend.app.config import WORKSPACE

class Logger:
    def __init__(self, log_file: str = f"{WORKSPACE}/backend/log/log.txt"):
        self.log_path = Path(log_file)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.LEVEL = ["INFO", "ERROR", "DEBUG", "WARNING"]
        self.start = 0
        self.end = 0

    def log(self, message: str, level: str = "INFO"):
        if not level in self.LEVEL:
            print("Incorrect logging level!")
            exit(1)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(file=self.log_path, mode='a', encoding='utf-8') as f:
            f.write(f"[{timestamp}], {level}: {message}.\n")
    
    def read_log(self, level: str = "INFO"):
        with open(file = self.log_path, mode = 'r', encoding = 'utf-8') as f:
            for log in f:
                if level in log:
                    print(log)

    # -------------------- Still in works --------------------
    def start_counter(self):
        self.start = perf_counter()
    
    def end_counter(self):
        self.end = perf_counter()
    
    
    def retrive_counter_value(self):
        retrived_value = self.end - self.start
        self.end = 0
        self.start = 0
        return retrived_value