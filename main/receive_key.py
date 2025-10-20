# receive_key_input.py
import os
import time
import pandas as pd
from pynput import keyboard

def receive_key_input(d_name, save_flag, DATASET_PATH, stop_event):
    """
    스페이스바 '한 번의 누름'마다 2행(PRESS, RELEASE) 기록.
    - 파일: DATASET_PATH/key/space_events_YYYY_MM_DD_HH_MM.csv
    - 컬럼: [id, timestamp, event] (동일 id로 PRESS/RELEASE 페어링)
    - 상태 전이 기반: 0->1일 때만 PRESS, 1->0일 때만 RELEASE 기록 (키 자동 반복 방지)
    """
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    # 저장 경로/파일
    key_dir = os.path.join(DATASET_PATH, "key")
    if save_flag:
        os.makedirs(key_dir, exist_ok=True)
    start_str = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
    events_path = os.path.join(key_dir, f"space_events_{start_str}.csv")

    # 헤더
    if save_flag:
        pd.DataFrame(columns=["id", "timestamp", "event"]).to_csv(events_path, index=False)

    # 내부 상태
    space_down = False        # 현재 눌림 상태
    press_id   = 0            # 누름 식별자 (PRESS/RELEASE에 동일 id 부여)
    event_buf  = []           # 버퍼(쓰기 효율/스레드 안전)
    last_flush = time.time()

    # 콜백
    def on_press(key):
        nonlocal space_down, press_id
        if key == keyboard.Key.space:
            # 0 -> 1 전이일 때만 기록 (자동 키반복 방지)
            if not space_down:
                space_down = True
                press_id += 1
                event_buf.append({"id": press_id, "timestamp": time.time(), "event": "PRESS"})

    def on_release(key):
        nonlocal space_down
        if key == keyboard.Key.space:
            # 1 -> 0 전이일 때만 기록
            if space_down:
                space_down = False
                event_buf.append({"id": press_id, "timestamp": time.time(), "event": "RELEASE"})

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    print(f"[INFO] '{d_name}' process starts collecting spacebar PRESS/RELEASE pairs.")
    try:
        while not stop_event.is_set():
            now = time.time()

            # 주기/개수 기반 flush
            if save_flag and (event_buf and ((now - last_flush) >= 0.2 or len(event_buf) >= 20)):
                pd.DataFrame(event_buf).to_csv(events_path, mode="a", header=False, index=False)
                event_buf.clear()
                last_flush = now

            time.sleep(0.05)

    except Exception as e:
        print(f"[ERROR] '{d_name}' exception: {e}")

    finally:
        # 종료 직전에 남은 이벤트 flush
        if save_flag and event_buf:
            pd.DataFrame(event_buf).to_csv(events_path, mode="a", header=False, index=False)
            event_buf.clear()

        # 만약 종료 시점에 아직 누른 상태였다면, 종료 시각을 RELEASE로 보정해 줄 수도 있음 (옵션)
        # if save_flag and space_down:
        #     pd.DataFrame([{"id": press_id, "timestamp": time.time(), "event": "RELEASE"}]) \
        #       .to_csv(events_path, mode="a", header=False, index=False)

        try:
            listener.stop()
        except:
            pass

        print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")