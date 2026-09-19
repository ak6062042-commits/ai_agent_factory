import datetime
from time import time, perf_counter
from typing import Any, Dict, Optional

class Logger:
    def __init__(self, log_file: str = "backend/log/log.txt"):
        self.log_file = log_file
        self.LEVEL = ["INFO", "ERROR", "DEBUG"]
        self.start = 0
        self.end = 0

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}], {level}: {message}.\n")
    
    def start_counter(self):
        self.start = perf_counter()
    
    def end_counter(self):
        self.end = perf_counter()
    
    
    def retrive_counter_value(self):
        retrived_value = self.end - self.start
        self.end = 0
        self.start = 0
        return retrived_value