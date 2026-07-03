from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import commands, ws

app = FastAPI(title="FL Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(commands.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8001"))
    reload = os.getenv("BACKEND_RELOAD", "true").lower() == "true"
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=reload)
