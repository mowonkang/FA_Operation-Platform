from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..workflow_templates import TEMPLATES

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/templates")
def templates():
    return [
        {"wf_type": k, "label": v["label"], "description": v["description"],
         "step_count": len(v["steps"]),
         "steps": [{"name": s["name"], "guide": s["guide"], "link": s.get("link")} for s in v["steps"]]}
        for k, v in TEMPLATES.items()
    ]


@router.get("", response_model=list[schemas.WorkflowOut])
def list_workflows(wf_type: str | None = None, status: str | None = None,
                   equipment_id: int | None = None, site_id: int | None = None,
                   db: Session = Depends(get_db)):
    q = db.query(models.Workflow)
    if site_id:
        from sqlalchemy import or_
        q = q.outerjoin(models.Equipment, models.Workflow.equipment_id == models.Equipment.id)\
             .filter(or_(models.Equipment.site_id == site_id,
                         models.Workflow.equipment_id.is_(None)))
    if wf_type:
        q = q.filter(models.Workflow.wf_type == wf_type)
    if status:
        q = q.filter(models.Workflow.status == status)
    if equipment_id:
        q = q.filter(models.Workflow.equipment_id == equipment_id)
    return q.order_by(models.Workflow.created_at.desc()).all()


@router.post("", response_model=schemas.WorkflowDetailOut)
def create_workflow(body: schemas.WorkflowCreateIn, db: Session = Depends(get_db)):
    tpl = TEMPLATES.get(body.wf_type)
    if not tpl:
        raise HTTPException(400, f"wf_type must be one of {list(TEMPLATES)}")
    wf = models.Workflow(**body.model_dump())
    db.add(wf)
    db.flush()
    for i, s in enumerate(tpl["steps"], start=1):
        db.add(models.WorkflowStep(workflow_id=wf.id, seq=i, name=s["name"],
                                   guide=s["guide"], link=s.get("link")))
    if wf.equipment_id:
        stage = {"DR": "DR", "SETUP_STAB": "SETUP", "BM_FLOW": "BM", "PM_FLOW": "PM",
                 "CONTROL_CHANGE": "MODIFY"}.get(body.wf_type, "MODIFY")
        db.add(models.LifecycleEvent(
            equipment_id=wf.equipment_id, stage=stage,
            title=f"워크플로우 시작: [{tpl['label']}] {body.title}",
            performed_by=body.created_by,
        ))
    db.commit()
    db.refresh(wf)
    return wf


