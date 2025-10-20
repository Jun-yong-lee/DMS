# receive_key_input.py
import os
import time
import pandas as pd
from pynput import keyboard

def receive_key_input(d_name, save_flag, DATASET_PATH, stop_event):
    """
    스페이스바 PRESS / RELEASE 이벤트를 기록하는 프로세스
    - 저장 파일: DATASET_PATH/key/space_events_YYYY_MM_DD_HH_MM.csv
    - 컬럼: [timestamp, event]  (event = PRESS 또는 RELEASE)
    """
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    # 저장 경로
    KEY_PATH = os.path.join(DATASET_PATH, 'key')
    if save_flag:
        os.makedirs(KEY_PATH, exist_ok=True)

    start_time_str = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    events_path = os.path.join(KEY_PATH, f"space_events_{start_time_str}.csv")

    # CSV 헤더 생성
    if save_flag:
        pd.DataFrame(columns=['timestamp', 'event']).to_csv(events_path, index=False)

    # 이벤트 버퍼 (쓰기 효율을 위해)
    event_buffer = []
    last_write_time = time.time()

    # 콜백 함수
    def on_press(key):
        if key == keyboard.Key.space:
            event_buffer.append({'timestamp': time.time(), 'event': 'PRESS'})

    def on_release(key):
        if key == keyboard.Key.space:
            event_buffer.append({'timestamp': time.time(), 'event': 'RELEASE'})

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    print(f"[INFO] '{d_name}' process starts collecting spacebar events.")
    try:
        while not stop_event.is_set():
            now = time.time()

            # 버퍼가 일정량 쌓이거나 0.2초 경과 시 기록
            if save_flag and ((now - last_write_time) > 0.2 or len(event_buffer) >= 20):
                if event_buffer:
                    pd.DataFrame(event_buffer).to_csv(events_path, mode='a', header=False, index=False)
                    event_buffer.clear()
                last_write_time = now

            time.sleep(0.05)

    except Exception as e:
        print(f"[ERROR] '{d_name}' exception: {e}")
    finally:
        # 종료 시 버퍼 남은 데이터 저장
        if save_flag and event_buffer:
            pd.DataFrame(event_buffer).to_csv(events_path, mode='a', header=False, index=False)
        try:
            listener.stop()
        except:
            pass
        print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")