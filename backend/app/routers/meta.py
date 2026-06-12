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

    # 주별 BM 트렌드 (최근 8주)
    from datetime import datetime, timedelta
    weekly = []
    now = datetime.utcnow()
    for w in range(7, -1, -1):
        start = now - timedelta(days=7 * (w + 1))
        end = now - timedelta(days=7 * w)
        rows = (
            db.query(func.count(models.BMReport.id),
                     func.coalesce(func.sum(models.BMReport.downtime_min), 0))
            .filter(models.BMReport.occurred_at >= start, models.BMReport.occurred_at < end)
            .one()
        )
        weekly.append({"week": end.strftime("%m/%d"), "bm_count": rows[0],
                       "downtime_min": float(rows[1])})

    # PM 오더 상태 분포 (OVERDUE 는 파생)
    pm_dist = {"DONE": pm_done, "OVERDUE": pm_overdue,
               "PLANNED": max(pm_planned - pm_overdue, 0)}
    pm_dist["IN_PROGRESS"] = (
        db.query(func.count(models.PMOrder.id))
        .filter(models.PMOrder.status == "IN_PROGRESS").scalar() or 0
    )

    # FDC 알람 분류 분포
    alarm_cls = dict(
        db.query(models.FDCAlarm.classification, func.count(models.FDCAlarm.id))
        .group_by(models.FDCAlarm.classification).all()
    )

    return {
        "equipment_total": eq_total,
        "equipment_running": eq_run,
        "availability_pct": round(eq_run / eq_total * 100, 1) if eq_total else 0,
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
        "weekly_bm": weekly,
        "pm_status_dist": pm_dist,
        "alarm_classification_dist": [{"name": k, "count": v} for k, v in alarm_cls.items()],
    }
