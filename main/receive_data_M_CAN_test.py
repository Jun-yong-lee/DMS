import os
import time
import pandas as pd
import cantools
import can
from config import config


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
    df = pd.DataFrame(columns=timestamp_cols)

    cnt = 0
    first = True
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    print(f"[INFO] CAN 수집 시작 ({start_time})")

    while(True):
        try:
            can_msg = can_bus.recv()
            timestamp2 = time.time()
            for msg in db_msg:
                if can_msg.arbitration_id == msg.frame_id:
                    can_dict = db.decode_message(can_msg.arbitration_id, can_msg.data)
                    # row = {k: can_dict.get(k, None) for k in signal_names}
                    can_dict = {k: v for k, v in can_dict.items() if k in signal_names}
                    can_dict['timestamp'] = can_msg.timestamp
                    can_dict['timestamp2'] = timestamp2

                    if len(df.columns) >= len(signal_names) + len(timestamp_cols):
                        if save_flag:
                            if first:
                                df.to_csv(CAN_PATH + f"{start_time}_test.csv", index=False)
                                first = False
                            else:
                                df.to_csv(CAN_PATH + f"{start_time}_test.csv", mode='a', header=False, index=False)

                        cnt += 1
                        df = df[0:0]
                        df = df.append(can_dict, ignore_index=True)
                    else:
                        cnt += 1
                        df = df.append(can_dict, ignore_index=True)

            # if stop_event is not None and stop_event.is_set():
            #     break

        except KeyboardInterrupt:
            print("[INFO] 수집 중단 (KeyboardInterrupt)")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            break

    # # 남은 데이터 저장
    # if save_flag and not df.empty:
    #     if first:
    #         df.to_csv(os.path.join(CAN_PATH, f"{start_time}_test.csv"), index=False)
    #     else:
    #         df.to_csv(os.path.join(CAN_PATH, f"{start_time}_test.csv"), mode='a', header=False, index=False)

    print(f"[INFO] CAN 수집 종료, 총 {cnt}개 프레임 저장됨.")

if __name__ == "__main__":
    can_name = "C" # "C"
    save_path = config['SAVE_PATH']

    if can_name == "M":
        save_path = save_path
        CAN_basePath = os.path.join(save_path, 'dbc')
        M_db = cantools.database.load_file(os.path.join(CAN_basePath, 'M_CAN.dbc'))

        can_bus_m = can.interface.Bus('can2', bustype='socketcan')

        msg_list = ['CLU_HU_PE_01',
                    'HU_Car_PE_01',

                    'HU_CLU_PE_05',
                    'GW_IPM_PE_2',
                    'HU_DATC_PE_00',

                    # 'TP_HU_FM_CLU',
                    # 'TP_HU_CLU_HF'
                    ]

        signal_names = ['Clu_RheostatLvl',
                        'HU_VehiclePwr',
                        'HU_VolumeStatus',
                        'C_DRVUnlockState',
                        'HU_PhoneActivity',
            # 'Byte0_TCP_485', 'Byte0_TCP_4E8'
            ]

        save_flag = True

        # 함수 호출
        receive_CAN_test(M_db, can_bus_m, save_path, save_flag=save_flag, print_status=True, msg_list=msg_list, signal_names=signal_names)
        
    elif can_name == "C":
        save_path = save_path
        CAN_basePath = os.path.join(save_path, 'dbc')
        C_db = cantools.database.load_file(os.path.join(CAN_basePath, 'C_CAN.dbc'))

        can_bus_c = can.interface.Bus('can0', bustype='socketcan')

        msg_list = ['HEV_PC1', 'HEV_PC2', 'HEV_PC4',
                    'HEV_PC5','HEV_PC6', 'HEV_PC12',
                    'SAS11', 'ESP12', 'WHL_SPD11',
                    'CGW1', 'CLU12', 'CLU15',
                    'DATC3',
                    'CGW4', 'TCS15',
                    'BCW11'
                    ]
        
        signal_names = ['CF_Ems_EngStat', 'CR_Brk_StkDep_Pc', 'CR_Ems_AccPedDep_Pc',
                        'CR_Ems_EngSpd_rpm', 'CR_Ems_FueCon_uL', 'CR_Ems_VehSpd_Kmh',
                        'CF_Tcu_TarGe', 'SAS_Angle', 'CYL_PRES',
                        'CYL_PRES_FLAG', 'LAT_ACCEL', 'LONG_ACCEL',
                        'YAW_RATE', 'WHL_SPD_FL', 'WHL_SPD_FR',
                        'WHL_SPD_RL', 'WHL_SPD_RR', 'BAT_SOC',
                        'CF_Gway_HeadLampHigh', 'CF_Gway_HeadLampLow', 'CR_Hcu_HigFueEff_Pc',
                        'CR_Hcu_NorFueEff_Pc', 'CF_Hcu_DriveMode', 'CR_Fatc_OutTempSns_C',
                        'CR_Hcu_EcoLvl', 'CR_Hcu_FuelEco_MPG', 'CR_Hcu_HevMod',
                        'CF_Ems_BrkForAct', 'CR_Ems_EngColTemp_C', 'CF_Clu_InhibitD',
                        'CF_Clu_InhibitN', 'CF_Clu_InhibitP', 'CF_Clu_InhibitR',
                        'CF_Clu_VehicleSpeed', 'CF_Clu_Odometer', 'CF_Gway_TSigLHSw', 'CF_Gway_TSigRHSw',
                        # latest added signals
                        'CF_Datc_TempDispUnit',
                        'CF_Gway_HazardSw', 'CF_Gway_WiperSwState', 'CF_Gway_WiperIntT', 'CF_Gway_WiperIntSw', 'CF_Gway_WiperLowSw', \
                        'CF_Gway_WiperHighSw', 'CF_Gway_WiperAutoSw', 'CF_Gway_DrvSeatBeltSw', 'ESC_Off_Step', 'CF_BCW_Stat', 'CF_Gway_HoodSw'
                        ]

        save_flag = True

        # 함수 호출
        receive_CAN_test(C_db, can_bus_c, save_path, save_flag=save_flag, print_status=True, msg_list=msg_list, signal_names=signal_names)
    else:
        print("Invalid CAN name. Please use 'M' or 'C'.")