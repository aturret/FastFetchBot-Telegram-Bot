import os
import secrets

from jinja2 import Environment, FileSystemLoader

env = os.environ
current_directory = os.path.dirname(os.path.abspath(__file__))

# logger
LOG_FILE_PATH = env.get("LOG_FILE_PATH", "/tmp")
LOG_LEVEL = env.get("LOG_LEVEL", "DEBUG")

# telegram bot
TELEGRAM_BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN", None)

TELEGRAM_CHANNEL_ID = []
telegram_channel_id = env.get("TELEGRAM_CHANNEL_ID", "").split(",")
for single_telegram_channel_id in telegram_channel_id:
    if single_telegram_channel_id.startswith("@"):
        TELEGRAM_CHANNEL_ID.append(single_telegram_channel_id)
    elif single_telegram_channel_id.startswith("-1"):
        TELEGRAM_CHANNEL_ID.append(int(single_telegram_channel_id))
if len(TELEGRAM_CHANNEL_ID) == 0:
    TELEGRAM_CHANNEL_ID = None
telebot_debug_channel = env.get("TELEBOT_DEBUG_CHANNEL", "")
if telebot_debug_channel.startswith("@"):
    TELEBOT_DEBUG_CHANNEL = telebot_debug_channel
elif telebot_debug_channel.startswith("-1"):
    TELEBOT_DEBUG_CHANNEL = int(telebot_debug_channel)
else:
    TELEBOT_DEBUG_CHANNEL = None
telegram_channel_admin_list = env.get("TELEGRAM_CHANNEL_ADMIN_LIST", "")
TELEGRAM_CHANNEL_ADMIN_LIST = [
    admin_id for admin_id in telegram_channel_admin_list.split(",")
]
if not TELEGRAM_CHANNEL_ADMIN_LIST:
    TELEGRAM_CHANNEL_ADMIN_LIST = None

TELEGRAM_TEXT_LIMIT = int(env.get("TELEGRAM_TEXT_LIMIT", 900)) or 900

TELEBOT_API_SERVER_HOST = env.get("TELEBOT_API_SERVER_HOST", None)
TELEBOT_API_SERVER_PORT = env.get("TELEBOT_API_SERVER_PORT", None)
TELEBOT_API_SERVER = (
    f"http://{TELEBOT_API_SERVER_HOST}:{TELEBOT_API_SERVER_PORT}" + "/bot"
    if (TELEBOT_API_SERVER_HOST and TELEBOT_API_SERVER_PORT)
    else "https://api.telegram.org/bot"
)
TELEBOT_API_SERVER_FILE = (
    f"http://{TELEBOT_API_SERVER_HOST}:{TELEBOT_API_SERVER_PORT}" + "/file/bot"
    if (TELEBOT_API_SERVER_HOST and TELEBOT_API_SERVER_PORT)
    else "https://api.telegram.org/file/bot"
)
TELEBOT_LOCAL_FILE_MODE = (
    False if TELEBOT_API_SERVER == "https://api.telegram.org/bot" else True
)
TELEBOT_CONNECT_TIMEOUT = int(env.get("TELEGRAM_CONNECT_TIMEOUT", 15)) or 15
TELEBOT_READ_TIMEOUT = int(env.get("TELEGRAM_READ_TIMEOUT", 60)) or 60
TELEBOT_WRITE_TIMEOUT = int(env.get("TELEGRAM_WRITE_TIMEOUT", 60)) or 60
TELEBOT_MAX_RETRY = int(env.get("TELEGRAM_MAX_RETRY", 5)) or 5
TELEGRAM_IMAGE_DIMENSION_LIMIT = int(env.get("TELEGRAM_IMAGE_SIZE_LIMIT", 1600)) or 1600
TELEGRAM_IMAGE_SIZE_LIMIT = (
    int(env.get("TELEGRAM_IMAGE_SIZE_LIMIT", 5242880)) or 5242880
)
TELEGRAM_SINGLE_MESSAGE_MEDIA_LIMIT = int(env.get("TELEGRAM_SINGLE_MESSAGE_MEDIA_LIMIT", 10)) or 10
TELEGRAM_FILE_UPLOAD_LIMIT = 52428800  # 50MB
TELEGRAM_FILE_UPLOAD_LIMIT_LOCAL_API = 2147483648  # 2GB

telegram_group_message_ban_list = env.get("TELEGRAM_GROUP_MESSAGE_BAN_LIST", "")
telegram_bot_message_ban_list = env.get("TELEGRAM_BOT_MESSAGE_BAN_LIST", "")


def ban_list_resolver(ban_list_string: str) -> list:
    ban_list = ban_list_string.split(",")
    for item in ban_list:
        if item == "social_media":
            ban_list.extend(
                [
                    "weibo",
                    "twitter",
                    "instagram",
                    "zhihu",
                    "douban",
                    "wechat",
                    "xiaohongshu",
                    "reddit",
                ]
            )
        elif item == "video":
            ban_list.extend(["youtube", "bilibili"])
    return ban_list


TELEGRAM_GROUP_MESSAGE_BAN_LIST = ban_list_resolver(telegram_group_message_ban_list)
TELEGRAM_BOT_MESSAGE_BAN_LIST = ban_list_resolver(telegram_bot_message_ban_list)

# fastfetch bot
FASTFETCH_BOT_URL = env.get("FASTFETCH_BOT_URL", None)
FASTFETCH_BOT_API_KEY = env.get("FASTFETCH_BOT_API_KEY", None)

# extra functions
FILE_EXPORTER_ON = env.get("FILE_EXPORTER_ON", False)
OPENAI_API_KEY = env.get("OPENAI_API_KEY", None)

# Network
HTTP_REQUEST_TIMEOUT = int(env.get("HTTP_REQUEST_TIMEOUT", 15)) or 15

# Services environment variables
templates_directory = os.path.join(current_directory, "templates")
JINJA2_ENV = Environment(
    loader=FileSystemLoader(templates_directory), lstrip_blocks=True, trim_blocks=True
)
TEMPLATE_LANGUAGE = env.get(
    "TEMPLATE_LANGUAGE", "zh_CN"
)  # It is a workaround for translation system

TEMPLATE_TRANSLATION = {
    "en": {
        "online_snapshot": "Online Snapshot",
        "original_webpage": "Original Webpage",
    },
    "zh_CN": {
        "online_snapshot": "原文备份",
        "original_webpage": "阅读原文",
    },
    "zh_TW": {
        "online_snapshot": "原文備份",
        "original_webpage": "閱讀原文",
    },
}