from datetime import datetime, timedelta
import random

# -----------------------------
# 설정값
# -----------------------------
STATE_STABLE_TIME = 20  # temp_state 유지 시간 (초)
INITIAL_SEATS = ["A1", "A2", "A3", "B1", "B2", "B3"]
VALID_STATES = ["Empty", "Occupied", "Camped"]

# 정책 설정
POLICY_CONFIG = {
    "camping_minutes": 120,
    "no_show_minutes": 20,
    "return_grace_minutes": 5,
}


# -----------------------------
# 좌석 초기화
# -----------------------------
def init_seats():
    seats = {}

    for seat in INITIAL_SEATS:
        is_reserved = random.choice([True, False])

        seats[seat] = {
            "state": "Empty",
            "last_update": None,

            # 예약 관련
            "reserved": is_reserved,
            "reserved_at": datetime.now() if is_reserved else None,

            # DEADLINE
            "unreserve_deadline": (
                datetime.now() + timedelta(minutes=1) 
                if is_reserved else None
            ),
            "release_remain": None,       # 남은 시간 (초)

            # 정책 엔진 관련
            "ever_occupied": False,
            "authorized": True,

            # 임시상태
            "temp_state": None,
            "temp_started": None,
        }

    return seats


# -----------------------------
# 상태 강제 변경 (수동 버튼)
# -----------------------------
def set_seat_state(seats, seat_id, new_state):
    if seat_id not in seats:
        raise ValueError(f"Unknown seat id: {seat_id}")

    if new_state not in VALID_STATES:
        raise ValueError(f"Invalid state: {new_state}")

    s = seats[seat_id]
    s["state"] = new_state
    s["last_update"] = datetime.now()

    if new_state == "Occupied":
        s["ever_occupied"] = True

    # DEADLINE 재설정
    if new_state == "Empty":
        s["unreserve_deadline"] = datetime.now() + timedelta(minutes=1)
    elif new_state == "Camped":
        s["unreserve_deadline"] = datetime.now() + timedelta(minutes=3)
    else:
        s["unreserve_deadline"] = None


# -----------------------------
# AI 상태 판별
# -----------------------------
def check_status(detections):
    det = set(detections)

    if "person" in det:
        return "Occupied"

    if det & {"backpack", "laptop", "book"}:
        return "Camped"

    return "Empty"


# -----------------------------
# DEADLINE 기반 임시 상태 + 연장 기능
# -----------------------------
def update_seat_state(seat, inferred_state):
    if not seat["reserved"]:
        seat["state"] = "Empty"
        seat["temp_state"] = None
        seat["temp_started"] = None
        seat["unreserve_deadline"] = None
        return "Empty"

    now = datetime.now()
    current = seat["state"]
    temp = seat.get("temp_state")
    temp_started = seat.get("temp_started")

    deadline = seat.get("unreserve_deadline")

    # -----------------------------
    # 1) 상태 동일 → temp 초기화
    # -----------------------------
    if inferred_state == current:
        seat["temp_state"] = None
        seat["temp_started"] = None
        return current, None, None

    # -----------------------------
    # 2) 새로운 temp_state 시작
    # -----------------------------
    if temp is None:
        seat["temp_state"] = inferred_state
        seat["temp_started"] = now

        # 🔥 남은 시간이 20초 이하이면 DEADLINE 연장
        remain = seat.get("release_remain")
        if remain is not None and remain <= 20 and deadline is not None:
            extra = 20 - remain
            seat["unreserve_deadline"] = deadline + timedelta(seconds=extra + 20)

        return current, inferred_state, STATE_STABLE_TIME

    # -----------------------------
    # 3) temp_state는 있는데 다른 상태로 바뀜
    # -----------------------------
    if temp != inferred_state:
        seat["temp_state"] = inferred_state
        seat["temp_started"] = now

        remain = seat.get("release_remain")
        if remain is not None and remain <= 20 and deadline is not None:
            extra = 20 - remain
            seat["unreserve_deadline"] = deadline + timedelta(seconds=extra)

        return current, inferred_state, STATE_STABLE_TIME

    # -----------------------------
    # 4) temp_state 유지 중
    # -----------------------------
    elapsed = (now - temp_started).total_seconds()
    remain_temp = max(0, STATE_STABLE_TIME - int(elapsed))

    # 임시 상태가 확정될 때
    if elapsed >= STATE_STABLE_TIME:
        seat["state"] = inferred_state
        seat["last_update"] = now
        seat["temp_state"] = None
        seat["temp_started"] = None

        # DEADLINE 재설정
        if inferred_state == "Empty":
            seat["unreserve_deadline"] = now + timedelta(minutes=1)
        elif inferred_state == "Camped":
            seat["unreserve_deadline"] = now + timedelta(minutes=3)
        else:
            seat["unreserve_deadline"] = None

        return inferred_state, None, None

    return current, temp, remain_temp


