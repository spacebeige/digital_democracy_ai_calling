import sys

with open('/Users/ashwinagarkhed/integration1/awaaz/api_server.py', 'r') as f:
    orig = f.read()

orig = orig.replace(
    "from fastapi import (\n    FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query\n)", 
    "from fastapi import (\n    FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query, Path\n)"
)

replacements = [
    (
        "async def get_transcription_status(\n    job_id: str = Query(..., description=\"Job ID to check\"),",
        "async def get_transcription_status(\n    job_id: str = Path(..., description=\"Job ID to check\"),"
    ),
    (
        "async def get_ai_processing_status(\n    job_id: str = Query(..., description=\"Job ID to check\"),",
        "async def get_ai_processing_status(\n    job_id: str = Path(..., description=\"Job ID to check\"),"
    ),
    (
        "async def get_tts_status(\n    job_id: str = Query(..., description=\"Job ID to check\"),",
        "async def get_tts_status(\n    job_id: str = Path(..., description=\"Job ID to check\"),"
    ),
    (
        "async def get_pipeline_details(\n    job_id: str = Query(..., description=\"Base job ID (typically transcription job_id)\"),",
        "async def get_pipeline_details(\n    job_id: str = Path(..., description=\"Base job ID (typically transcription job_id)\"),"
    )
]

for s, r in replacements:
    orig = orig.replace(s, r)

with open('/Users/ashwinagarkhed/integration1/awaaz/api_server.py', 'w') as f:
    f.write(orig)

print("Path fixed.")
