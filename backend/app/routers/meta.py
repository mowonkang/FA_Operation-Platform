from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["meta"])


@router.get("/sites", response_model=list[schemas.SiteOut])
def list_sites(db: Session = Depends(get_db)):
    return db.query(models.Site).all()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = date.today()
    eq_total = db.query(func.count(models.Equipment.id)).scalar() or 0
    eq_run = db.query(func.count(models.Equipment.id)).filter(models.Equipment.status == "RUN").scalar() or 0
    pm_planned = db.query(func.count(models.PMOrder.id)).filter(models.PMOrder.status == "PLANNED").scalar() or 0
    pm_overdue = (
        db.query(func.count(models.PMOrder.id))
        .filter(models.PMOrder.status.in_(["PLANNED", "IN_PROGRESS"]), models.PMOrder.plan_date < today)
        .scalar() or 0
    )
    pm_done = db.query(func.count(models.PMOrder.id)).filter(models.PMOrder.status == "DONE").scalar() or 0
    bm_open = db.query(func.count(models.BMReport.id)).filter(models.BMReport.status.in_(["OPEN", "ANALYZING"])).scalar() or 0
    bm_total = db.query(func.count(models.BMReport.id)).scalar() or 0
    downtime = db.query(func.coalesce(func.sum(models.BMReport.downtime_min), 0)).scalar() or 0
    alarms_open = db.query(func.count(models.FDCAlarm.id)).filter(models.FDCAlarm.status == "OPEN").scalar() or 0
    parts_short = (
        db.query(func.count(models.Part.id))
        .filter(models.Part.current_stock < models.Part.min_stock)
        .scalar() or 0
    )
    lessons = db.query(func.count(models.Lesson.id)).scalar() or 0
    dep_total = db.query(func.count(models.LessonDeployment.id)).scalar() or 0
    dep_applied = (
        db.query(func.count(models.LessonDeployment.id))
        .filter(models.LessonDeployment.status == "APPLIED")
        .scalar() or 0
    )
    pm_compliance = round(pm_done / (pm_done + pm_overdue) * 100, 1) if (pm_done + pm_overdue) else 100.0

    return {
        "equipment_total": eq_total,
        "equipment_running": eq_run,
        "pm_planned": pm_planned,
        "pm_overdue": pm_overdue,
        "pm_done": pm_done,
        "pm_compliance_pct": pm_compliance,
        "bm_open": bm_open,
        "bm_total": bm_total,
        "total_downtime_min": downtime,
        "fdc_alarms_open": alarms_open,
        "parts_below_min_stock": parts_short,
        "lessons_total": lessons,
        "lesson_apply_rate_pct": round(dep_applied / dep_total * 100, 1) if dep_total else 0.0,
    }
