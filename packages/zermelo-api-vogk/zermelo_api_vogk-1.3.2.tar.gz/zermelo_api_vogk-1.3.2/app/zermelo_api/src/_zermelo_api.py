from __future__ import annotations
from ._credentials import Credentials
from ._io_json import get_json, post_request
import json
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class NoSchoolNameException(Exception):
    def __init__(self, message: str = ""):
        error = f"no schoolname provided: {message}\n Please import and run installAPI to setup credentials"
        super().__init__(error)


class NoTokenException(Exception):
    def __init__(self, message: str = ""):
        error = f"no token provided: {message}\n Please Please import and run installAPI to setup credentials"
        super().__init__(error)


class WrongCredentialsException(Exception):
    def __init__(self, message: str = ""):
        error = f"wrong token provided: {message}\n Please Please import and run installAPI to setup credentials"
        super().__init__(error)


class ZermeloAPI:
    def __init__(self):
        self.credentials = Credentials()
        try:
            if not self.credentials.schoolname:
                raise NoSchoolNameException("init API")
            self.set_schoolname(self.credentials.schoolname)
            if not self.credentials.token:
                raise NoTokenException("init API")
        except Exception as e:
            logger.exception(e)

    def set_schoolname(self, schoolname: str):
        self.zerurl = f"https://{schoolname}.zportal.nl/api/v3/"

    def update_schoolname(self, schoolname: str):
        if not schoolname:
            raise Exception("No schoolname provided")
        if schoolname == self.credentials.schoolname:
            logger.debug("schoolname is already stored")
            return
        self.credentials.setschoolname(schoolname)
        self.set_schoolname(schoolname)
        self.credentials.settoken("")

    async def login(self, code: str) -> bool:
        token = await self.get_access_token(code)
        return await self.add_token(token)

    async def get_access_token(self, code: str) -> str:
        if not code:
            raise Exception("No Code Provided")
        code = "".join(code.split())
        logger.debug(f"new code {code}")
        url = self.zerurl + f"oauth/token"
        data = {"grant_type": "authorization_code", "code": code}
        return await post_request(url, data)

    async def add_token(self, token: str) -> bool:
        if not token:
            return False
        self.credentials.settoken(token)
        return await self.checkCreds()

    async def checkCreds(self):
        try:
            await self.getName()
            result = True
        except Exception as e:
            logger.error(e)
            result = False
        finally:
            return result

    async def getName(self):
        if not self.credentials.schoolname:
            raise NoSchoolNameException("getName")
        if not self.credentials.token:
            raise NoTokenException("using getName")
        status, data = await self.getData("users/~me", True)
        if status != 200 or type(data) is not list:
            raise WrongCredentialsException("getName")
        logger.debug(f"get name: {data[0]}")
        row = data[0]
        if not row["prefix"]:
            return " ".join([row["firstName"], row["lastName"]])
        else:
            return " ".join([row["firstName"], row["prefix"], row["lastName"]])

    async def getData(
        self, task, from_id=False
    ) -> tuple[int, list[dict] | str | Exception]:
        result = (500, "unknown error")
        request = (
            self.zerurl + task + f"?access_token={self.credentials.token}"
            if from_id
            else self.zerurl + task + f"&access_token={self.credentials.token}"
        )
        logger.debug(request)
        try:
            data1 = await get_json(request)
            json_response = json.loads(data1.decode("utf-8"))
            if json_response:
                json_status = json_response["response"]["status"]
                if json_status == 200:
                    result = (200, json_response["response"]["data"])
                    logger.debug("    **** JSON OK ****")
                else:
                    logger.debug(f"oeps, geen juiste response: {task}")
                    result = (json_status, json_response["response"])
            else:
                logger.error("JSON - response is leeg")
        except Exception as e:
            logger.exception(e)
            result = (500, e)
        finally:
            return result

    async def load_query(self, query: str) -> list[dict]:
        try:
            status, data = await self.getData(query)
            if status != 200 or type(data) is not list:
                raise Exception(f"Error loading data {status}, {data}")
            if not data:
                logger.debug("no data")
            return data
        except Exception as e:
            logger.debug(e)
            return []


zermelo = ZermeloAPI()


async def loadAPI(schoolname: str = "") -> ZermeloAPI:
    try:
        if schoolname:
            zermelo.update_schoolname(schoolname)
        if not await zermelo.checkCreds():
            logger.warning(
                "credentials not set up properly. Please import and run: installAPI()"
            )
    except Exception as e:
        logger.exception(e)
    finally:
        return zermelo
