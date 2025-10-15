import argparse
import subprocess
import os
import yaml
from collections import OrderedDict
from datetime import datetime

package_dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(package_dir, 'indycare_utils', 'config.yml')
confk_file_path = os.path.join(package_dir, 'indycare_utils', '.inc_confk')
v3_dummy_path = '/home/user/release/IndyDeployment/IndyCAREReport'
v2_dummy_path = '/home/user/release/IndyCAREReporter/'

daliworks_script_path = os.path.join(package_dir, 'daliworks_software')
install_script_path = os.path.join(package_dir, 'daliworks_software', 'install.sh')
mjpg_streamer_share_path = os.path.join(package_dir, 'daliworks_software', 'mjpg-streamer-share')
mjpg_streamer_lib_path = os.path.join(package_dir, 'daliworks_software', 'mjpg-streamer-lib')
ffmpeg_share_path = os.path.join(package_dir, 'daliworks_software', 'ffmpeg-share')


class CustomDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(CustomDumper, self).increase_indent(flow, indentless)

    def represent_list(self, data):
        if len(data) == 1:
            return self.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
        return super(CustomDumper, self).represent_list(data)

    def represent_scalar(self, tag, value, style=None):
        if tag == 'tag:yaml.org,2002:str' and ':' in value:
            style = '"'
        return super(CustomDumper, self).represent_scalar(tag, value, style)

CustomDumper.add_representer(list, CustomDumper.represent_list)


