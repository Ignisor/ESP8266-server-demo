#!/bin/bash

sudo ../env/bin/esptool.py --port /dev/ttyUSB0 erase_flash
sudo ../env/bin/esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 $1

