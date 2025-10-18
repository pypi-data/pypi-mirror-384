import aiohttp
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


async def get_json(url: str):
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as response:
            return await response.read()


async def post_request(url: str, data: dict) -> str:
    async with aiohttp.ClientSession() as session:
        response = await session.post(url=url, data=data)
        result = await response.json()
        if "access_token" in result:
            return result["access_token"]
        return ""