def run_command(command, description=""):
    print(f"Running: {description}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    # result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error message: {result.stderr}")
    else:
        print(f"Success: {description}")
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Configure IndyCare settings.")
    parser.add_argument('--passwd', required=True, help='Password for sudo commands')
    parser.add_argument('--device_id', required=True, help='Device ID registered with Daliworks')

    args = parser.parse_args()

    passwd = args.passwd
    device_id = args.device_id
    robot_sn = input("Enter robot_sn: ")
    
    # Add robot DOF input
    while True:
        robot_dof = input("Enter robot DOF: ")
        if robot_dof in ["6", "7", "8", "9", "10", "11", "12", "13", "14"]:
            robot_dof = int(robot_dof)
            break
        else:
            print("Robot DOF invalid (6-14). Please try again.")
    
    camera_choice = input("Enter Camera options (1: None/USB Camera, 2: C200/C200E, 3: C300): ")
    
    while True:
        FW_version = input("Enter FW version(2: FW 2.x, 3: FW 3.x): ")
        if FW_version == "2" or FW_version == "3":
            break
        else:
            print("FW_version value must be either '2' or '3'")


    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)    # IndyCARE installation date
    config['indycare_installation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    config['mqtt_device_id'] = device_id
    config['robot_sn'] = robot_sn
    config['robot_dof'] = robot_dof
    if FW_version == "2":
        config['FW_version'] = "v2"
    elif FW_version == "3":
        config['FW_version'] = "v3"

    if camera_choice == "1":  # None or USB Camera
        config['rtsp'] = False
        config['rtsp_url'] = "rtsp://admin:nrmk2013@192.168.20.5/stream1"
        config['rtsp_streaming_fps'] = 20
    elif camera_choice == "2":  # C200 or C200E
        config['rtsp'] = True
        rtsp_id = input("Enter RTSP ID: ")
        rtsp_pw = input("Enter RTSP Password: ")
        rtsp_ip = input("Enter RTSP IP: ")
        config['rtsp_url'] = f"rtsp://{rtsp_id}:{rtsp_pw}@{rtsp_ip}/stream1"
        config['rtsp_streaming_fps'] = 20
    elif camera_choice == "3":  # C300
        config['rtsp'] = True
        rtsp_pw = input("Enter RTSP Password: ")
        rtsp_ip = input("Enter RTSP IP: ")
        config['rtsp_url'] = f"rtsp://admin:{rtsp_pw}@{rtsp_ip}/stream1"
        config['rtsp_streaming_fps'] = 10
    else:
        print("Invalid camera choice.")
        return

    with open(config_file_path, 'w') as file:
        # yaml.dump(config, file, default_flow_style=False, Dumper=CustomDumper)
        yaml.dump(config, file, default_flow_style=False, sort_keys=False, Dumper=CustomDumper)

    # Disable lsb_release if exists
    # file = '/usr/bin/lsb_release'
    # if os.path.exists(file):
    #     run_command(f'sed -i "s/^#!/##!/" {file}', "Disable lsb_release")

    # Disable old IndyCare gstream
    files_to_backup = [
        '/usr/sbin/nrmkscm.sh',
        '/usr/sbin/nrmkbox',
        '/usr/sbin/gstvideo',
        '/usr/bin/nrmkscm.sh',
        '/usr/bin/nrmkbox',
        '/usr/bin/gstvideo',
        '/home/user/release/IndyDeployment/IndyCAREReport',
        '/home/user/release/IndyCAREReporter'
    ]

    for file in files_to_backup:
        if os.path.exists(file):
            run_command(f'echo {passwd} | sudo -S -k mv {file} {file}.bk', f"Backup {file}")
        else:
            print(f"File not found, skipping: {file}")

    # Convert config to unix file
    run_command(f'echo {passwd} | sudo -S -k apt-get install dos2unix', "Install dos2unix")
    run_command(f'echo {passwd} | sudo -S -k dos2unix {config_file_path}', "Convert config.yml to Unix format")
    run_command(f'echo {passwd} | sudo -S -k chmod 600 {confk_file_path}')

    # Install Daliworks software
    daliworks_files = [
        'lt',
        'mjpg_streamer',
        'auth.sh',
        'ffmpeg',
        'domain.on.sh',
        'service.on.sh',
        'service_cam.on.sh',
        'service_cam_rtsp.on.sh',
        'kill_process.sh',
        'install.sh'
    ]

    for file in daliworks_files:
        file_path = os.path.join(package_dir, 'daliworks_software', file)
        if os.path.exists(file_path):
            run_command(f'echo {passwd} | sudo -S -k chmod +x {file_path}', f"Set execute permission for {file_path}")
        else:
            print(f"File not found, skipping: {file_path}")

    if os.path.exists(install_script_path):
        run_command(f'echo {passwd} | sudo -S -k chmod +x {install_script_path}', "Set execute permission for install script")
        run_command(f'echo {passwd} | sudo -S -k find {daliworks_script_path} -type f -exec dos2unix {{}} +', "Convert all files in daliworks_software to Unix format")
        # run_command(f'echo {passwd} | sudo -S -k dos2unix {install_script_path}', "Convert install.sh to Unix format")
        run_command(f'echo {passwd} | sudo -S -k {install_script_path}', "Run Daliworks install script")
    else:
        print(f"Install script not found: {install_script_path}")

    if FW_version == '3':
        run_command(f'echo {passwd} | sudo -S -k mkdir -p {v3_dummy_path}', "Create dummy directory")
        run_command(f'echo {passwd} | sudo -S -k touch {v3_dummy_path}/IndyCAREReporter.py', "Create dummy IndyCAREReporter.py")
        run_command(f'echo {passwd} | echo \'import subprocess\nsubprocess.run("run_indycare")\' | sudo -S tee {v3_dummy_path}/IndyCAREReporter.py', "Write content to IndyCAREReporter.py")
    else: # 2
        run_command(f'echo {passwd} | sudo -S -k mkdir -p {v2_dummy_path}', "Create dummy directory")
        run_command(f'echo {passwd} | sudo -S -k touch {v2_dummy_path}/IndyCAREReporter.py', "Create dummy IndyCAREReporter.py")
        run_command(f'echo {passwd} | echo \'import subprocess\nsubprocess.run("run_indycare")\' | sudo -S tee {v2_dummy_path}/IndyCAREReporter.py', "Write content to IndyCAREReporter.py")

    item_list = ['lt', 'auth.sh', 'mjpg_streamer', 'ffmpeg']
    for item in item_list:
        item_path = os.path.join(package_dir, 'daliworks_software', item)
        run_command(f'echo {passwd} | cp {item_path} /usr/local/bin/', f"install {item} to /usr/local/bin")
    
    run_command(f'echo {passwd} | cp -r {mjpg_streamer_share_path} /usr/local/share/mjpg-streamer', f"install mjpg-streamer-share to /usr/local/share/mjpg-streamer")
    run_command(f'echo {passwd} | cp -r {mjpg_streamer_lib_path} /usr/local/lib/mjpg-streamer', f"install mjpg-streamer-lib to /usr/local/lib/mjpg-streamer")
    run_command(f'echo {passwd} | cp -r {ffmpeg_share_path} /usr/local/share/ffmpeg/', f"install ffmpeg-share to /usr/local/share/ffmpeg")
    
    print('Installation completed. Please reboot the computer.')
    

if __name__ == "__main__":
    main()
