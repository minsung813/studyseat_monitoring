# streamlit run app/main.py
import streamlit as st
from datetime import datetime, timedelta
from logic.seat_logic import (
    init_seats, set_seat_state, VALID_STATES,
    check_status, update_policies
)
import json
import cv2
import numpy as np
import time
from ultralytics import YOLO
import pandas as pd
import csv
from logic.seat_logic import update_seat_state



# ------------------------------------------------------------
# 🎯 YOLO 모델 로드
# ------------------------------------------------------------
model = YOLO("yolov8n.pt")


# ------------------------------------------------------------
# 🎯 좌석별 ROI 불러오기
# ------------------------------------------------------------
with open("seats_roi.json", "r") as f:
    seat_rois = json.load(f)


# ------------------------------------------------------------
# 🎥 YOLO 실시간 웹캠 판별 함수 (최상단에 위치해야 함)
# ------------------------------------------------------------
def run_webcam_test(model, seat_rois):

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        st.error("웹캠을 열 수 없습니다!")
        return

    stframe = st.empty()

    # ⭐ 유지할 클래스 선언
    keep_classes = ["person", "backpack", "laptop", "book"]

    # ⭐ 클래스 재매핑 함수
    def remap_class(name):
        if name in keep_classes:
            return name
        else:
            return "object"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO 추론
        results = model(frame)[0]

        detections = []
        for box in results.boxes:
            cls = int(box.cls[0])
            name = results.names[cls]

            # ⭐ 클래스 재매핑
            name = remap_class(name)

            # ⭐ bounding box 좌표
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # ⭐⭐ YOLO 박스 그리기 ⭐⭐
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(
                frame, name, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
            )

            # 탐지 목록 저장
            detections.append({
                "name": name,
                "bbox": [x1, y1, x2, y2]
            })

        
        

        # 좌석 상태 계산
        seat_states = {}

        for idx, roi in enumerate(seat_rois):
            seat_id = list(st.session_state["seats"].keys())[idx]
            x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]

            in_roi = []
            for d in detections:
                dx1, dy1, dx2, dy2 = d["bbox"]

                if not (dx2 < x1 or dx1 > x2 or dy2 < y1 or dy1 > y2):
                    in_roi.append(d["name"])

            seat_states[seat_id] = check_status(in_roi)

        # 화면 출력
        stframe.image(frame, channels="BGR")
        st.write(seat_states)

        time.sleep(1)



# ------------------------------------------------------------
# ⭐ Streamlit UI 구성
# ------------------------------------------------------------
st.set_page_config(
    page_title="열람실 좌석 모니터링",
    layout="wide",
)

# 최초 실행 시 세션 초기화
if "seats" not in st.session_state:
    st.session_state["seats"] = init_seats()

st.title("📚 열람실 좌석 모니터링 시스템 (Day 1 테스트)")

# ------------------------------------------------------------
# Day 1-2 수동 좌석 상태 변경
# ------------------------------------------------------------
st.subheader("좌석 상태 수동 변경 (Day 1-2 테스트)")

col1, col2 = st.columns(2)

with col1:
    selected_seat = st.selectbox("좌석 선택", list(st.session_state["seats"].keys()))

with col2:
    selected_state = st.selectbox("새 상태", VALID_STATES)

if st.button("상태 변경 적용", key="manual_state_btn"):
    set_seat_state(st.session_state["seats"], selected_seat, selected_state)
    st.success(f"{selected_seat} 상태가 {selected_state} 로 변경되었습니다.")


# ------------------------------------------------------------
# ⭐ Day 3-4 AI 판별 테스트
# ------------------------------------------------------------
st.subheader("🤖 AI 3-State 판별 로직 테스트 (Day 3-4)")

col3, col4, col5 = st.columns(3)

with col3:
    ai_seat = st.selectbox(
        "AI 로직을 적용할 좌석 선택",
        list(st.session_state["seats"].keys()),
        key="ai_seat_select",
    )

with col4:
    scenario = st.selectbox(
        "탐지 시나리오 선택",
        [
            "🟢 아무것도 없음 (Empty)",
            "🟡 짐만 있음 (Camped)",
            "🔴 사람이 있음 (Occupied)",
            "🔴 사람 + 짐 (Occupied)",
        ],
        key="ai_scenario_select",
    )

