import asyncio
from typing import Optional, Tuple

from telegram import Update
from telegram.ext import (
    Application,
    AIORateLimiter
)

from fastfetchbot_telegram_bot.bot.handlers import add_handlers
from fastfetchbot_telegram_bot.config import TELEGRAM_BOT_TOKEN, TELEBOT_CONNECT_TIMEOUT, TELEBOT_READ_TIMEOUT, \
    TELEBOT_WRITE_TIMEOUT, TELEBOT_API_SERVER, TELEBOT_LOCAL_FILE_MODE, TELEBOT_MAX_RETRY


class FastFetchBot:
    def __init__(self, **kwargs):
        self.application: Application = FastFetchBot.new_bot(**kwargs)

    @staticmethod
    def new_bot(
            token: str = TELEGRAM_BOT_TOKEN,
            arbitrary_callback_data: Optional[bool] = True,
            connect_timeout: Optional[int] = TELEBOT_CONNECT_TIMEOUT,
            read_timeout: Optional[int] = TELEBOT_READ_TIMEOUT,
            write_timeout: Optional[int] = TELEBOT_WRITE_TIMEOUT,
            base_url: Optional[str] = TELEBOT_API_SERVER,
            base_file_url: Optional[str] = TELEBOT_API_SERVER,
            local_mode: Optional[bool] = TELEBOT_LOCAL_FILE_MODE,
            max_retry: Optional[int] = TELEBOT_MAX_RETRY,
            add_response_handlers: Optional[bool] = True,
    ) -> Application:
        application = (
            Application.builder()
            .token(token)
            .arbitrary_callback_data(arbitrary_callback_data)
            .connect_timeout(connect_timeout)
            .read_timeout(read_timeout)
            .write_timeout(write_timeout)
            .base_url(base_url)
            .base_file_url(base_file_url)
            .local_mode(local_mode)
            .rate_limiter(AIORateLimiter(max_retries=max_retry))
            .build()
        )
        if add_response_handlers:
            add_handlers(application)
        return application

    @staticmethod
    def run_bot_polling(application: Application) -> None:
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def startup(self):
        await self.application.initialize()

    async def run_polling(self):
        await asyncio.to_thread(FastFetchBot.run_bot_polling, self.application)

    async def run_webhook(self, url: str):
        await self.set_webhook(url)
        await self.application.start()

    async def set_webhook(self, url: str):
        await self.application.bot.set_webhook(url)

    async def delete_webhook(self):
        await self.application.bot.delete_webhook()

    async def send_message(self):
        await self.application.bot.send_message()
