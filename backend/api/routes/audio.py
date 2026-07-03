from fastapi import APIRouter, UploadFile, HTTPException
from core.audio.transcriber import transcribe_wav

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/transcribe")
async def transcribe(file: UploadFile):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio file")
    try:
        text = transcribe_wav(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"text": text}
