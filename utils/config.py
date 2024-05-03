import json
import random

api_id = 2040
api_hash = "b18441a1ff607e10a989891a5462e627"
device = "Desktop"
sdk = "Windows 10"
app_version = "4.16.6 x64"
system_lang_pack = "en"
lang_pack = "tdesktop"

squad_uuid = ""

startup_delay = random.randint(5, 30)

def load_config(filename):
    with open(filename, "r") as config_file:
        return json.load(config_file)