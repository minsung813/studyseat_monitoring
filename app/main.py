import streamlit as st
from logic.seat_logic import init_seats, set_seat_state, VALID_STATES

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
