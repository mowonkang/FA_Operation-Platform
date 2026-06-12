import math
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/fdc", tags=["fdc"])

SPIKE_SIGMA = 4.0       # 직전 구간 평균 대비 표준편차 배수
DRIFT_WINDOW = 20       # 드리프트 판정 최근 표본 수
DRIFT_RATIO = 0.7       # 워닝 한계 대비 평균 접근 비율


def _classify(sensor: models.FDCSensor, value: float, recent_vals: list[float]) -> tuple[str, str] | None:
    """레벨/스파이크/드리프트 룰 기반 Fault Detection & Classification.

    recent_vals 는 호출 측이 유지하는 롤링 윈도우(과거→최신 순) — 배치 인제스트 시
    레코드마다 DB 를 조회하지 않도록 분리했다.
    """
    if sensor.alarm_high is not None and value >= sensor.alarm_high:
        return "ALARM", "LEVEL_HIGH"
    if sensor.alarm_low is not None and value <= sensor.alarm_low:
        return "ALARM", "LEVEL_LOW"
    if sensor.warn_high is not None and value >= sensor.warn_high:
        return "WARN", "LEVEL_HIGH"
    if sensor.warn_low is not None and value <= sensor.warn_low:
        return "WARN", "LEVEL_LOW"

    if len(recent_vals) >= 10:
        mean = sum(recent_vals) / len(recent_vals)
        std = math.sqrt(sum((v - mean) ** 2 for v in recent_vals) / len(recent_vals)) or 1e-9
        if abs(value - mean) > SPIKE_SIGMA * std:
            return "WARN", "SPIKE"
        if sensor.warn_high is not None and mean > sensor.warn_high * DRIFT_RATIO:
            return "WARN", "DRIFT"
    return None


@router.get("/sensors", response_model=list[schemas.FDCSensorOut])
def list_sensors(equipment_id: int | None = None, site_id: int | None = None,
                 db: Session = Depends(get_db)):
    q = db.query(models.FDCSensor)
    if site_id:
        q = q.join(models.Equipment).filter(models.Equipment.site_id == site_id)
    if equipment_id:
        q = q.filter(models.FDCSensor.equipment_id == equipment_id)
    return q.all()


@router.post("/sensors", response_model=schemas.FDCSensorOut)
def create_sensor(body: schemas.FDCSensorIn, db: Session = Depends(get_db)):
    s = models.FDCSensor(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.post("/ingest")
def ingest(body: schemas.FDCIngestIn, db: Session = Depends(get_db)):
    """설비 게이트웨이로부터 측정값 배치 수집 + 실시간 룰 평가.

    센서별로 최근 윈도우를 1회만 조회하고 배치 내에서는 메모리 롤링으로 유지한다.
    """
    by_sensor: dict[int, list] = {}
    for r in body.readings:
        by_sensor.setdefault(r.sensor_id, []).append(r)

    alarms = 0
    for sensor_id, readings in by_sensor.items():
        sensor = db.get(models.FDCSensor, sensor_id)
        if not sensor:
            raise HTTPException(400, f"sensor {sensor_id} not found")
        recent = (
            db.query(models.FDCReading.value)
            .filter(models.FDCReading.sensor_id == sensor_id)
            .order_by(models.FDCReading.ts.desc())
            .limit(DRIFT_WINDOW)
            .all()
        )
        window = [row[0] for row in reversed(recent)]
        for r in sorted(readings, key=lambda x: x.ts or datetime.utcnow()):
            verdict = _classify(sensor, r.value, window)
            db.add(models.FDCReading(sensor_id=sensor_id, value=r.value,
                                     ts=r.ts or datetime.utcnow()))
            window.append(r.value)
            if len(window) > DRIFT_WINDOW:
                window.pop(0)
            if verdict:
                level, cls = verdict
                db.add(models.FDCAlarm(
                    sensor_id=sensor.id, level=level, classification=cls, value=r.value,
                    message=f"{sensor.name} {cls} ({r.value}{sensor.unit})",
                    ts=r.ts or datetime.utcnow(),
                ))
                alarms += 1
    db.commit()
    return {"ingested": len(body.readings), "alarms_raised": alarms}


@router.get("/readings")
def readings(sensor_id: int, limit: int = 200, db: Session = Depends(get_db)):
    rows = (
        db.query(models.FDCReading)
        .filter(models.FDCReading.sensor_id == sensor_id)
        .order_by(models.FDCReading.ts.desc())
        .limit(limit)
        .all()
    )
    return [{"ts": r.ts.isoformat(), "value": r.value} for r in reversed(rows)]


@router.get("/alarms", response_model=list[schemas.FDCAlarmOut])
def alarms(status: str | None = None, site_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.FDCAlarm)
    if site_id:
        q = (q.join(models.FDCSensor, models.FDCAlarm.sensor_id == models.FDCSensor.id)
             .join(models.Equipment).filter(models.Equipment.site_id == site_id))
    if status:
        q = q.filter(models.FDCAlarm.status == status)
    return q.order_by(models.FDCAlarm.ts.desc()).limit(200).all()


@router.patch("/alarms/{alarm_id}")
def update_alarm(alarm_id: int, status: str, db: Session = Depends(get_db)):
    a = db.get(models.FDCAlarm, alarm_id)
    if not a:
        raise HTTPException(404, "alarm not found")
    a.status = status
    db.commit()
    return {"id": a.id, "status": a.status}


@router.post("/alarms/{alarm_id}/to-bm", response_model=schemas.BMReportOut)
def alarm_to_bm(alarm_id: int, db: Session = Depends(get_db)):
    """FDC 알람을 BM 보고로 전환 (알람-정비 연계)."""
    a = db.get(models.FDCAlarm, alarm_id)
    if not a:
        raise HTTPException(404, "alarm not found")
    r = models.BMReport(
        equipment_id=a.sensor.equipment_id,
        symptom=f"[FDC {a.level}] {a.message}",
        fdc_alarm_id=a.id, reported_by="FDC",
    )
    a.status = "ACK"
    db.add(r)
    db.flush()
    db.add(models.LifecycleEvent(
        equipment_id=r.equipment_id, stage="BM",
        title=f"FDC 알람 → BM 전환: {a.message}", performed_by="FDC",
    ))
    db.commit()
    db.refresh(r)
    return r


@router.post("/simulate")
def simulate(sensor_id: int, hours: int = 24, anomaly: bool = True, db: Session = Depends(get_db)):
    """데모/시험용: 시계열 데이터 생성(정상 + 말미 이상 트렌드)."""
    sensor = db.get(models.FDCSensor, sensor_id)
    if not sensor:
        raise HTTPException(404, "sensor not found")
    base = ((sensor.warn_low or 0) + (sensor.warn_high or 100)) / 2
    span = ((sensor.warn_high or 100) - (sensor.warn_low or 0)) / 2
    now = datetime.utcnow()
    n = hours * 6  # 10분 간격
    readings = []
    for i in range(n):
        ts = now - timedelta(minutes=10 * (n - i))
        value = base + random.gauss(0, span * 0.1)
        if anomaly and i > n * 0.85:  # 말미 15% 구간 상승 드리프트
            value += span * 1.5 * (i - n * 0.85) / (n * 0.15)
        readings.append(schemas.FDCIngestReading(sensor_id=sensor_id, value=round(value, 2), ts=ts))
    return ingest(schemas.FDCIngestIn(readings=readings), db)
