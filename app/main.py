# streamlit run app/main.py
import streamlit as st
import os
from datetime import datetime
import cv2
import pandas as pd
import time
import json
import numpy as np
from ultralytics import YOLO
from logic.seat_logic import (
    init_seats,
    check_status,
    update_seat_state,
    update_policies,
)

def is_inside_polygon(bbox, polygon):
    x1, y1, x2, y2 = bbox
    test_points = [
        (x1, y1),         # 좌상단
        (x2, y1),         # 우상단
        (x1, y2),         # 좌하단
        (x2, y2),         # 우하단
        ((x1 + x2)//2, (y1 + y2)//2)  # 중심
    ]

    pts = np.array(polygon, np.int32)

    for (tx, ty) in test_points:
        inside = cv2.pointPolygonTest(pts, (tx, ty), False)
        if inside >= 0:
            return True
    return False

# ============================================
# 초기 설정
# ============================================
st.set_page_config(page_title="열람실 좌석 모니터링", layout="wide")

# YOLO 모델 로드
model = YOLO("yolov8m.pt")

# ROI 불러오기
with open("seats_roi.json", "r") as f:
    seat_rois = json.load(f)

# 세션 초기화
if "seats" not in st.session_state:
    st.session_state["seats"] = init_seats()
if "ai_running" not in st.session_state:
    st.session_state["ai_running"] = False
if "admin_mode" not in st.session_state:
    st.session_state["admin_mode"] = False

seats = st.session_state["seats"]


# ============================================
# 🎛 관리자 모드 토글
# ============================================
st.sidebar.title("⚙ 관리자 설정")

st.sidebar.write("관리자 기능을 켜면 수동 조작 기능이 나타납니다.")
admin_toggle = st.sidebar.checkbox("관리자 모드 활성화", value=False)
st.session_state["admin_mode"] = admin_toggle


# ============================================
# 관리자 모드에서는 수동 조작 기능 표시
# ============================================
if st.session_state["admin_mode"]:
    st.subheader("🛠 관리자 모드 - 수동 좌석 상태 변경")

    col1, col2 = st.columns(2)
    seat_select = col1.selectbox("좌석 선택", list(seats.keys()))
    state_select = col2.selectbox("새 상태 설정", ["Empty", "Occupied", "Camped"])

    if st.button("적용"):
        seats[seat_select]["state"] = state_select
        seats[seat_select]["last_update"] = datetime.now()
        st.success(f"{seat_select} 상태가 '{state_select}' 로 변경되었습니다.")


# ============================================
# 📸 실시간 좌석 판별 UI
# ============================================
st.title("📚 열람실 좌석 모니터링 시스템")

col_cam, col_status = st.columns(2)
cam_window = col_cam.empty()
status_window = col_status.empty()

start_btn = st.button("▶ AI 판별 시작")
stop_btn = st.button("⏹ 종료")

if start_btn:
    st.session_state["ai_running"] = True
if stop_btn:
    st.session_state["ai_running"] = False


# ============================================
# 🎥 AI 판별 루프
# ============================================
if st.session_state["ai_running"]:
    cap = cv2.VideoCapture(0)
    keep_classes = ["person", "backpack", "laptop", "book", "clothes"]

    def remap_class(name):
        return name if name in keep_classes else "object"

    while st.session_state["ai_running"]:
        ret, frame = cap.read()
        if not ret:
            st.error("웹캠을 불러올 수 없습니다.")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = model(rgb)[0]

        detections = []
        for box in results.boxes:
            cls = int(box.cls[0])
            name = remap_class(results.names[cls])

            # object 모두 무시
            if name == "object":
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # 시각화
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, name, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            detections.append({"name": name, "bbox": [x1, y1, x2, y2]})

        # ===========================
        # ROI 기반 좌석 판별
        # ===========================
        SEAT_IDS = list(seats.keys())
        seat_states = {}
        
        for idx, roi in enumerate(seat_rois):
            seat_id = SEAT_IDS[idx]
            polygon = roi["points"]   # ⭐ 다각형 사용
            seat_info = seats[seat_id]
        
            # ROI 색상
            if seat_info.get("temp_state"):
                roi_color = (0, 255, 255)
            elif seat_info["reserved"]:
                roi_color = (0, 255, 0)
            else:
                roi_color = (0, 0, 255)
        
            # ROI polygon 그리기
            pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, roi_color, 2)
        
            # ROI 내부 detection 확인 (⭐ 다각형 기반)
            in_roi = []
            for d in detections:
                if is_inside_polygon(d["bbox"], polygon):
                    in_roi.append(d["name"])
        
            inferred = check_status(in_roi)
            result = update_seat_state(seat_info, inferred)
        
            # 반환값 정리
            if isinstance(result, tuple):
                final_state, temp_state, remain = result
            else:
                final_state, temp_state, remain = result, None, None
        
            seat_info["state"] = final_state
            seat_info["temp_state"] = temp_state
            seat_info["remain"] = remain
        
            seat_states[seat_id] = final_state
        
            # ROI 텍스트 표시
            tx, ty = polygon[0]
            label = seat_id
            if temp_state:
                sec = remain if remain is not None else "..."
                label += f" ({temp_state}? {sec}s)"
            cv2.putText(frame, label, (tx, ty - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, roi_color, 2)
        

        # 정책 엔진 실행
        alerts = update_policies(seats)
        if alerts:
            for a in alerts:
                st.warning(f"[{a['type']}] {a['message']}")

        # 예약된 좌석만 테이블로 표시
        filtered_for_table = []
        for sid, info in seats.items():
            if info["reserved"]:
                filtered_for_table.append({
                    "Seat": sid,
                    "State": info["state"],
                    "Temp": info.get("temp_state"),
                    "Remain": info.get("remain"),
                    "Reserved": info["reserved"],
                    "Release_Remain": info.get("release_remain"),
                    "Last Update": info["last_update"].strftime("%H:%M:%S") if info["last_update"] else "-"
                })

        cam_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        status_window.table(filtered_for_table)

        time.sleep(0.2)

    cap.release()
    st.success("AI 좌석 판별 종료됨.")