# -----------------------------
# DEADLINE 기반 정책 엔진
# -----------------------------
def update_policies(seats, now=None):
    if now is None:
        now = datetime.now()

    alerts = []

    for sid, seat in seats.items():
        state = seat["state"]
        reserved = seat["reserved"]
        deadline = seat.get("unreserve_deadline")
        reserved_at = seat.get("reserved_at")
        last_update = seat.get("last_update")
        ever_occ = seat["ever_occupied"]
        authorized = seat["authorized"]

        # ------------------------------------------------------------------
        # DEADLINE 남은 시간 계산 (main.py에서 보여주기 위해)
        # ------------------------------------------------------------------
        if reserved and deadline is not None:
            remain = int((deadline - now).total_seconds())
            seat["release_remain"] = max(remain, 0)
        else:
            seat["release_remain"] = None

        # ------------------------------------------------------------------
        # 1) DEADLINE 도달 → 자동 예약 해제
        # ------------------------------------------------------------------
        if reserved and deadline is not None and now >= deadline:
            seat["reserved"] = False
            seat["unreserve_deadline"] = None

            alerts.append({
                "seat": sid,
                "type": "Auto-Unreserve",
                "message": f"{sid} 좌석이 자동으로 예약해제되었습니다."
            })
            continue

        # -------------------------
        # 캠핑 (STATE 기반)
        # -------------------------
        if state == "Camped" and last_update:
            if now - last_update >= timedelta(minutes=POLICY_CONFIG["camping_minutes"]):
                alerts.append({
                    "seat": sid,
                    "type": "camping",
                    "message": f"{sid} 좌석이 2시간 이상 짐만 존재합니다."
                })

        # -------------------------
        # No-Show
        # -------------------------
        if reserved and state == "Empty" and not ever_occ and reserved_at:
            if now - reserved_at >= timedelta(minutes=POLICY_CONFIG["no_show_minutes"]):
                alerts.append({
                    "seat": sid,
                    "type": "no_show",
                    "message": f"{sid} 좌석이 No-Show 의심됩니다."
                })

        # -------------------------
        # Return Needed
        # -------------------------
        if reserved and state == "Empty" and ever_occ and last_update:
            if now - last_update >= timedelta(minutes=POLICY_CONFIG["return_grace_minutes"]):
                alerts.append({
                    "seat": sid,
                    "type": "return",
                    "message": f"{sid} 좌석은 사용 후 반납이 필요합니다."
                })

        # -------------------------
        # Unauthorized
        # -------------------------
        if state in ("Occupied", "Camped") and not authorized:
            alerts.append({
                "seat": sid,
                "type": "unauthorized",
                "message": f"{sid}: 비인가 사용자 감지"
            })

    return alerts

def update_release_timer(seats):
    now = datetime.now()

    for sid, s in seats.items():

        if not s["reserved"]:
            s["release_remain"] = None
            continue

        deadline = s.get("unreserve_deadline")

        # ❗ DEADLINE이 없으면 = 초기 설정 필요
        if deadline is None:
            last_update = s.get("last_update") or s.get("reserved_at") or now

            if s["state"] == "Empty":
                s["unreserve_deadline"] = last_update + timedelta(minutes=1)
            elif s["state"] == "Camped":
                s["unreserve_deadline"] = last_update + timedelta(minutes=3)
            else:
                s["unreserve_deadline"] = None
                s["release_remain"] = None
                continue

            deadline = s["unreserve_deadline"]

        # ❗ 여기서는 DEADLINE을 재설정하지 말고 “계산만”
        remain = int((deadline - now).total_seconds())
        s["release_remain"] = max(remain, 0)
