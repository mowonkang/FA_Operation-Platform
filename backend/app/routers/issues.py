from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/issues", tags=["issues"])

DOMAIN_LABEL = {
    "MECH": "기구", "ELEC": "전장", "CONTROL": "제어", "INTERLOCK": "인터락",
    "CIM": "CIM", "MCS": "MCS", "RTD": "RTD", "SAFETY": "안전", "ETC": "기타",
}


@router.get("/domains")
def domains():
    return [{"code": k, "label": v, "group": "시스템" if k in ("CIM", "MCS", "RTD") else
             ("안전" if k == "SAFETY" else "설비" if k in ("MECH", "ELEC", "CONTROL", "INTERLOCK") else "기타")}
            for k, v in DOMAIN_LABEL.items()]


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Issue.domain, models.Issue.status, func.count(models.Issue.id))
        .group_by(models.Issue.domain, models.Issue.status).all()
    )
    out: dict[str, dict] = {}
    for domain, status, cnt in rows:
        d = out.setdefault(domain, {"domain": domain, "label": DOMAIN_LABEL.get(domain, domain),
                                    "open": 0, "in_progress": 0, "closed": 0})
        key = {"OPEN": "open", "IN_PROGRESS": "in_progress", "CLOSED": "closed"}.get(status, "open")
        d[key] += cnt
    high_open = (
        db.query(func.count(models.Issue.id))
        .filter(models.Issue.severity == "HIGH", models.Issue.status != "CLOSED")
        .scalar() or 0
    )
    return {"by_domain": list(out.values()), "high_open": high_open}


@router.get("", response_model=list[schemas.IssueOut])
def list_issues(domain: str | None = None, status: str | None = None,
                phase: str | None = None, equipment_id: int | None = None,
                site_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Issue)
    if site_id:
        from sqlalchemy import or_
        q = q.outerjoin(models.Equipment).filter(or_(
            models.Equipment.site_id == site_id, models.Issue.equipment_id.is_(None)))
    if domain:
        q = q.filter(models.Issue.domain == domain)
    if status:
        q = q.filter(models.Issue.status == status)
    if phase:
        q = q.filter(models.Issue.phase == phase)
    if equipment_id:
        q = q.filter(models.Issue.equipment_id == equipment_id)
    return q.order_by(models.Issue.created_at.desc()).all()


@router.post("", response_model=schemas.IssueOut)
def create_issue(body: schemas.IssueIn, db: Session = Depends(get_db)):
    data = body.model_dump()
    if data.get("domain") == "SAFETY":
        data["severity"] = "HIGH"  # 안전 이슈는 HIGH 고정
    issue = models.Issue(**data)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.patch("/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: int, body: schemas.IssueUpdate, db: Session = Depends(get_db)):
    issue = db.get(models.Issue, issue_id)
    if not issue:
        raise HTTPException(404, "issue not found")
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(issue, k, v)
    if data.get("status") == "CLOSED" and not issue.closed_at:
        issue.closed_at = datetime.utcnow()
        if issue.equipment_id:
            db.add(models.LifecycleEvent(
                equipment_id=issue.equipment_id, stage="MODIFY",
                title=f"이슈 해결 [{DOMAIN_LABEL.get(issue.domain, issue.domain)}] {issue.title}",
                detail=issue.resolution,
            ))
    db.commit()
    db.refresh(issue)
    return issue
