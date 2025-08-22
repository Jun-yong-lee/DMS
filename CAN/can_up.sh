sudo modprobe can
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000
sudo ip link set can1 type can bitrate 100000
sudo ifconfig can0 up
sudo ifconfig can1 up
# workon dmd
