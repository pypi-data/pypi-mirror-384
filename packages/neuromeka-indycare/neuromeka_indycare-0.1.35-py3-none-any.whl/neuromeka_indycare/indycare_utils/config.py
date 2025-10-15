import os
import yaml
from os import path as op
from cryptography.fernet import Fernet

INDY_CARE_CONFIG_FILE = op.join(op.abspath(op.dirname(__file__)), "config.yml")
INDY_CARE_CONFK_FILE = op.join(op.abspath(op.dirname(__file__)), ".inc_confk")

SERIAL_STRING = b"gAAAAABnvrJXD3wz0VskUmR1dNVGAssRqUT7CMj-z6XNHtjLD0PtMkbvsDkb_upTaia5hVQ6jeHnG48k3wLo0dQ5vBuO5Qkaa0Jt25K8EM6q-lHHayRMmCc6-ZMulajwnCznZetHeqnUBeDM_U-QtyhlEzZp5RAh0VHsQRgWtJSqnV5hzeJQNjwTR6cHMvTHqWJG839AbQ2TOJBepIHpFDgBrReEgnZvJRd4KrRxWHTWhJrI9LBxDAbNH0h8hT25drBb8FjKUaF_D-pJu5blqNmqnfo_Jlbt7MibjAf7gtIDzEX7JGosKGsu6Q5UFf9ML6HCxcNQdJ3Ug01hYi7giRpcfWsPYAUXKDqoXGuk5WUGJqJn_G4dz3yinL_d73sURaQS6JEIqawTCsn5hW4Etefk-y88pJg20xS9WGcEg4uqs2TOaYGshxQ-Frc2MeEix30v-o204r5y"

def load_config() -> dict:
    try:
        with open(INDY_CARE_CONFIG_FILE, "r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            if data["rtsp"]:
                data["rtsp"] = f'{data["rtsp_url"]}'
            else:
                pass
            print("Load IndyCARE configuration file")
        with open(INDY_CARE_CONFK_FILE, 'rb') as f:
            conf_k = f.read()
        # conf_k = os.getenv("IDC_CONFK")        
        if not conf_k:
            raise ValueError("IDC_CONFK not found!")
        cipher = Fernet(conf_k)
        addition_config = yaml.safe_load(cipher.decrypt(SERIAL_STRING))
        data.update(addition_config)
    except:
        print("Cannot load yaml config!!!")
        
    return data

# print(load_config())
