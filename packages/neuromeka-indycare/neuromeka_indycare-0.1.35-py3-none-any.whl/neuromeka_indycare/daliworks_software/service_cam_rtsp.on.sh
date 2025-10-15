#!/bin/bash

#filebrowser -a 127.0.0.1 -p 20080 -r / &
#gotty --permit-write --reconnect -p 29090 /usr/local/bin/auth.sh &

function parse_yaml() {

  local prefix=$2
  local s='[[:space:]]*'
  local w='[a-zA-Z0-9_\-]*'
  local fs=$(echo @ | tr @ '\034')

  sed "h;s/^[^:]*//;x;s/:.*$//;y/-/_/;G;s/\n//" $1 |
    sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
      -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" |
    awk -F$fs '{
    indent = length($1)/2;
    vname[indent] = $2;

    for (i in vname) {if (i > indent) {delete vname[i]}}
    if (length($3) > 0) {
        vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
        printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
    }
  }'
}

# Read YAML file
YAML_FILE="./../indycare_utils/config.yml"
eval $(parse_yaml $YAML_FILE)

# input_stream="rtsp://$rtsp_id:$rtsp_pw@$rtsp_ip:$rtsp_port/stream_ch00_$rtsp_quality"
input_stream="$rtsp_url"

# Kill running processes
kill $(lsof -t -i:23000) 2> /dev/null
kill $(lsof -t -i:"$rtsp_port") 2> /dev/null

mkdir /tmp/stream/
rm -f /tmp/stream/*
crontab -l > mycron
sed -i '/delete_old_files/d' mycron
crontab mycron
rm mycron

sleep 1

# Start ffmpeg
sudo ffmpeg -rtsp_transport tcp -threads 0 -i "$input_stream" -r $rtsp_streaming_fps -q:v 1 -s 640x400 -an -y /tmp/stream/frame%03d.jpg &

sudo mjpg_streamer -i "input_file.so -f /tmp/stream -d 0.01" -o "output_http.so -p 23000 -w /usr/local/share/mjpg-streamer/www/" &

# Create a script to delete old files
cat << EOF > ~/delete_old_files.sh
#!/bin/bash
find /tmp/stream -name "frame*.jpg" -type f -mmin +1 -delete
EOF

# Make the script executable
chmod +x ~/delete_old_files.sh

# Add a cron job to delete old files every minute
# This assumes the current user has permission to use crontab. If not, you may need to use sudo.
(crontab -l 2>/dev/null; echo "* * * * * ~/delete_old_files.sh") | crontab -