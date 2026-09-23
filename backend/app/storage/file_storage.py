from pathlib import Path
from fastapi import UploadFile
from backend.app.config import DATA_DIR
from backend.log.logger import Logger
import shutil

UPLOAD_ROOT = DATA_DIR / "uploads"
logger = Logger()

def save_upload(tenant_id: str, agent_id: str, uploaded_file: UploadFile):
    file_name = Path(uploaded_file.filename).name
    
    target_dir = UPLOAD_ROOT / tenant_id / agent_id
    target_dir.mkdir(parents = True, exist_ok = True) 
    logger.log(f"created directory {target_dir}", "INFO")
    
    file_path = (target_dir / file_name).resolve()
    
    with open(file_path, "wb") as out:
        out.write(uploaded_file.file.read())
    
    return str

def delete_agent_files(tenant_id: str, agent_id: str):
    agent_dir = Path(UPLOAD_ROOT / tenant_id / agent_id)
    if agent_dir.exists():
        shutil.rmtree(agent_dir)
