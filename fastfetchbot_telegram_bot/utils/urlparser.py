from urllib.parse import urljoin, urlencode

from fastfetchbot_telegram_bot.config import FASTFETCHBOT_HOST_URL, FASTFETCHBOT_API_KEY

base_params = {
    "pwd": FASTFETCHBOT_API_KEY
}


def generate_request_url(host: str = FASTFETCHBOT_HOST_URL, path: str = "test", params: dict = None) -> str:
    if params:
        params.update(base_params)
    else:
        params = base_params
    query_string = urlencode(params)
    return urljoin(host, f"{path}?{query_string}")