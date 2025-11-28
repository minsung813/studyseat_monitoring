import cv2
import json
import numpy as np

# 저장될 ROI 파일 이름
ROI_FILE = "seats_roi.json"

# ROI 저장 리스트
rois = []
points = []   # 현재 ROI의 4개 점 저장
frame = None


def click_event(event, x, y, flags, param):
    global points, frame

    if event == cv2.EVENT_LBUTTONDOWN:
        # 클릭한 점 추가
        points.append([x, y])
        print(f"Point added: {points[-1]}")

        # 점 그리기
        cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

        # 선 그리기 (점이 2개 이상일 때)
        if len(points) > 1:
            cv2.line(frame, tuple(points[-2]), tuple(points[-1]), (0, 255, 0), 2)

        # 4번째 점 → ROI 완성
        if len(points) == 4:
            # 마지막 점과 첫 점 연결하여 폐합
            cv2.line(frame, tuple(points[3]), tuple(points[0]), (0, 255, 0), 2)

            # ROI 저장
            rois.append({
                "points": points.copy()
            })
            print("ROI Completed:", rois[-1])

            # 다음 ROI 선택 준비
            points.clear()

        cv2.imshow("ROI Selector", frame)


# --- 1) 웹캠에서 한 프레임 가져오기 ---
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

if not ret:
    print(" 웹캠에서 프레임을 불러오지 못했습니다.")
    exit()

cv2.namedWindow("ROI Selector")
cv2.setMouseCallback("ROI Selector", click_event)

print("===  ROI 다각형 선택기 실행 중 ===")
print("좌석 영역을 마우스로 4번 클릭해 주세요 (4점 = 1개 좌석).")
print("S 키 → 저장 / ESC → 종료")

while True:
    cv2.imshow("ROI Selector", frame)
    key = cv2.waitKey(1)

    if key == ord('s'):
        with open(ROI_FILE, "w") as f:
            json.dump(rois, f, indent=4)
        print(f" ROI 저장 완료 → {ROI_FILE}")
        break

    elif key == 27:  # ESC
        print(" ROI 선택 취소")
        break

cv2.destroyAllWindows()
