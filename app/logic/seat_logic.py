# app/logic/seat_logic.py
from datetime import datetime

# Day 1 기준: 단순 좌석 목록
INITIAL_SEATS = {
    "A1": {"state": "Empty", "last_update": None},
    "A2": {"state": "Empty", "last_update": None},
    "A3": {"state": "Empty", "last_update": None},
    "B1": {"state": "Empty", "last_update": None},
    "B2": {"state": "Empty", "last_update": None},
    "B3": {"state": "Empty", "last_update": None},
}

VALID_STATES = ["Empty", "Occupied", "Camped"]

def init_seats():
    """초기 좌석 상태 복사"""
    seats = {}
    for seat_id, info in INITIAL_SEATS.items():
        seats[seat_id] = {
            "state": info["state"],
            "last_update": info["last_update"],
        }
    return seats

def set_seat_state(seats, seat_id, new_state):
    """좌석 상태를 수동으로 변경 (Day1-2 테스트용)"""
    from datetime import datetime

    seats[seat_id]["state"] = new_state
    seats[seat_id]["last_update"] = datetime.now()
    return seats

# YOLO 클래스 이름과 매핑할 집합 (A팀이 실제 클래스 이름에 맞게 나중에 조정)
PERSON_CLASSES = {"person"}
BAG_CLASSES = {"backpack", "bag"}
DEVICE_CLASSES = {"laptop"}

def check_status(detections):
    """
    YOLO 탐지 결과(클래스 이름 리스트)를 받아서
    좌석 상태 (Empty / Occupied / Camped) 중 하나를 반환합니다.

    detections 예시:
        []                          -> "Empty"
        ["person"]                  -> "Occupied"
        ["backpack"]                -> "Camped"
        ["laptop", "backpack"]      -> "Camped"
        ["person", "backpack"]      -> "Occupied"
    """
    det_set = set(detections)

    # 1) 사람이 있으면 무조건 Occupied
    if det_set & PERSON_CLASSES:
        return "Occupied"

    # 2) 사람은 없지만 짐/노트북만 있으면 Camped
    if det_set & (BAG_CLASSES | DEVICE_CLASSES):
        return "Camped"

    # 3) 아무것도 없으면 Empty
    return "Empty"
