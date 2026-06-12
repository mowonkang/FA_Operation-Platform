from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/lifecycle-config", tags=["lifecycle-config"])


@router.get("/map")
def lifecycle_map(db: Session = Depends(get_db)):
    """전체 라이프사이클 맵 (비어있으면 기본값 자동 시드 — seed 모듈 공용 함수 사용)."""
    from ..lifecycle_seed import seed_defaults
    seed_defaults(db)
    phases = db.query(models.LifecyclePhase).order_by(models.LifecyclePhase.seq).all()
    return [
        {
            "id": p.id, "code": p.code, "name": p.name, "seq": p.seq,
            "description": p.description,
            "processes": [
                {"id": pr.id, "code": pr.code, "name": pr.name, "seq": pr.seq,
                 "description": pr.description, "module_key": pr.module_key}
                for pr in p.processes
            ],
        }
        for p in phases
    ]


@router.post("/phases")
def create_phase(body: schemas.PhaseIn, db: Session = Depends(get_db)):
    p = models.LifecyclePhase(**body.model_dump())
    db.add(p)
    db.commit()
    return {"id": p.id}


@router.patch("/phases/{phase_id}")
def update_phase(phase_id: int, body: schemas.PhaseUpdate, db: Session = Depends(get_db)):
    p = db.get(models.LifecyclePhase, phase_id)
    if not p:
        raise HTTPException(404, "phase not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/phases/{phase_id}")
def delete_phase(phase_id: int, db: Session = Depends(get_db)):
    p = db.get(models.LifecyclePhase, phase_id)
    if not p:
        raise HTTPException(404, "phase not found")
    db.delete(p)  # processes cascade
    db.commit()
    return {"ok": True}


@router.post("/processes")
def create_process(body: schemas.ProcessIn, db: Session = Depends(get_db)):
    if not db.get(models.LifecyclePhase, body.phase_id):
        raise HTTPException(404, "phase not found")
    pr = models.LifecycleProcess(**body.model_dump())
    db.add(pr)
    db.commit()
    return {"id": pr.id}


@router.patch("/processes/{process_id}")
def update_process(process_id: int, body: schemas.ProcessUpdate, db: Session = Depends(get_db)):
    pr = db.get(models.LifecycleProcess, process_id)
    if not pr:
        raise HTTPException(404, "process not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(pr, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/processes/{process_id}")
def delete_process(process_id: int, db: Session = Depends(get_db)):
    pr = db.get(models.LifecycleProcess, process_id)
    if not pr:
        raise HTTPException(404, "process not found")
    db.delete(pr)
    db.commit()
    return {"ok": True}
