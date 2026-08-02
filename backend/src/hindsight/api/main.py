from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hindsight.api.investigations import router as investigations_router
from hindsight.config import settings

app = FastAPI(title="Hindsight", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
