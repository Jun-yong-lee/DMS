sudo modprobe can
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000 # C-CAN
sudo ip link set can2 type can bitrate 100000 # M-CAN
sudo ifconfig can0 up
sudo ifconfig can2 up
# workon dmd
