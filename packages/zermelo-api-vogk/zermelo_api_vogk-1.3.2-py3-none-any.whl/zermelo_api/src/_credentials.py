from ._config import getConfig
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class Credentials:
    def __init__(self):
        self.file = getConfig("creds")
        self.schoolname = ""
        self.token = ""
        self.load()

    def load(self):
        try:
            data = self.file.load()
            self.schoolname = data["schoolname"]
            self.token = data["token"]
        except Exception as e:
            logger.error(e)
        finally:
            logger.debug(f"schoolname: {self.schoolname}")
            logger.debug(f"token: {self.token}")

    def check(self) -> bool:
        if self.schoolname and self.token:
            return True
        return False

    def save(self):
        data = {}
        if self.schoolname:
            data["schoolname"] = self.schoolname
        if self.token:
            data["token"] = self.token
        self.file.save(data)

    def setschoolname(self, schoolname: str):
        logger.debug(f"setting schoolname: {schoolname}")
        self.schoolname = schoolname
        self.save()

    def settoken(self, token: str):
        logger.debug(f"setting token: {token}")
        self.token = token
        self.save()
