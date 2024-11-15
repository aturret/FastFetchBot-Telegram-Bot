import asyncio
import uuid
from typing import Optional

import httpx
from fake_useragent import UserAgent

from fastfetchbot_telegram_bot.config import HTTP_REQUEST_TIMEOUT
from fastfetchbot_telegram_bot.models.files import NamedBytesIO
from fastfetchbot_telegram_bot.utils.logger import logger
from fastfetchbot_telegram_bot.utils.urlparser import generate_request_url


async def get_url_metadata(url: str, ban_list: Optional[str] = None) -> dict:
    request_url = generate_request_url(path="scraper/getUrlMetadata", params={"url": url, "ban_list": ban_list})
    async with httpx.AsyncClient() as client:
        response = await client.post(request_url)
        return response.json()


async def get_item(url: str, ban_list: Optional[str] = None, **kwargs) -> dict:
    params = {"url": url, "ban_list": ban_list}
    params.update(kwargs)
    request_url = generate_request_url(path="scraper/getItem", params=params)
    async with httpx.AsyncClient() as client:
        response = await client.post(request_url)
        return response.json()


async def download_file_by_metadata_item(
        url: str,
        data: dict,
        file_name: str = None,
        file_format: str = None,
        headers: dict = None,
) -> NamedBytesIO:
    """
    A customized function to download a file from url and return a NamedBytesIO object.
    :param file_format:
    :param data:
    :param url:
    :param file_name:
    :param headers:
    :return:
    """
    try:
        if headers is None:
            headers = HEADERS
        headers["User-Agent"] = get_random_user_agent()
        headers["referer"] = data["url"]
        if data["category"] in ["reddit"]:
            headers["Accept"] = "image/avif,image/webp,*/*"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=url, headers=headers, timeout=HTTP_REQUEST_TIMEOUT
            )
            # if redirect 302, get the final url
            if response.status_code == 302 or response.status_code == 301:
                url = response.headers["Location"]
        file_data = response.content
        if file_name is None:
            file_format = file_format if file_format else url.split(".")[-1]
            file_name = "media-" + str(uuid.uuid1())[:8] + "." + file_format
        io_object = NamedBytesIO(file_data, name=file_name)
        return io_object
    except Exception as e:
        await asyncio.sleep(2)
        logger.error(f"Failed to download {url}, {e}")


def get_random_user_agent() -> str:
    ua = UserAgent()
    return ua.random


"""
default headers
"""

HEADERS = {
    "User-Agent": get_random_user_agent(),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}
