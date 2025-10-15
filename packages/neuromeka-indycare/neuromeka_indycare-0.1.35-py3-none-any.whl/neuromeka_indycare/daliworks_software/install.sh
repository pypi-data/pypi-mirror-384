#!/bin/bash

echo ' '
echo '=========== Start DALIWORKS Settings ============'

sudo apt-get -f install -y curl
sudo apt-get -f install -y git

chmod +755 lt mjpg_streamer auth.sh ffmpeg
chmod +x domain.on.sh
chmod +x service.on.sh
chmod +x service_cam.on.sh
chmod +x service_cam_rtsp.on.sh
#chmod +x daliworks_service_autorun.sh
chmod +x kill_process.sh

##### Local Tunnel #####
echo 'Start Tunnel Setting'
cp lt /usr/local/bin
echo 'End Tunnel Setting'

##### File Browser #####
echo 'Start File Browser Setting'
curl -fsSL https://gitlab.com/daliworks/thingplus-public/filebrowser/-/raw/master/get/get.sh | bash
echo 'End File Browser Setting'

##### Gotty #####
echo 'Start Terminal Setting'
curl -fsSL https://gitlab.com/daliworks/thingplus-public/gotty/-/raw/master/get/get.sh | bash
cp auth.sh /usr/local/bin
echo 'End Terminal Setting'

##### MJPG Streamer #####
echo 'Start MJPG Streamer Setting'
cp mjpg_streamer /usr/local/bin
cp -r mjpg-streamer-share /usr/local/share/mjpg-streamer
cp -r mjpg-streamer-lib /usr/local/lib/mjpg-streamer
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib:/usr/local/lib/mjpg-streamer" | tee -a /etc/profile
echo 'End MJPG Streamer Setting'

##### ffmpeg #####
echo 'Start ffmpeg Setting'
cp ffmpeg /usr/local/bin
cp -r ffmpeg-share /usr/local/share/ffmpeg
echo 'End ffmpeg Setting'

echo '=========== End DALIWORKS Settings =============='
echo ' '
