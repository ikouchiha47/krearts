from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from cinema.server.controllers import router as book_router, jobs_router, workflows_router


app = FastAPI(title="Cinema Book Workflow API")

# CORS configuration: for now allow all origins so local web UIs can call
# the API without additional setup. In production you may want to restrict
# this via environment-driven configuration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the book workflow routes, job status routes, and workflows list
app.include_router(book_router)
app.include_router(jobs_router)
app.include_router(workflows_router)

# Static file serving for assets (images, characters, pages)
# Only enabled if SERVE_ASSETS_LOCALLY=true (for local dev without CDN)
if os.getenv("SERVE_ASSETS_LOCALLY", "true").lower() == "true":
    asset_base_path = os.getenv("ASSET_BASE_PATH", "./output")
    asset_dir = Path(asset_base_path).resolve()
    
    if asset_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(asset_dir)),
            name="assets"
        )
        print(f"📁 Serving assets from: {asset_dir} at /assets")
    else:
        print(f"⚠️  Asset directory not found: {asset_dir}")
