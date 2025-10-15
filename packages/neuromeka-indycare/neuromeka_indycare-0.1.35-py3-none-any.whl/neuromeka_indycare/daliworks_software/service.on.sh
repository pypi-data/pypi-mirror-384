#!/bin/bash

filebrowser -a 127.0.0.1 -p 20080 -r / &
gotty --permit-write --reconnect -p 29090 /usr/local/bin/auth.sh &
#mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x360 -f 24" -o "output_http.so -p 23000 -w /usr/local/share/mjpg-streamer/www/" &
