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
│  ├─ main.py                     # Streamlit 메인 대시보드
│  │
│  ├─ logic/
│  │  └─ seat_logic.py            # 좌석 상태 관리 / 정책 로직(확장 예정)
│  │
│  └─ data_processing/
│     ├─ extract_frames.py        # OpenCV: 영상 → 1초 단위 프레임 추출 스크립트
│     │
│     └─ dataset_raw/             # 영상에서 추출한 원본 이미지 데이터셋
│        ├─ nothing1/
│        ├─ object1/
│        └─ people1/
│
├─ requirements.txt                # PyTorch·YOLO·Streamlit·OpenCV 등 패키지 목록
├─ README.md
└─ .gitignore
```