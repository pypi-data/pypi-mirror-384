import os
from shutil import copyfile
import json
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class getConfig:
    def __init__(self, file):
        HOMEDIR = getConfigDir()
        filename = file + ".json"
        backupname = file + ".bak"
        if not HOMEDIR:
            raise Exception("Kan configuratie directory niet aanmaken")
        self.filepath = os.path.join(HOMEDIR, filename)
        self.backup = os.path.join(HOMEDIR, backupname)

    def __repr__(self):
        return f'ConfigFile(path="{self.filepath}")'

    def save(self, data: dict) -> bool:
        logger.debug(f"saving data: {data}")
        try:
            copyfile(self.filepath, self.backup)
        except Exception:
            print("warning - geen datafile")
        try:
            with open(self.filepath, "w") as file:
                json.dump(data, file, indent=2)
        except Exception:
            return False
        return True

    def load(self) -> dict:
        data = {}
        for file in [self.filepath, self.backup]:
            try:
                if os.path.isfile(file):
                    with open(file, "r") as json_file:
                        data = json.load(json_file)
            except Exception:
                continue
            return data

    def get(self, key: str = ""):
        data = self.load()
        if not key:
            return data
        return data[key] if type(data) is dict and key in data else {}


def getConfigDir():
    basepath = os.getcwd()
    configpath = os.path.join(basepath, ".config_zermelo_api")
    if not os.path.isdir(configpath):
        os.mkdir(configpath)
    return configpath