@router.get("/dr-pack")
def dr_pack(model_id: int, db: Session = Depends(get_db)):
    """Design Review 데이터팩 — 해당 모델의 운영 이력 전체를 DR 근거자료로 집계.

    BM 원인 통계, PM NG 항목, FDC 알람 통계, L&L, 지식 DB, 파라미터 변경 빈도를 모은다.
    """
    model = db.get(models.EquipmentModel, model_id)
    if not model:
        raise HTTPException(404, "model not found")
    eq_ids = [e.id for e in db.query(models.Equipment).filter(models.Equipment.model_id == model_id).all()]

    bms = db.query(models.BMReport).filter(models.BMReport.equipment_id.in_(eq_ids)).all() if eq_ids else []
    bm_by_cause: dict[str, dict] = {}
    for b in bms:
        key = b.cause or "(원인 미기재)"
        agg = bm_by_cause.setdefault(key, {"count": 0, "downtime_min": 0.0})
        agg["count"] += 1
        agg["downtime_min"] += b.downtime_min
    bm_top = sorted(
        [{"cause": k, **v} for k, v in bm_by_cause.items()],
        key=lambda x: (x["count"], x["downtime_min"]), reverse=True)[:10]

    ng_rows = (
        db.query(models.PMStandardItem.name, models.PMResult.judgment,
                 func.count(models.PMResult.id))
        .join(models.PMResult, models.PMResult.standard_item_id == models.PMStandardItem.id)
        .filter(models.PMStandardItem.model_id == model_id,
                models.PMResult.judgment.in_(["NG", "CHECK"]))
        .group_by(models.PMStandardItem.name, models.PMResult.judgment)
        .all()
    )
    pm_ng = [{"item": n, "judgment": j, "count": c} for n, j, c in ng_rows]

    alarm_rows = []
    if eq_ids:
        alarm_rows = (
            db.query(models.FDCSensor.name, models.FDCAlarm.classification,
                     func.count(models.FDCAlarm.id))
            .join(models.FDCAlarm, models.FDCAlarm.sensor_id == models.FDCSensor.id)
            .filter(models.FDCSensor.equipment_id.in_(eq_ids))
            .group_by(models.FDCSensor.name, models.FDCAlarm.classification)
            .all()
        )
    fdc_stats = [{"sensor": s, "classification": c, "count": n} for s, c, n in alarm_rows]

    lessons = (
        db.query(models.Lesson)
        .filter((models.Lesson.model_id == model_id) | (models.Lesson.model_id.is_(None)))
        .order_by(models.Lesson.created_at.desc()).all()
    )
    lessons_out = [{
        "id": l.id, "title": l.title, "category": l.category,
        "countermeasure": l.countermeasure, "std_reflected": l.std_reflected,
    } for l in lessons]

    cat_map = {"STK": "STK", "OHT": "PORT_OHT", "AGV": "AGV_AMR", "AMR": "AGV_AMR",
               "CNV": "CNV", "LIFTER": "LIFT", "LIFT": "LIFT", "PORT": "PORT_OHT",
               "ROBOT": "ROBOT", "RTV": "AGV_AMR"}
    kn_cat = cat_map.get(model.category, "COMMON")
    knowledge = (
        db.query(models.KnowledgeArticle)
        .filter(models.KnowledgeArticle.category.in_([kn_cat, "COMMON"]))
        .all()
    )
    knowledge_out = [{"id": a.id, "category": a.category, "title": a.title, "summary": a.summary}
                     for a in knowledge]

    param_changes = 0
    if eq_ids:
        param_changes = (
            db.query(func.count(models.InstallParameter.id))
            .filter(models.InstallParameter.equipment_id.in_(eq_ids),
                    models.InstallParameter.version > 1)
            .scalar() or 0
        )
    total_downtime = sum(b.downtime_min for b in bms)

    return {
        "model": {"id": model.id, "code": model.code, "name": model.name, "category": model.category},
        "equipment_count": len(eq_ids),
        "bm_summary": {"total": len(bms), "total_downtime_min": total_downtime, "top_causes": bm_top},
        "pm_ng_items": pm_ng,
        "fdc_alarm_stats": fdc_stats,
        "lessons": lessons_out,
        "unreflected_lessons": [l for l in lessons_out if not l["std_reflected"]],
        "param_change_versions": param_changes,
        "knowledge": knowledge_out,
        "guide": (
            "DR 체크: ① BM Top 원인이 설계 개선으로 해소되는가 ② 미반영 L&L 이 신규 설계에 반영됐는가 "
            "③ PM NG 빈발 항목의 부품 내구/접근성 개선 ④ FDC 알람 빈발 센서부의 설계 마진 ⑤ 파라미터 "
            "변경이 잦았던 항목의 기본값 재설정"
        ),
    }


@router.get("/{wf_id}", response_model=schemas.WorkflowDetailOut)
def get_workflow(wf_id: int, db: Session = Depends(get_db)):
    wf = db.get(models.Workflow, wf_id)
    if not wf:
        raise HTTPException(404, "workflow not found")
    return wf


@router.patch("/steps/{step_id}", response_model=schemas.WorkflowStepOut)
def update_step(step_id: int, body: schemas.WorkflowStepUpdate, db: Session = Depends(get_db)):
    step = db.get(models.WorkflowStep, step_id)
    if not step:
        raise HTTPException(404, "step not found")
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(step, k, v)
    if data.get("status") == "DONE" and not step.done_at:
        step.done_at = datetime.utcnow()
    db.commit()
    db.refresh(step)
    return step


@router.post("/{wf_id}/close", response_model=schemas.WorkflowDetailOut)
def close_workflow(wf_id: int, body: schemas.WorkflowCloseIn, db: Session = Depends(get_db)):
    wf = db.get(models.Workflow, wf_id)
    if not wf:
        raise HTTPException(404, "workflow not found")
    open_steps = [s for s in wf.steps if s.status in ("PENDING", "IN_PROGRESS")]
    if open_steps:
        raise HTTPException(400, f"미완료 단계 {len(open_steps)}건 — 모든 단계를 DONE/NG/SKIP 처리 후 종료하세요")
    wf.status = "DONE"
    wf.closed_at = datetime.utcnow()
    wf.result_note = body.result_note
    if body.create_lesson:
        if not body.origin_site_id:
            raise HTTPException(400, "L&L 생성에는 origin_site_id 가 필요합니다")
        from .lessons import create_lesson_with_deployments
        lesson = create_lesson_with_deployments(
            db,
            title=body.lesson_title or f"[{wf.wf_type}] {wf.title}",
            category=body.lesson_category, model_id=wf.model_id,
            problem=wf.title, countermeasure=body.result_note,
            origin_site_id=body.origin_site_id, created_by=wf.created_by,
        )
        wf.lesson_id = lesson.id
    if wf.equipment_id:
        db.add(models.LifecycleEvent(
            equipment_id=wf.equipment_id, stage="MODIFY",
            title=f"워크플로우 완료: {wf.title}", detail=body.result_note,
        ))
    db.commit()
    db.refresh(wf)
    return wf