with col5:
    st.write("")
    st.write("")
    run_ai_button = st.button("AI 로직 적용", key="apply_ai_btn")

scenario_to_detections = {
    "🟢 아무것도 없음 (Empty)": [],
    "🟡 짐만 있음 (Camped)": ["backpack"],
    "🔴 사람이 있음 (Occupied)": ["person"],
    "🔴 사람 + 짐 (Occupied)": ["person", "backpack"],
}

if run_ai_button:
    detections = scenario_to_detections[scenario]
    inferred_state = check_status(detections)

    set_seat_state(st.session_state["seats"], ai_seat, inferred_state)
    st.info(
        f"탐지 결과 {detections} → AI 판별 상태: **{inferred_state}**\n"
        f"{ai_seat} 좌석에 적용되었습니다!"
    )


# ------------------------------------------------------------
# 현재 좌석 테이블 출력
# ------------------------------------------------------------
st.subheader("현재 좌석 상태")

seats = st.session_state["seats"]
table = []

for seat_id, info in seats.items():
    table.append({
        "Seat": seat_id,
        "State": info["state"],
        "Last Update": info["last_update"].strftime("%H:%M:%S") if info["last_update"] else "-"
    })

st.table(table)

# ------------------------------------------------------------
# Day 5 정책 엔진 테스트
# ------------------------------------------------------------
st.subheader("🧪 Day 5 정책 엔진 테스트 (임시)")

if st.button("테스트용 위반 상황 넣기", key="policy_test_btn"):
    now = datetime.now()

    # No-Show / 캠핑 / Unauthorized 테스트 데이터
    seats["A1"]["state"] = "Camped"
    seats["A1"]["last_update"] = now - timedelta(minutes=130)

    seats["A2"]["state"] = "Empty"
    seats["A2"]["reserved"] = True
    seats["A2"]["reserved_at"] = now - timedelta(minutes=30)
    seats["A2"]["ever_occupied"] = False
    seats["A2"]["last_update"] = now - timedelta(minutes=30)

    seats["A3"]["state"] = "Empty"
    seats["A3"]["reserved"] = True
    seats["A3"]["reserved_at"] = now - timedelta(minutes=40)
    seats["A3"]["ever_occupied"] = True
    seats["A3"]["last_update"] = now - timedelta(minutes=10)

    seats["B1"]["state"] = "Occupied"
    seats["B1"]["authorized"] = False
    seats["B1"]["last_update"] = now - timedelta(minutes=5)

    st.success("테스트용 정책 위반 상황을 주입했습니다!")

alerts = update_policies(seats)
if alerts:
    st.subheader("⚠ 정책 엔진 경고")
    for alert in alerts:
        st.warning(f"[{alert['type']}] {alert['message']}")
else:
    st.caption("현재 정책 위반 없음")


# --------------------------
# ROI 박스 테스트 (Streamlit-safe)
# --------------------------
st.subheader("🎥 ROI 확인용 - 웹캠 테스트")

# 상태 저장
if "roi_cam_running" not in st.session_state:
    st.session_state["roi_cam_running"] = False

colA, colB = st.columns(2)

# 버튼들
start_roi = colA.button("▶ ROI 테스트 시작", key="roi_start")
stop_roi = colB.button("⏹ 종료", key="roi_stop")

# 시작 버튼 누르면 True
if start_roi:
    st.session_state["roi_cam_running"] = True

# 종료 버튼 누르면 False
if stop_roi:
    st.session_state["roi_cam_running"] = False

frame_window = st.empty()

