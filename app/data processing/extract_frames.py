import cv2
import os
import sys

# --- 1. 설정 (Configuration) ---

# [수정됨] 모든 영상 데이터셋 폴더를 저장할 기본 경로
BASE_OUTPUT_DIR = 'app/data processing/dataset_raw'

# 몇 초(Second)에 1장씩 추출할지 설정 (1.0 = 1초, 5.0 = 5초)
SECONDS_PER_FRAME = 1.0

# -----------------------------------

def extract_frames(video_path, output_dir, interval_sec):
    print(f"\n'{video_path}' 파일에서 {interval_sec}초당 1프레임 추출을 시작합니다.")
    print(f"저장 위치: '{output_dir}'")
    
    # 1. 출력 폴더 생성 (os.makedirs는 경로 전체를 생성해 줍니다)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"'{output_dir}' 폴더를 생성했습니다.")
    else:
        print(f"'{output_dir}' 폴더가 이미 존재합니다. 이곳에 덮어씁니다.")

    # 2. 비디오 파일 열기
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"오류: '{video_path}' 비디오 파일을 열 수 없습니다.")
        return

    # 3. 비디오 정보(FPS) 가져오기
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print("오류: 비디오 FPS를 읽을 수 없습니다. 기본값 30으로 설정합니다.")
        fps = 30.0

    # 4. 건너뛸 프레임 수 계산
    frame_interval = int(fps * interval_sec)
    print(f"비디오 FPS: {fps:.2f} (약 {frame_interval} 프레임당 1장 저장)")

    current_frame = 0
    saved_frame_count = 0

    while True:
        # 5. 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print("비디오의 끝에 도달했습니다.")
            break

        # 6. 저장할 시점인지 확인
        if current_frame % frame_interval == 0:
            # 7. 이미지 파일로 저장
            save_path = os.path.join(output_dir, f"frame_{saved_frame_count:05d}.jpg")
            cv2.imwrite(save_path, frame)
            
            if saved_frame_count % 10 == 0:
                print(f"  -> {save_path} 저장됨...")
            
            saved_frame_count += 1
        
        current_frame += 1

    # 8. 작업 완료 및 리소스 해제
    cap.release()
    print("\n" + "="*30)
    print("프레임 추출 작업 완료!")
    print(f"총 저장된 이미지 개수: {saved_frame_count} 개")
    print(f"최종 저장 위치: {output_dir} 폴더")
    print("="*30)


if __name__ == "__main__":
    
    # --- [수정된 부분 1] ---
    # 1. 비디오 파일 경로 입력받기
    video_path_input = input("프레임을 추출할 비디오 파일 경로를 입력하세요 (예: video.mp4): ")
    video_path_input = video_path_input.strip().strip('"') # 따옴표/공백 자동 제거
    
    if not os.path.exists(video_path_input):
        print(f"\n[오류] 파일을 찾을 수 없습니다: {video_path_input}")
        print("스크립트를 종료합니다.")
        sys.exit()

    # --- [수정된 부분 2] ---
    # 2. 이 영상의 "이름" (폴더명) 입력받기
    print(f"\n파일 확인: {video_path_input}")
    video_name_input = input("이 영상의 '이름'(데이터셋 폴더명)을 입력하세요 (예: night_scene_1): ")
    video_name_input = video_name_input.strip() # 공백 자동 제거

    if not video_name_input:
        print("\n[오류] 폴더 이름이 비어있습니다. 공백이나 특수문자는 피해주세요.")
        print("스크립트를 종료합니다.")
        sys.exit()

    # 3. 최종 저장 경로 조합
    # 예: 'app/data processing/dataset_raw' + 'night_scene_1'
    #  -> 'app/data processing/dataset_raw/night_scene_1'
    final_output_dir = os.path.join(BASE_OUTPUT_DIR, video_name_input)
    # --- [수정 끝] ---

    # 4. 입력받은 경로로 함수 실행
    extract_frames(video_path_input, final_output_dir, SECONDS_PER_FRAME)