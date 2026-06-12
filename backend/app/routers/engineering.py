from fastapi import APIRouter

from .. import schemas
from ..services import engineering as eng

router = APIRouter(prefix="/engineering", tags=["engineering"])


@router.post("/wire-rope-pro")
def wire_rope_pro(body: schemas.WireRopeProIn):
    """전문가용: 가반하중·체결방식 기반 안전율/수명 + 민감도 곡선."""
    return eng.wire_rope_pro(body)


@router.post("/wire-rope")
def wire_rope(body: schemas.WireRopeIn):
    return eng.wire_rope_life(body)


@router.post("/bearing")
def bearing(body: schemas.BearingIn):
    return eng.bearing_life(body)


@router.post("/battery")
def battery(body: schemas.BatteryIn):
    return eng.battery_life(body)


@router.post("/wheel")
def wheel(body: schemas.WheelIn):
    return eng.wheel_life(body)


@router.post("/motor")
def motor(body: schemas.MotorIn):
    """주행/권상 모터 용량 산정 + 속도 민감도 곡선."""
    return eng.motor_capacity(body)


@router.post("/conveyor")
def conveyor(body: schemas.ConveyorIn):
    """벨트 컨베이어 구동 출력 + 반송능력 민감도 곡선."""
    return eng.conveyor_power(body)


@router.post("/chain")
def chain(body: schemas.ChainIn):
    """리프 체인 안전율 + 신율 추세 잔여수명 예측."""
    return eng.chain_life(body)
