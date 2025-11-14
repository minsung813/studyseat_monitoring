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
