#!/bin/bash

while true
do
    cd /home/baby/
    /home/baby/make_dirs.sh

    cd /home/baby/picam

    # Get Microphone Alsa-Card-No
    MICROPHONE_ALSA_ID=$(arecord -l|grep card|head -n1|cut -d':' -f1|cut -d' ' -f2)

    # Select tuning-file for no-IR camera.
    LIBCAMERA_RPI_TUNING_FILE=/usr/share/libcamera/ipa/rpi/vc4/ov5647_noir.json ./picam -w 1280 -h 720 -o /picam/hls --alsadev hw:${MICROPHONE_ALSA_ID},0 --vfr --autoex --time --avcprofile main --avclevel 3.1 -v 2500000 --hlsnumberofsegments 5 --maxfps 18
done

