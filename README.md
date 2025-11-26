# 열람실 좌석 자동 모니터링 시스템

```
# 최신화 코드
git checkout main
git pull origin main
git checkout 개인브랜치
git merge main
```

```
# git commit & push 코드
git status
git add 바뀐코드
git commit -m "메세지"
git push origin 개인브랜치
```

```
# 가상환경 활성화
conda activate 가상환경이름
```

```
# merge 방법
git checkout main
git pull origin main
git merge 개인브랜치
git push origin main
```

```
# 프로젝트 구조
studyseat_monitoring/
│
├─ app/
│  ├─ data_processing/
│  │  ├─ dataset_raw/                 ← 원본 영상 및 프레임 저장
│  │  ├─ extract_frames.py            ← 영상 → 프레임 추출 스크립트
│  │  ├─ roi_selector.py              ← 좌석 ROI 설정 스크립트 (C팀원 작업)
│  │
│  ├─ logic/
│  │  ├─ seat_logic.py                ← 3-State + 정책 엔진 (B팀 작업)
│  │
│  ├─ model/
│  │  ├─ 학술제_AI모델_v1_best.pt     ← A팀원이 제공한 YOLO 모델 체크포인트
│  │
│  ├─ main.py                         ← Streamlit 메인 앱
│
├─ data.yaml                          ← YOLO 학습용 데이터셋 설정
├─ seats_roi.json                     ← ROI 좌표 정보 (C팀원 작업)
├─ train.py                           ← YOLO 파인튜닝 스크립트 (A팀원 작업)
├─ yolo11n.pt                         ← YOLO11n 모델 가중치
├─ yolov8n.pt                         ← YOLOv8n 모델 가중치
│
├─ requirements.txt                   ← 개발 환경 패키지 리스트
├─ README.md                          ← 프로젝트 문서
├─ .gitignore

```