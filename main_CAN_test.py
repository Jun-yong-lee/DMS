from lib2to3.pgen2 import driver
import multiprocessing
from tracemalloc import start
import cantools
import can
import pyaudio
import time
import sys
import pandas as pd
import os
import configparser
from datetime import datetime, timedelta

from config import config

def main():
    from receive_data import receive_CAN_C, receive_CAN_M, receive_audio, WindowClass #, receive_HMI
    from receive_GNSS import receive_GNSS
    from receive_image import receive_realsense
    from check_status import check_driving_cycle, check_velocity, check_driver, check_odometer, check_intention, check_passenger, check_weight
    # from config import config

    # version = config['VERSION']['version']
    # save_path = config['PATH']['SAVE_PATH']
    # driver_list = eval(config['DRIVER']['driver_list'])

    start_time = time.time()

    version = config['VERSION']
    save_flag = config['MEASUREMENT']
    save_path = config['SAVE_PATH']
    driver_list = config['DRIVER_LIST']
    data_config = config['DATA']
    hmi_config = data_config['HMI']

    HMI_flag = config['DATA']['HMI']
    ###  CAN setting  ###
    CAN_flag = config['DATA']['CAN']
    CAN_basePath = os.path.join(save_path, 'dbc')
    C_db = cantools.database.load_file(os.path.join(CAN_basePath, 'C_CAN.dbc'))
    M_db = cantools.database.load_file(os.path.join(CAN_basePath, 'M_CAN.dbc'))
    can_bus_c = can.interface.Bus('can0', bustype='socketcan')
    can_bus_m = can.interface.Bus('can1', bustype='socketcan')
    print_can_status = config['CAN']['print_can_status']
    #####################

    ### START ODOMETRY CHECK ###
    START_ODO = check_odometer(C_db, can_bus_c)

    ### DATASET path setting ###
    if save_flag:
        DATASET_PATH = save_path + 'data/'

        if not os.path.isdir(DATASET_PATH + START_ODO + "_test"):
            os.makedirs(DATASET_PATH + START_ODO + "_test")
        DATASET_PATH += START_ODO + "_test"
    #####################

    P_db = 0


    ### Multi-process setting ###
    procs = []
    stop_event = multiprocessing.Event()
    send_conn, recv_conn = multiprocessing.Pipe()

    data_names = ['CAN_C',
                  'CAN_M',
                  'audio', 
                  ]
    proc_functions = [receive_CAN_C,
                      receive_CAN_M,
                      ]
    func_args = {'CAN_C': (P_db, C_db, can_bus_c, print_can_status),
                'CAN_M': (M_db, can_bus_m, print_can_status),
                }


    print("[INFO] Main thread started.")

    ### Process generation ###
    for d_name, proc_func in zip(data_names, proc_functions):
        if not data_config[d_name]:
            continue
        proc = multiprocessing.Process(target=proc_func, args=(d_name, save_flag, DATASET_PATH, *func_args[d_name], stop_event))
        procs.append(proc)

    for proc in procs:
        proc.start()

    time.sleep(4)

    ### Process terminate ###
    terminate_signal = input("[REQUEST] Press 'Enter' if you want to terminate every processes.\n\n")
    while terminate_signal != '':
        print("[REQUEST] Invalid input! Press 'Enter'")
        terminate_signal = input()

    stop_event.set()

    ### thread terminate double check ###
    for proc in procs:
        proc.join()

    ### END ODOMETRY CHECK ###
    END_ODO = check_odometer(C_db, can_bus_c)
    odo_df = pd.DataFrame([(START_ODO, END_ODO, int(END_ODO) - int(START_ODO), version)], columns=["START", "END", "TOTAL", "VERSION"])
    if save_flag:
        odo_df.to_csv(f"{DATASET_PATH}/START_END_TOTAL_{int(END_ODO) - int(START_ODO)}km.csv")

    end_time = time.time()
    ########## UTC to KST ###########
    start_time = datetime.fromtimestamp(start_time)
    start_time_KST = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = datetime.fromtimestamp(end_time)
    end_time_KST = end_time.strftime('%Y-%m-%d %H:%M:%S')

    # read

    # write (add)

    # save


    ###################################

    print("[INFO] Main process finished.")

    #####################


if __name__ == "__main__":
    # config = configparser.ConfigParser()
    # config.read('./config.ini')
    # from config import config

    main()
