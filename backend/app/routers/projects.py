"""투자/구축 프로젝트 관리.

생성·수정은 모든 사용자, 삭제는 관리자(X-Role: admin 헤더)만 가능.
※ 현 단계의 역할은 설정창에서 선택하는 데모 권한 — Phase 3 에서 SSO/RBAC 로 대체.
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/projects", tags=["projects"])

STATUS_LABEL = {"PLANNING": "기획", "ONGOING": "진행중", "DONE": "완료", "HOLD": "보류"}


def require_admin(x_role: str = Header(default="user")):
    if x_role != "admin":
        raise HTTPException(403, "관리자만 수행할 수 있습니다 — 설정(⚙)에서 역할을 변경하세요")


@router.get("", response_model=list[schemas.ProjectOut])
def list_projects(site_id: int | None = None, status: str | None = None,
                  db: Session = Depends(get_db)):
    q = db.query(models.Project)
    if site_id:
        q = q.filter(models.Project.site_id == site_id)
    if status:
        q = q.filter(models.Project.status == status)
    return q.order_by(models.Project.created_at.desc()).all()


@router.get("/{project_id}/summary")
def project_summary(project_id: int, db: Session = Depends(get_db)):
    """프로젝트 현황 요약 — 견적(이름 매칭)·예산 대비 선정가."""
    p = db.get(models.Project, project_id)
    if not p:
        raise HTTPException(404, "project not found")
    quotes = db.query(models.Quotation).filter(models.Quotation.project == p.name).all()
    selected = next((q for q in quotes if q.status == "SELECTED"), None)
    return {
        "project": schemas.ProjectOut.model_validate(p).model_dump(),
        "quotation_count": len(quotes),
        "vendors": [q.vendor for q in quotes],
        "selected_vendor": selected.vendor if selected else None,
        "selected_amount": selected.total_amount if selected else None,
        "budget_usage_pct": round(selected.total_amount / p.budget * 100, 1)
        if selected and p.budget else None,
    }


@router.post("", response_model=schemas.ProjectOut)
def create_project(body: schemas.ProjectIn, db: Session = Depends(get_db)):
    if db.query(models.Project).filter(models.Project.code == body.code).first():
        raise HTTPException(400, f"프로젝트 코드 중복: {body.code}")
    p = models.Project(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, body: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    p = db.get(models.Project, project_id)
    if not p:
        raise HTTPException(404, "project not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{project_id}", dependencies=[Depends(require_admin)])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Project, project_id)
    if not p:
        raise HTTPException(404, "project not found")
    db.delete(p)
    db.commit()
    return {"deleted": project_id}
