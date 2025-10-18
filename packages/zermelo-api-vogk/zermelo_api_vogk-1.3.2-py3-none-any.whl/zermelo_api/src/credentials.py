from .config import getConfig
import logging

logger = logging.getLogger(__name__)


class Credentials:
    def __init__(self):
        self.file = getConfig("creds")
        self.token = ""
        self.load()

    def load(self):
        self.token = ""
        try:
            data = self.file.load()
            self.token = data["token"]
        except Exception as e:
            logger.error(e)
        finally:
            logger.debug(f"token: {self.token}")
            return True if self.token else False

    def settoken(self, token):
        self.file.save({"token": token})
        self.token = token