# 메인 루프
if st.session_state["roi_cam_running"]:
    cap = cv2.VideoCapture(0)

    while st.session_state["roi_cam_running"]:
        ret, frame = cap.read()
        if not ret:
            st.error("웹캠을 불러올 수 없습니다.")
            break

        # ROI 그리기
        for idx, r in enumerate(seat_rois):
            x1, y1, x2, y2 = r["x1"], r["y1"], r["x2"], r["y2"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Seat {idx+1}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_window.image(frame_rgb)

    cap.release()
    frame_window.empty()




# ------------------------------------------------------------
# CSV 로그 저장 함수
# ------------------------------------------------------------
def save_ai_log(seat_states, csv_file="ai_log.csv"):
    fieldnames = ["timestamp"] + list(seat_states.keys())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 파일이 존재하는지 체크
    try:
        with open(csv_file, "r"):
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    # CSV 쓰기
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row = {"timestamp": now}
        row.update(seat_states)
        writer.writerow(row)
# ------------------------------------------------------------
# 🎯 Streamlit 공간 준비 (웹캠 영상 + 상태 텍스트)
# ------------------------------------------------------------
st.subheader("🤖 AI 좌석 판별 (실시간 + 로그 저장)")

colA, colB = st.columns(2)

# 버튼 (key 중복 제거!)
start_ai = colA.button("▶ AI 좌석 판별 시작", key="ai_start_main")
stop_ai = colB.button("⏹ 종료", key="ai_stop_main")

# AI 실행 상태 관리
if "ai_running" not in st.session_state:
    st.session_state["ai_running"] = False

if start_ai:
    st.session_state["ai_running"] = True
if stop_ai:
    st.session_state["ai_running"] = False

# 웹캠 영상 + 상태 테이블
col_cam, col_status = st.columns(2)
cam_window = col_cam.empty()
status_window = col_status.empty()

LOG_CSV = "seat_state_log.csv"

# ------------------------------------------------------------
# 🎥 AI 좌석 자동 판별 루프 (바운딩박스 포함 Streamlit-safe)
# ------------------------------------------------------------
if st.session_state["ai_running"]:
    cap = cv2.VideoCapture(0)

    keep_classes = ["person", "backpack", "laptop", "book", "clothes"]

    def remap_class(name):
        if name in keep_classes:
            return name
        else:
            return "object"

    while st.session_state["ai_running"]:
        ret, frame = cap.read()
        if not ret:
            st.error("웹캠을 불러올 수 없습니다.")
            break

        # YOLO는 RGB 이미지로 추론
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = model(rgb)[0]

        detections = []
        for box in results.boxes:
            cls = int(box.cls[0])
            name = remap_class(results.names[cls])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Bounding box draw
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, name, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            detections.append({
                "name": name,
                "bbox": [x1, y1, x2, y2]
            })


        # -----------------------------
        # ROI 판별 + 색상 지정
        # -----------------------------
        SEAT_IDS = list(st.session_state["seats"].keys())  # A1~B3

        seat_states = {}
        for idx, roi in enumerate(seat_rois):
            seat_id = SEAT_IDS[idx]
        
            x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]
        
            seat_info = st.session_state["seats"][seat_id]
        
            # ROI 색 결정
            if seat_info.get("temp_state") is not None:
                roi_color = (0, 255, 255)      # Yellow (임시 상태)
            elif seat_info["reserved"]:
                roi_color = (0, 255, 0)        # Green (예약된 좌석)
            else:
                roi_color = (0, 0, 255)        # Red (예약 안됨)
        
            # ROI 박스 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), roi_color, 2)
        
            # 텍스트도 같이 표시
            label_text = seat_id
            if seat_info.get("temp_state"):
                label_text += f" ({seat_info['temp_state']}?)"
        
            cv2.putText(frame, label_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, roi_color, 2)
        
            # ROI 내부 detection 체크
            in_roi = []
            for d in detections:
                dx1, dy1, dx2, dy2 = d["bbox"]
                if not (dx2 < x1 or dx1 > x2 or dy2 < y1 or dy1 > y2):
                    in_roi.append(d["name"])
        
            inferred = check_status(in_roi)

            # 좌석 구조 가져오기
            seat = st.session_state["seats"][seat_id]

            # 임시 상태 처리 포함한 최종 상태 반환
            final_state = update_seat_state(seat, inferred)

            seat_states[seat_id] = final_state




        # -----------------------------
        # 🔥 예약된 좌석만 필터링 및 표시
        # -----------------------------
        filtered_states = {
            seat: state
            for seat, state in seat_states.items()
            if st.session_state["seats"][seat]["reserved"]
        }

        # Streamlit에 출력
        cam_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        status_window.table(filtered_states)

        # CSV 저장
        df = pd.DataFrame([filtered_states])
        df.to_csv(
            LOG_CSV,
            mode='a',
            header=not pd.io.common.file_exists(LOG_CSV),
            index=False,
        )

        time.sleep(0.2)

    cap.release()
    st.success("AI 좌석 판별 종료됨.")