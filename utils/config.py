import json


def load_config(filename):
    with open(filename, "r") as config_file:
        return json.load(config_file)