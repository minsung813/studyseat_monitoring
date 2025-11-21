# streamlit run app/main.py
import streamlit as st
from datetime import datetime, timedelta
from logic.seat_logic import init_seats, set_seat_state, VALID_STATES, check_status, update_policies

st.set_page_config(
    page_title="열람실 좌석 모니터링",
    layout="wide",
)

# 세션에 seats가 없다면 초기화
if "seats" not in st.session_state:
    st.session_state["seats"] = init_seats()

st.title("📚 열람실 좌석 모니터링 시스템 (Day 1 테스트)")

st.subheader("좌석 상태 수동 변경 (Day 1-2 테스트)")

col1, col2 = st.columns(2)

with col1:
    selected_seat = st.selectbox("좌석 선택", list(st.session_state["seats"].keys()))

with col2:
    selected_state = st.selectbox("새 상태", VALID_STATES)

if st.button("상태 변경 적용"):
    set_seat_state(st.session_state["seats"], selected_seat, selected_state)
    st.success(f"{selected_seat} 상태가 {selected_state} 로 변경되었습니다.")

# -----------------------------------------------------
# ⭐ AI 3-State 판별 로직 테스트 (Day 3-4)
# -----------------------------------------------------
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
    run_ai_button = st.button("AI 로직 적용")

# 시나리오 → detections 매핑
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
        f"탐지 결과 {detections} → AI 판별 상태: **{inferred_state}**"
        f"\n{ai_seat} 좌석에 적용했습니다!"
    )


st.subheader("현재 좌석 상태")

seats = st.session_state["seats"]

table_data = []
for seat_id, info in seats.items():
    last_update = (
        info["last_update"].strftime("%H:%M:%S")
        if info["last_update"] else "-"
    )
    table_data.append({
        "Seat": seat_id,
        "State": info["state"],
        "Last Update": last_update
    })

st.table(table_data)

# --------------------------
# Day 5 정책 엔진 테스트용 버튼
# --------------------------
st.subheader("🧪 Day 5 정책 엔진 테스트 (임시)")

if st.button("테스트용 위반 상황 넣기"):
    now = datetime.now()

    # 1) A1: 2시간 넘게 Camped 상태 → 캠핑 의심
    seats["A1"]["state"] = "Camped"
    seats["A1"]["last_update"] = now - timedelta(minutes=130)  # 130분 전

    # 2) A2: 예약만 되고 한 번도 안 앉았고, 30분 동안 Empty → No-Show 의심
    seats["A2"]["state"] = "Empty"
    seats["A2"]["reserved"] = True
    seats["A2"]["reserved_at"] = now - timedelta(minutes=30)
    seats["A2"]["ever_occupied"] = False
    seats["A2"]["last_update"] = now - timedelta(minutes=30)

    # 3) A3: 예전에 앉은 적 있음(ever_occupied=True), 지금은 떠난 지 10분 → 반납 필요
    seats["A3"]["state"] = "Empty"
    seats["A3"]["reserved"] = True
    seats["A3"]["reserved_at"] = now - timedelta(minutes=40)
    seats["A3"]["ever_occupied"] = True
    seats["A3"]["last_update"] = now - timedelta(minutes=10)

    # 4) B1: 누군가 앉아 있는데 비인가 사용자 → Unauthorized
    seats["B1"]["state"] = "Occupied"
    seats["B1"]["authorized"] = False
    seats["B1"]["last_update"] = now - timedelta(minutes=5)

    st.success("테스트용 정책 위반 상황을 좌석 데이터에 주입했습니다. 아래 경고 영역을 확인해 주세요!")


# --------------------------
# 정책 엔진 경고 표시 (MVP)
# --------------------------
alerts = update_policies(seats)

if alerts:
    st.subheader("⚠ 정책 엔진 경고 (Day 5 MVP)")
    for alert in alerts:
        # 타입별로 나중에 색깔 분리 가능 (지금은 전부 warning으로 표시)
        st.warning(f"[{alert['type']}] {alert['message']}")
else:
    # 나중엔 이 문구는 빼도 됨. 지금은 동작 확인용.
    st.caption("현재 정책 위반/의심 좌석 없음 (테스트용 기본 문구)")
