from typing import Optional, Tuple

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    AIORateLimiter
)

from bot.handlers import add_handlers
from config import TELEGRAM_BOT_TOKEN, TELEBOT_CONNECT_TIMEOUT, TELEBOT_READ_TIMEOUT, TELEBOT_WRITE_TIMEOUT, \
    TELEBOT_API_SERVER, TELEBOT_LOCAL_FILE_MODE, TELEBOT_MAX_RETRY

application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .arbitrary_callback_data(True)
        .connect_timeout(TELEBOT_CONNECT_TIMEOUT)
        .read_timeout(TELEBOT_READ_TIMEOUT)
        .write_timeout(TELEBOT_WRITE_TIMEOUT)
        .base_url(TELEBOT_API_SERVER)
        .base_file_url(TELEBOT_API_SERVER)
        .local_mode(TELEBOT_LOCAL_FILE_MODE)
        .rate_limiter(AIORateLimiter(max_retries=TELEBOT_MAX_RETRY))
        .build()
    )


def run_bot() -> None:
    add_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
