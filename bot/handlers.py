from telegram import MessageEntity
from telegram.ext import (
    Application,
    CallbackContext,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    InvalidCallbackData,
    AIORateLimiter,
)

from bot.message_process import (all_messages_process,
                                 invalid_buttons,
                                 https_url_process,
                                 https_url_auto_process,
                                 error_process,
                                 buttons_process)


def add_handlers(application: Application) -> None:
    all_messages_handler = MessageHandler(
        filters=filters.ALL,
        callback=all_messages_process,
    )
    https_url_process_handler = MessageHandler(
        filters=filters.ChatType.PRIVATE
                & filters.Entity(MessageEntity.URL)
                & (~filters.FORWARDED)
                & filters.USER,
        callback=https_url_process,
    )
    https_url_auto_process_handler = MessageHandler(
        filters=(
                        filters.ChatType.SUPERGROUP
                        | filters.ChatType.GROUP
                        | filters.ChatType.GROUPS
                )
                & filters.Entity(MessageEntity.URL)
                & (~filters.FORWARDED)
                & filters.USER,
        callback=https_url_auto_process,
    )
    invalid_buttons_handler = CallbackQueryHandler(
        callback=invalid_buttons,
        pattern=InvalidCallbackData,
    )
    buttons_process_handler = CallbackQueryHandler(
        callback=buttons_process, pattern=dict
    )
    # add handlers
    application.add_handlers(
        [
            https_url_process_handler,
            https_url_auto_process_handler,
            all_messages_handler,
            invalid_buttons_handler,
            buttons_process_handler,
        ]
    )
    application.add_error_handler(error_process)
