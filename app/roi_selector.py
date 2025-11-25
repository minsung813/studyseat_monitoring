import cv2
import json

# 저장될 ROI 파일 이름
ROI_FILE = "seats_roi.json"

# ROI 저장 리스트
rois = []
drawing = False
ix, iy = -1, -1
frame = None

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, frame

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp = frame.copy()
            cv2.rectangle(temp, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow("ROI Selector", temp)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(frame, (ix, iy), (x, y), (0, 255, 0), 2)
        rois.append({
            "x1": min(ix, x),
            "y1": min(iy, y),
            "x2": max(ix, x),
            "y2": max(iy, y)
        })
        print(f"ROI added: {rois[-1]}")
        cv2.imshow("ROI Selector", frame)


# 웹캠에서 한 프레임 가져오기
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

if not ret:
    print("웹캠에서 프레임을 불러오지 못했습니다.")
    exit()

cv2.namedWindow("ROI Selector")
cv2.setMouseCallback("ROI Selector", draw_rectangle)

print("=== ROI 선택기 실행 중 ===")
print("마우스로 좌석 영역을 드래그하여 선택하세요.")
print("완료되면 S 키로 저장, ESC 키로 종료합니다.")

while True:
    cv2.imshow("ROI Selector", frame)
    key = cv2.waitKey(1)

    if key == ord('s'):
        with open(ROI_FILE, "w") as f:
            json.dump(rois, f, indent=4)
        print(f"📁 ROI 저장 완료: {ROI_FILE}")
        break

    elif key == 27:  # ESC
        print(" ROI 선택 취소")
        break

cv2.destroyAllWindows()
