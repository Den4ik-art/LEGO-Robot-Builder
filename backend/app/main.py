from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes_components import router as components_router
from app.api.routes_config import router as config_router
from app.api.auth.routes_auth import router as auth_router
from app.api.history.routes_history import router as history_router
from app.api.routes_benchmark import router as benchmark_router

app = FastAPI(title="LEGO Configurator API", version="1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    print(f"УВАГА: Папка статики не знайдена: {STATIC_DIR}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Реєстрація всіх маршрутів
app.include_router(components_router)
app.include_router(config_router)
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(benchmark_router, prefix="/benchmark", tags=["Analysis"])

@app.get("/")
def root():
    return {"message": "LEGO Configurator API працює"}