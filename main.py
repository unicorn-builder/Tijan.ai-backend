"""
Tijan AI — Backend FastAPI v2
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from typing import Optional
import os, uuid, tempfile

from engine_structural import (
    ProjetStructurel, ParamsGeometrie, ParamsUsage,
    ParamsSol, ParamsLocalisation,
    UsageBatiment, ZoneVent,
    calculer_structure_complete
)
from generate_pdf import generer_pdf, calculer_score_edge

app = FastAPI(title="Tijan AI Engine", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def health():
    return {"status": "online", "service": "Tijan AI Engine v2", "version": "2.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
