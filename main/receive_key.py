import os
import time
import pandas as pd
from pynput import keyboard

def receive_key_input(d_name, save_flag, DATASET_PATH, stop_event):
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    key_dir = os.path.join(DATASET_PATH, "key")
    if save_flag:
        os.makedirs(key_dir, exist_ok=True)
    start_str = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
    events_path = os.path.join(key_dir, f"space_events_{start_str}.csv")

    if save_flag:
        pd.DataFrame(columns=["id", "timestamp", "event"]).to_csv(events_path, index=False)

    space_down = False
    press_id   = 0
    event_buf  = []
    last_flush = time.time()

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
            if save_flag and (event_buf and ((now - last_flush) >= 0.2 or len(event_buf) >= 20)):
                pd.DataFrame(event_buf).to_csv(events_path, mode="a", header=False, index=False)
                event_buf.clear()
                last_flush = now

            time.sleep(0.05)

    except Exception as e:
        print(f"[ERROR] '{d_name}' exception: {e}")

    finally:
        if save_flag and event_buf:
            pd.DataFrame(event_buf).to_csv(events_path, mode="a", header=False, index=False)
            event_buf.clear()
        try:
            listener.stop()
        except:
            pass

        print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")