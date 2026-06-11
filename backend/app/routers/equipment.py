from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["equipment"])

LIFECYCLE_STAGES = ["DR", "FABRICATION", "SETUP", "INSTALL_PARAM", "PM", "BM", "MODIFY", "SCRAP"]


# ── 설비 모델 ──
@router.get("/models", response_model=list[schemas.EquipmentModelOut])
def list_models(db: Session = Depends(get_db)):
    return db.query(models.EquipmentModel).all()


@router.post("/models", response_model=schemas.EquipmentModelOut)
def create_model(body: schemas.EquipmentModelIn, db: Session = Depends(get_db)):
    m = models.EquipmentModel(**body.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


# ── 설비 ──
@router.get("/equipments", response_model=list[schemas.EquipmentOut])
def list_equipments(site_id: int | None = None, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Equipment)
    if site_id:
        q = q.filter(models.Equipment.site_id == site_id)
    if status:
        q = q.filter(models.Equipment.status == status)
    return q.all()


@router.post("/equipments", response_model=schemas.EquipmentOut)
def create_equipment(body: schemas.EquipmentIn, db: Session = Depends(get_db)):
    eq = models.Equipment(**body.model_dump())
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


@router.get("/equipments/{eq_id}", response_model=schemas.EquipmentOut)
def get_equipment(eq_id: int, db: Session = Depends(get_db)):
    eq = db.get(models.Equipment, eq_id)
    if not eq:
        raise HTTPException(404, "equipment not found")
    return eq


@router.patch("/equipments/{eq_id}/status", response_model=schemas.EquipmentOut)
def update_status(eq_id: int, status: str, db: Session = Depends(get_db)):
    eq = db.get(models.Equipment, eq_id)
    if not eq:
        raise HTTPException(404, "equipment not found")
    eq.status = status
    db.commit()
    db.refresh(eq)
    return eq


# ── 생애주기 이력 ──
@router.get("/equipments/{eq_id}/lifecycle", response_model=list[schemas.LifecycleEventOut])
def lifecycle(eq_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.LifecycleEvent)
        .filter(models.LifecycleEvent.equipment_id == eq_id)
        .order_by(models.LifecycleEvent.event_date, models.LifecycleEvent.id)
        .all()
    )


@router.post("/lifecycle", response_model=schemas.LifecycleEventOut)
def add_lifecycle(body: schemas.LifecycleEventIn, db: Session = Depends(get_db)):
    if body.stage not in LIFECYCLE_STAGES:
        raise HTTPException(400, f"stage must be one of {LIFECYCLE_STAGES}")
    data = body.model_dump()
    if data.get("event_date") is None:
        data.pop("event_date")
    ev = models.LifecycleEvent(**data)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


# ── Install Parameter (버전 이력) ──
@router.get("/equipments/{eq_id}/parameters", response_model=list[schemas.InstallParameterOut])
def parameters(eq_id: int, all_versions: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.InstallParameter).filter(models.InstallParameter.equipment_id == eq_id)
    if not all_versions:
        q = q.filter(models.InstallParameter.is_current.is_(True))
    return q.order_by(models.InstallParameter.name, models.InstallParameter.version).all()


@router.post("/parameters", response_model=schemas.InstallParameterOut)
def set_parameter(body: schemas.InstallParameterIn, db: Session = Depends(get_db)):
    prev = (
        db.query(models.InstallParameter)
        .filter(
            models.InstallParameter.equipment_id == body.equipment_id,
            models.InstallParameter.name == body.name,
            models.InstallParameter.is_current.is_(True),
        )
        .first()
    )
    version = 1
    if prev:
        prev.is_current = False
        version = prev.version + 1
    p = models.InstallParameter(**body.model_dump(), version=version)
    db.add(p)
    db.add(models.LifecycleEvent(
        equipment_id=body.equipment_id, stage="INSTALL_PARAM",
        title=f"파라미터 설정: {body.name} = {body.value}{body.unit} (v{version})",
        performed_by=body.set_by, detail=body.note,
    ))
    db.commit()
    db.refresh(p)
    return p
