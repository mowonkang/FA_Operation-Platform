from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import (bm, engineering, equipment, fdc, issues, knowledge,
                      lessons, lifecycle_config, meta, parts, pm, quotations,
                      vision, workflows)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FA Operation Platform",
    description="FA 물류설비 생애주기(DR~PM/BM) 운영 플랫폼 — PM 표준화, 비전 측정, "
                "스페어파츠, 엔지니어링 수명검토, FDC, Lesson&Learn 다법인 확산",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API = "/api/v1"
app.include_router(meta.router, prefix=API)
app.include_router(equipment.router, prefix=API)
app.include_router(pm.router, prefix=API)
app.include_router(bm.router, prefix=API)
app.include_router(parts.router, prefix=API)
app.include_router(engineering.router, prefix=API)
app.include_router(fdc.router, prefix=API)
app.include_router(vision.router, prefix=API)
app.include_router(lessons.router, prefix=API)
app.include_router(knowledge.router, prefix=API)
app.include_router(workflows.router, prefix=API)
app.include_router(lifecycle_config.router, prefix=API)
app.include_router(quotations.router, prefix=API)
app.include_router(issues.router, prefix=API)


@app.get("/api/health")
def health():
    return {"status": "ok"}
