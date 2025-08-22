import os
import time
import pandas as pd
import cantools
import can


def receive_CAN_test(db, can_bus, save_path, save_flag=True, print_status=False, stop_event=None,
                  msg_list=None, signal_names=None):
    """
    실제 환경에서 CAN 신호를 받아와 csv로 저장하는 테스트 함수
    """
    msg_list = msg_list if msg_list else []
    signal_names = signal_names if signal_names else []

    CAN_PATH = os.path.join(save_path, 'CAN')
    if save_flag and not os.path.isdir(CAN_PATH):
        os.makedirs(CAN_PATH)

    db_msg = []
    for msg in db.messages:
        if msg.name in msg_list:
            db_msg.append(msg)

    timestamp_cols = ['timestamp', 'timestamp2']
    all_columns = signal_names + timestamp_cols
    df = pd.DataFrame(columns=all_columns)

    cnt = 0
    first = True
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    print(f"[INFO] CAN 수집 시작 ({start_time})")

    try:
        while True:
            can_msg = can_bus.recv()
            timestamp2 = time.time()
            for msg in db_msg:
                if can_msg.arbitration_id == msg.frame_id:
                    can_dict = db.decode_message(can_msg.arbitration_id, can_msg.data)
                    row = {k: can_dict.get(k, None) for k in signal_names}
                    row['timestamp'] = can_msg.timestamp
                    row['timestamp2'] = timestamp2
                    df = df.append(row, ignore_index=True)
                    cnt += 1

                    if print_status:
                        print(f"[{cnt}] {row}")

                    # 100개마다 저장 (필요시 조정)
                    if len(df) >= 100:
                        if save_flag:
                            if first:
                                df.to_csv(os.path.join(CAN_PATH, f"{start_time}_test.csv"), index=False)
                                first = False
                            else:
                                df.to_csv(os.path.join(CAN_PATH, f"{start_time}_test.csv"), mode='a', header=False, index=False)
                        df = df[0:0]

            if stop_event is not None and stop_event.is_set():
                break

    except KeyboardInterrupt:
        print("[INFO] 수집 중단 (KeyboardInterrupt)")
    except Exception as e:
        print(f"[ERROR] {e}")

    # 남은 데이터 저장
    if save_flag and not df.empty:
        if first:
            df.to_csv(os.path.join(CAN_PATH, f"{start_time}_test.csv"), index=False)
        else:
            df.to_csv(os.path.join(CAN_PATH, f"{start_time}_test.csv"), mode='a', header=False, index=False)

    print(f"[INFO] CAN 수집 종료, 총 {cnt}개 프레임 저장됨.")

if __name__ == "__main__":
    save_path = os.path.join("media", "imlab", "Samsung_T5", "dms_rev1")
    CAN_basePath = os.path.join(save_path, 'dbc')
    M_db = cantools.database.load_file(os.path.join(CAN_basePath, 'M_CAN.dbc'))

    can_bus_m = can.interface.Bus('can1', bustype='socketcan')

    msg_list = ['CLU_HU_PE_01', 'HU_CLU_PE_05', 'HU_CLU_PE_06',
                'GW_IPM_PE_2', 'TP_HU_FM_CLU', 'HU_Car_PE_01',
                'TP_HU_CLU_HF', 'HU_DATC_PE_00']

    signal_names = ['HU_VolumeStatus', 'C_DRVUnlockState', 'Byte0_TCP_4E8',
                    'HU_VehiclePwr', 'Byte0_TCP_485', 'HU_PhoneActivity',
                    'Clu_RheostatLvl']

    save_flag = True

    # 함수 호출
    receive_CAN_test(M_db, can_bus_m, save_path, save_flag=save_flag, print_status=True, msg_list=msg_list, signal_names=signal_names)