from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.vision import judge

router = APIRouter(prefix="/pm", tags=["pm"])


# ── 표준 점검항목 ──
@router.get("/standards", response_model=list[schemas.PMStandardItemOut])
def list_standards(model_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.PMStandardItem)
    if model_id:
        q = q.filter(models.PMStandardItem.model_id == model_id)
    return q.order_by(models.PMStandardItem.model_id, models.PMStandardItem.item_no).all()


@router.post("/standards", response_model=schemas.PMStandardItemOut)
def create_standard(body: schemas.PMStandardItemIn, db: Session = Depends(get_db)):
    item = models.PMStandardItem(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/standards/{item_id}", response_model=schemas.PMStandardItemOut)
def update_standard(item_id: int, body: schemas.PMStandardItemIn, db: Session = Depends(get_db)):
    item = db.get(models.PMStandardItem, item_id)
    if not item:
        raise HTTPException(404, "standard item not found")
    for k, v in body.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


# ── PM 오더 ──
@router.get("/orders", response_model=list[schemas.PMOrderOut])
def list_orders(status: str | None = None, equipment_id: int | None = None, db: Session = Depends(get_db)):
    # 기한 경과 오더 자동 OVERDUE 처리
    db.query(models.PMOrder).filter(
        models.PMOrder.status == "PLANNED", models.PMOrder.plan_date < date.today()
    ).update({"status": "OVERDUE"})
    db.commit()
    q = db.query(models.PMOrder)
    if status:
        q = q.filter(models.PMOrder.status == status)
    if equipment_id:
        q = q.filter(models.PMOrder.equipment_id == equipment_id)
    return q.order_by(models.PMOrder.plan_date).all()


@router.post("/orders", response_model=schemas.PMOrderOut)
def create_order(body: schemas.PMOrderIn, db: Session = Depends(get_db)):
    o = models.PMOrder(**body.model_dump())
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.get("/orders/{order_id}", response_model=schemas.PMOrderDetailOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.get(models.PMOrder, order_id)
    if not o:
        raise HTTPException(404, "order not found")
    return o


@router.post("/orders/{order_id}/complete", response_model=schemas.PMOrderDetailOut)
def complete_order(order_id: int, body: schemas.PMCompleteIn, db: Session = Depends(get_db)):
    o = db.get(models.PMOrder, order_id)
    if not o:
        raise HTTPException(404, "order not found")
    for r in body.results:
        std = db.get(models.PMStandardItem, r.standard_item_id)
        if not std:
            raise HTTPException(400, f"standard item {r.standard_item_id} not found")
        judgment = r.judgment or judge(r.measured_value, std.lower_limit, std.upper_limit)
        db.add(models.PMResult(
            order_id=o.id, standard_item_id=r.standard_item_id,
            measured_value=r.measured_value, judgment=judgment,
            method_used=r.method_used, vision_inspection_id=r.vision_inspection_id,
            note=r.note,
        ))
    o.status = "DONE"
    o.performed_date = body.performed_date or date.today()
    o.performer = body.performer
    db.add(models.LifecycleEvent(
        equipment_id=o.equipment_id, stage="PM",
        title=f"PM 수행 완료 (오더 #{o.id})", performed_by=body.performer,
        event_date=o.performed_date,
    ))
    db.commit()
    db.refresh(o)
    return o


@router.post("/orders/generate")
def generate_orders(db: Session = Depends(get_db)):
    """모델별 표준항목 최소 주기로, RUN 상태 설비에 차기 PM 오더 자동 생성."""
    created = 0
    for eq in db.query(models.Equipment).filter(models.Equipment.status == "RUN").all():
        stds = db.query(models.PMStandardItem).filter(models.PMStandardItem.model_id == eq.model_id).all()
        if not stds:
            continue
        has_open = (
            db.query(models.PMOrder)
            .filter(models.PMOrder.equipment_id == eq.id,
                    models.PMOrder.status.in_(["PLANNED", "IN_PROGRESS", "OVERDUE"]))
            .first()
        )
        if has_open:
            continue
        min_period = min(s.period_days for s in stds)
        last = (
            db.query(models.PMOrder)
            .filter(models.PMOrder.equipment_id == eq.id, models.PMOrder.status == "DONE")
            .order_by(models.PMOrder.performed_date.desc())
            .first()
        )
        base = last.performed_date if last and last.performed_date else date.today()
        from datetime import timedelta
        plan = base + timedelta(days=min_period)
        db.add(models.PMOrder(equipment_id=eq.id, plan_date=plan,
                              note=f"자동 생성 (최소주기 {min_period}일)"))
        created += 1
    db.commit()
    return {"created": created}
