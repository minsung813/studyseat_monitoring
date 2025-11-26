from datetime import datetime, timedelta

# 좌석 목록 (필요하면 나중에 확장 가능)
INITIAL_SEATS = ["A1", "A2", "A3", "B1", "B2", "B3"]

# 가능한 상태
VALID_STATES = ["Empty", "Occupied", "Camped"]

# 정책 설정 (분 단위)
POLICY_CONFIG = {
    "camping_minutes": 120,       # 2시간 이상 Camped면 캠핑 의심
    "no_show_minutes": 20,        # 예약 후 20분 동안 안 오면 No-Show
    "return_grace_minutes": 5,    # 떠난 후 5분 안에 반납 처리되지 않으면 반납 필요
}


def init_seats():
    """
    좌석 상태 초기화.

    각 좌석 정보 구조:
    {
        "state": "Empty" | "Occupied" | "Camped",
        "last_update": datetime | None,

        # 정책 엔진용 필드 (Day 5~)
        "reserved": False,            # 예약 여부
        "reserved_at": None,          # 예약이 만들어진 시간
        "ever_occupied": False,       # 한 번이라도 Occupied 된 적 있는지
        "authorized": True,           # 인가된 사용자 여부 (False면 비인가)
    }
    """
    seats = {}
    for seat in INITIAL_SEATS:
        seats[seat] = {
            "state": "Empty",
            "last_update": None,
            "reserved": False,
            "reserved_at": None,
            "ever_occupied": False,
            "authorized": True,
        }
    return seats


def set_seat_state(seats, seat_id, new_state):
    """
    좌석 상태를 변경하고, last_update / ever_occupied를 갱신하는 함수.
    """
    if seat_id not in seats:
        raise ValueError(f"Unknown seat id: {seat_id}")

    if new_state not in VALID_STATES:
        raise ValueError(f"Invalid state: {new_state}")

    info = seats[seat_id]
    info["state"] = new_state
    info["last_update"] = datetime.now()

    # 한 번이라도 Occupied가 된 적이 있는지 기록
    if new_state == "Occupied":
        info["ever_occupied"] = True


# =========================
# Day 3-4: 3-State 판별 로직
# =========================


def check_status(detections):
    """
    YOLO 탐지 결과(클래스 이름 리스트)를 받아서
    좌석 상태 (Empty / Occupied / Camped)를 결정.

    Camped 기준:
        - backpack
        - laptop
        - book
    """

    det_set = set(detections)

    # 1) 사람이 보이면 무조건 Occupied
    if "person" in det_set:
        return "Occupied"

    # 2) 짐만 있으면 Camped (backpack, laptop, book)
    CAMPED_ITEMS = {"backpack", "laptop", "book"}
    if det_set & CAMPED_ITEMS:
        return "Camped"

    # 3) 아무것도 없으면 Empty
    return "Empty"



# =========================
# Day 5-6: 정책 엔진 로직
# =========================

def update_policies(seats, now=None):
    """
    좌석 상태(seats)를 기준으로
    No-Show / 반납 / 캠핑 / 비인가 4가지 정책을 체크하고,
    위반/의심 항목에 대한 메시지 리스트를 반환.

    return 형식 예:
        [
            {"seat": "A1", "type": "camping", "message": "..."},
            {"seat": "B2", "type": "no_show", "message": "..."},
            ...
        ]
    """
    if now is None:
        now = datetime.now()

    alerts = []

    camping_threshold = timedelta(minutes=POLICY_CONFIG["camping_minutes"])
    no_show_threshold = timedelta(minutes=POLICY_CONFIG["no_show_minutes"])
    return_threshold = timedelta(minutes=POLICY_CONFIG["return_grace_minutes"])

    for seat_id, info in seats.items():
        state = info["state"]
        last_update = info.get("last_update")
        reserved = info.get("reserved", False)
        reserved_at = info.get("reserved_at")
        ever_occupied = info.get("ever_occupied", False)
        authorized = info.get("authorized", True)

        # -----------------
        # 1) 캠핑(Camping)
        # -----------------
        if state == "Camped" and last_update is not None:
            elapsed = now - last_update
            if elapsed >= camping_threshold:
                alerts.append({
                    "seat": seat_id,
                    "type": "camping",
                    "message": (
                        f"{seat_id} 좌석: {POLICY_CONFIG['camping_minutes']}분 이상 "
                        f"짐만 있어서 '캠핑' 의심"
                    ),
                })

        # -----------------
        # 2) No-Show
        # -----------------
        # 조건: 예약은 되어 있는데, 사람이 한 번도 앉지 않았고(ever_occupied=False),
        #       좌석 상태가 계속 Empty인 경우
        if reserved and state == "Empty" and reserved_at is not None and not ever_occupied:
            elapsed_since_resv = now - reserved_at
            if elapsed_since_resv >= no_show_threshold:
                alerts.append({
                    "seat": seat_id,
                    "type": "no_show",
                    "message": (
                        f"{seat_id} 좌석: 예약 후 {POLICY_CONFIG['no_show_minutes']}분이 지나도록 "
                        f"착석하지 않아 'No-Show' 의심"
                    ),
                })

        # -----------------
        # 3) 반납 필요(Return)
        # -----------------
        # 조건: 예전에 Occupied였던 좌석이 지금은 Empty이고,
        #       일정 시간(return_grace_minutes) 이상 그대로인 경우
        if reserved and state == "Empty" and ever_occupied and last_update is not None:
            elapsed_empty = now - last_update
            if elapsed_empty >= return_threshold:
                alerts.append({
                    "seat": seat_id,
                    "type": "return",
                    "message": (
                        f"{seat_id} 좌석: 사용자가 떠난 뒤 "
                        f"{POLICY_CONFIG['return_grace_minutes']}분 이상 비어 있어 "
                        f"'반납 처리'가 필요해 보입니다."
                    ),
                })

        # -----------------
        # 4) 비인가 사용자(Unauthorized)
        # -----------------
        # 조건: 좌석에 누가 앉아 있거나 짐이 있는데(Occupied/Camped),
        #       authorized 플래그가 False인 경우
        if state in ("Occupied", "Camped") and not authorized:
            alerts.append({
                "seat": seat_id,
                "type": "unauthorized",
                "message": (
                    f"{seat_id} 좌석: 비인가 사용자 혹은 비인가 사용 패턴이 감지되었습니다."
                ),
            })

    return alerts
