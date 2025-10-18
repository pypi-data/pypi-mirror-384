from os import path, mkdir
from shutil import copyfile
import json


class getConfig:
    def __init__(self, file):
        HOMEDIR = getConfigDir()
        filename = file + ".json"
        backupname = file + ".bak"
        if not HOMEDIR:
            raise Exception("Kan configuratie directory niet aanmaken")
        self.filepath = path.join(HOMEDIR, filename)
        self.backup = path.join(HOMEDIR, backupname)

    def __repr__(self):
        return f'ConfigFile(path="{self.filepath}")'

    def save(self, data):
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

    def load(self):
        data = {}
        for file in [self.filepath, self.backup]:
            try:
                if path.isfile(file):
                    with open(file, "r") as json_file:
                        data = json.load(json_file)
            except Exception:
                continue
            return data

    def get(self, key: str = None):
        data = self.load()
        if not key:
            return data
        return data[key] if key in data else {}


def getConfigDir():
    abspath = path.abspath(__file__)
    dname = path.dirname(abspath)
    return dname
