from urllib.parse import urljoin, urlparse, urlencode

from config import FASTFETCH_BOT_URL, FASTFETCH_BOT_API_KEY

base_params = {
    "pwd": FASTFETCH_BOT_API_KEY
}


def generate_request_url(host: str = FASTFETCH_BOT_URL, path: str = "test", params: dict = None) -> str:
    if params:
        params.update(base_params)
    else:
        params = base_params
    query_string = urlencode(params)
    return urljoin(host, f"{path}?{query_string}")