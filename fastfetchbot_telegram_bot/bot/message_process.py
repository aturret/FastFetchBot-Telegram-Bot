import asyncio
import html
import json
import os
import traceback
from io import BytesIO
from typing import Union
from urllib.parse import urlparse
from urllib.request import url2pathname

import aiofiles
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAnimation,
    InputMediaAudio,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackContext,
    ContextTypes,
)

from fastfetchbot_telegram_bot.bot.formatting import message_formatting
from fastfetchbot_telegram_bot.config import FILE_EXPORTER_ON, OPENAI_API_KEY, TELEBOT_DEBUG_CHANNEL, TELEGRAM_CHANNEL_ID, \
    TELEGRAM_CHANNEL_ADMIN_LIST, TELEGRAM_BOT_MESSAGE_BAN_LIST, TELEGRAM_GROUP_MESSAGE_BAN_LIST, TELEBOT_WRITE_TIMEOUT, \
    TELEGRAM_SINGLE_MESSAGE_MEDIA_LIMIT, TELEBOT_API_SERVER, TELEGRAM_FILE_UPLOAD_LIMIT, \
    TELEGRAM_FILE_UPLOAD_LIMIT_LOCAL_API, TELEGRAM_IMAGE_DIMENSION_LIMIT, TELEGRAM_IMAGE_SIZE_LIMIT
from fastfetchbot_telegram_bot.models.files import NamedBytesIO
from fastfetchbot_telegram_bot.utils.image import Image, check_image_type, image_compressing
from fastfetchbot_telegram_bot.utils.logger import logger
from fastfetchbot_telegram_bot.utils.network import get_url_metadata, get_item, download_file_by_metadata_item
from fastfetchbot_telegram_bot.utils.parser import list_to_string


async def all_messages_process(update: Update, context: CallbackContext) -> None:
    message = update.message
    # if message and DATABASE_ON:
    #     telegram_chat = TelegramChat.construct(**message.chat.to_dict())
    #     telegram_user = TelegramUser.construct(**message.from_user.to_dict())
    #     telegram_message = TelegramMessage(
    #         datetime=message.date,
    #         chat=telegram_chat,
    #         user=telegram_user,
    #         text=message.text or "",
    #     )
    #     await save_instances(telegram_message)


async def https_url_process(update: Update, context: CallbackContext) -> None:
    message = update.message
    welcome_message = await message.reply_text(
        text="Processing...",
    )
    url_dict: dict = message.parse_entities(types=["url"])
    await welcome_message.delete()
    for i, url in enumerate(url_dict.values()):
        process_message = await message.reply_text(
            text=f"Processing the {i + 1}th url...",
        )
        url_metadata = await get_url_metadata(url, ban_list=list_to_string(TELEGRAM_BOT_MESSAGE_BAN_LIST))
        source = url_metadata.get("source")
        content_type = url_metadata.get("content_type")
        if source == "banned":
            await process_message.edit_text(
                text=f"For the {i + 1} th url, the url is banned."
            )
            return
        if source == "unknown":
            await process_message.edit_text(
                text=f"For the {i + 1} th url, no supported url found."
            )
            return
        else:
            await process_message.edit_text(
                text=f"{source} url found. Processing..."
            )
            # create the inline keyboard
            special_function_keyboard = []
            basic_function_keyboard = []
            if TELEGRAM_CHANNEL_ID and (
                    TELEGRAM_CHANNEL_ADMIN_LIST
                    and str(message.from_user.id) in TELEGRAM_CHANNEL_ADMIN_LIST
            ):
                special_function_keyboard.append(
                    InlineKeyboardButton(
                        "Send to Channel",
                        callback_data={
                            "type": "channel",
                            "metadata": url_metadata,
                            "extra_args": {"store_document": True},
                        },
                    ),
                )
            # video content url buttons
            if content_type == "video":
                basic_function_keyboard.extend(
                    [
                        InlineKeyboardButton(
                            "Get Info",
                            callback_data={
                                "type": "video",
                                "metadata": url_metadata,
                                "extra_args": {"download": False},
                            },
                        ),
                        InlineKeyboardButton(
                            "Download",
                            callback_data={
                                "type": "video",
                                "metadata": url_metadata,
                            },
                        ),
                    ]
                )
                if FILE_EXPORTER_ON:
                    special_function_keyboard.extend(
                        [
                            InlineKeyboardButton(
                                "Audio Only",
                                callback_data={
                                    "type": "video",
                                    "metadata": url_metadata,
                                    "extra_args": {
                                        "audio_only": True,
                                    },
                                },
                            ),
                            InlineKeyboardButton(
                                "Download HD",
                                callback_data={
                                    "type": "video",
                                    "metadata": url_metadata,
                                    "extra_args": {"hd": True},
                                },
                            ),
                        ]
                    )
                    if OPENAI_API_KEY:
                        special_function_keyboard.append(
                            InlineKeyboardButton(
                                "Transcribe Text",
                                callback_data={
                                    "type": "video",
                                    "metadata": url_metadata,
                                    "extra_args": {
                                        "audio_only": True,
                                        "transcribe": True,
                                        "store_document": True,
                                    },
                                },
                            ),
                        )
            elif content_type == "social_media":
                basic_function_keyboard.extend(
                    [
                        InlineKeyboardButton(
                            "Send to Me",
                            callback_data={"type": "private", "metadata": url_metadata},
                        ),
                        InlineKeyboardButton(
                            "Force Send in Chat",
                            callback_data={"type": "force", "metadata": url_metadata},
                        ),
                    ]
                )
                if FILE_EXPORTER_ON:
                    special_function_keyboard.append(
                        InlineKeyboardButton(
                            "Send with PDF",
                            callback_data={
                                "type": "pdf",
                                "metadata": url_metadata,
                                "extra_args": {"store_document": True},
                            },
                        ),
                    )
            basic_function_keyboard.append(
                InlineKeyboardButton(
                    "Cancel",
                    callback_data={"type": "cancel"},
                ),
            )
            keyboard = [
                special_function_keyboard,
                basic_function_keyboard,
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await process_message.reply_text(
                f"For the {i + 1}th url: {url}, please choose the function you want to use:",
                reply_markup=reply_markup,
            )
            await process_message.delete()


async def https_url_auto_process(update: Update, context: CallbackContext) -> None:
    message = update.message
    url_dict = message.parse_entities(types=["url"])
    for i, url in enumerate(url_dict.values()):
        url_metadata = await get_url_metadata(
            url, ban_list=TELEGRAM_GROUP_MESSAGE_BAN_LIST
        )
        source = url_metadata.get("source")
        if source == "unknown" or source == "banned":
            logger.debug(f"for the {i + 1}th url {url}, no supported url found.")
            return
        else:
            logger.debug(f"for the {i + 1}th url {url}, {source} url found. Processing...")
            item = await get_item(url)
            await send_item_message(data=item, chat_id=message.chat.id, message=message, context=context)


async def buttons_process(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    chat_id = None
    if data["type"] == "cancel":
        await query.answer("Canceled")
    else:
        if data["type"] == "private" or data["type"] == "force":
            await query.answer("Sending to you...")
        if data["type"] == "channel":
            if data.get("channel_id") or len(TELEGRAM_CHANNEL_ID) == 1:
                channel_chat = await context.bot.get_chat(
                    chat_id=data.get("channel_id")
                    if data.get("channel_id")
                    else TELEGRAM_CHANNEL_ID[0]
                )
                await query.answer("Sending to channel...")
                if channel_chat.type == "channel":
                    chat_id = channel_chat.id
                else:
                    await query.message.reply_text(
                        text="Sorry, the provided channel id does not exist or is not a channel."
                    )
                    chat_id = query.message.chat_id
            elif len(TELEGRAM_CHANNEL_ID) > 1:
                choose_channel_keyboard = await _create_choose_channel_keyboard(
                    data=data, context=context
                )
                await query.message.reply_text(
                    text="Please choose the channel you want to send:",
                    reply_markup=InlineKeyboardMarkup(choose_channel_keyboard),
                )
                await query.message.delete()
                context.drop_callback_data(query)
                return
        else:
            chat_id = query.message.chat_id
        if data["type"] == "video":
            await query.answer("Video processing...")
        replying_message = await query.message.reply_text(
            text=f"Item processing...",
        )
        extra_args = data["extra_args"] if "extra_args" in data else {}
        metadata_item = await get_item(
            url=data["metadata"]["url"], **extra_args
        )
        await replying_message.edit_text(
            text=f"Item processed. Sending to the target...",
        )
        if data["type"] == "force":
            metadata_item["message_type"] = "short"
        await send_item_message(metadata_item, chat_id=chat_id, context=context)
        if data["type"] == "channel":
            await query.message.reply_text(
                text=f"Item sent to the channel.",
            )
        await replying_message.delete()
    await query.message.delete()
    context.drop_callback_data(query)


async def _create_choose_channel_keyboard(data: dict, context: CallbackContext) -> list:
    choose_channel_keyboard = []
    for i, channel_id in enumerate(TELEGRAM_CHANNEL_ID):
        channel_chat = await context.bot.get_chat(chat_id=channel_id)
        choose_channel_keyboard.append(
            [
                InlineKeyboardButton(
                    channel_chat.title,
                    callback_data={
                        "type": "channel",
                        "metadata": data["metadata"],
                        "extra_args": data["extra_args"],
                        "channel_id": channel_id,
                    },
                )
            ]
        )
    choose_channel_keyboard.append(
        [
            InlineKeyboardButton(
                "Cancel",
                callback_data={"type": "cancel"},
            )
        ]
    )
    return choose_channel_keyboard


async def send_item_message(
        data: dict, chat_id: Union[int, str] = None, message: Message = None, context: CallbackContext = None
) -> None:
    """
    :param context:
    :param data: (dict) metadata of the item
    :param chat_id: (int) any chat id for sending
    :param message: (Message) any message to reply
    :return:
    """
    logger.debug(f"send_item_message: {data}, {chat_id}, {message}")
    if not chat_id and not message:
        raise ValueError("must provide chat_id or message")
    if (
            not chat_id
    ) and message:  # this function supports directly reply to a message even if the chat_id is None
        chat_id = message.chat.id
    discussion_chat_id = chat_id
    the_chat = await context.bot.get_chat(chat_id=chat_id)
    logger.debug(f"the chat of sending message: {the_chat}")
    if the_chat.type == "channel":
        if the_chat.linked_chat_id:
            discussion_chat_id = the_chat.linked_chat_id
    try:
        caption_text = message_formatting(data)
        if len(data["media_files"]) > 0:
            # if the message type is short and there are some media files, send media group
            reply_to_message_id = None
            media_message_group, file_message_group = await media_files_packaging(
                media_files=data["media_files"], data=data
            )
            if (
                    len(media_message_group) > 0
            ):  # if there are some media groups to send, send it
                for i, media_group in enumerate(media_message_group):
                    caption_text = (
                        caption_text
                        if i == 0
                        else f"the {i + 1}th part of the media item:"
                    )
                    logger.debug(f"media group: {media_group}")
                    logger.debug(
                        f"caption text: {caption_text},length={len(caption_text)}"
                    )
                    sent_media_files_message = await context.bot.send_media_group(
                        chat_id=chat_id,
                        media=media_group,
                        parse_mode=ParseMode.HTML,
                        caption=caption_text,
                        write_timeout=TELEBOT_WRITE_TIMEOUT,
                        reply_to_message_id=message.message_id if message else None,
                    )
            else:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=caption_text,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=message.message_id if message else None,
                    disable_web_page_preview=True
                    if data["message_type"] == "short"
                    else False,
                    disable_notification=True,
                )
            if discussion_chat_id != chat_id:
                await asyncio.sleep(
                    3
                )  # wait for several seconds to avoid missing the target message
                # if the chat is a channel, get the latest pinned message from the channel and reply to it
                group_chat = await context.bot.get_chat(chat_id=discussion_chat_id)
                logger.debug(f"the group chat: {group_chat}")
                pinned_message = group_chat.pinned_message
                logger.debug(f"the pinned message: {pinned_message}")
                if len(media_message_group) > 0:
                    if (
                            pinned_message.forward_from_message_id
                            == sent_media_files_message[-1].message_id
                    ):
                        reply_to_message_id = (
                                group_chat.pinned_message.id
                                - len(sent_media_files_message)
                                + 1
                        )
                elif pinned_message.forward_from_message_id == sent_message.message_id:
                    reply_to_message_id = group_chat.pinned_message.id
                else:
                    reply_to_message_id = group_chat.pinned_message.id + 1
            if (
                    len(file_message_group) > 0
            ):  # send files, the files messages should be replied to the message sent before
                logger.debug(f"reply_to_message_id: {reply_to_message_id}")
                for file_group in file_message_group:
                    logger.debug(f"file group: {file_group}")
                    await context.bot.send_media_group(
                        chat_id=discussion_chat_id,
                        media=file_group,
                        reply_to_message_id=reply_to_message_id,
                        parse_mode=ParseMode.HTML,
                        disable_notification=True,
                    )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.message_id if message else None,
                disable_web_page_preview=True
                if data["message_type"] == "short"
                else False,
                disable_notification=True,
            )
    except Exception as e:
        logger.error(e)
        traceback.print_exc()
        await context.bot.send_message(
            chat_id=discussion_chat_id,
            text="Error occurred while sending the item to the target 😕",
            reply_to_message_id=message.message_id if message else None,
        )
        await send_debug_channel(traceback.format_exc(), context)


async def invalid_buttons(update: Update, context: CallbackContext) -> None:
    await update.callback_query.answer("Invalid button!")
    await update.effective_message.edit_text(
        "Sorry, Error Occured, I could not process this button click 😕."
    )


async def error_process(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    debug_chat_id = update.message.chat_id
    if TELEBOT_DEBUG_CHANNEL is not None:
        debug_chat_id = TELEBOT_DEBUG_CHANNEL
    await context.bot.send_message(
        chat_id=debug_chat_id, text=message, parse_mode=ParseMode.HTML
    )


async def media_files_packaging(media_files: list, data: dict) -> tuple:
    """
    Download the media files from data["media_files"] and package them into a list of media group or file group for
    sending them by send_media_group method or send_document method.
    :param data: (dict) metadata of the item
    :param media_files: (list) a list of media files,
    :param caption_text: (str) the caption text
    :return: (tuple) a tuple of media group and file group
        media_message_group: (list) a list of media items, the type of each item is InputMediaPhoto or InputMediaVideo
        file_group: (list) a list of file items, the type of each item is InputFile
    TODO: It's not a good practice for this function. This method will still download all the media files even when
        media files are too large and it can be memory consuming even if we use a database to store the media files.
        The function should be optimized to resolve the media files one group by one group and send each group
        immediately after it is resolved.
        This processing method should be optimized in the future.
    """
    media_counter, file_counter = 0, 0
    media_message_group, media_group, file_message_group, file_group = [], [], [], []
    for (
            media_item
    ) in media_files:  # To traverse all media items in the media files list
        # check if we need to create a new media group
        if media_counter == TELEGRAM_SINGLE_MESSAGE_MEDIA_LIMIT:
            # the limitation of media item for a single telegram media group message is 10
            media_message_group.append(media_group)
            media_group = []
            media_counter = 0
        if file_counter == TELEGRAM_SINGLE_MESSAGE_MEDIA_LIMIT:
            # the limitation of media item for a single telegram media group message is 10
            file_message_group.append(file_group)
            file_group = []
            file_counter = 0
        if not (
                media_item["media_type"] in ["image", "gif", "video"]
                and data["message_type"] == "long"
        ):
            # check the url validity
            url_parser = urlparse(media_item["url"])
            if url_parser.scheme in [
                "http",
                "https",
            ]:  # if the url is a http url, download the file
                file_format = "mp4" if media_item["media_type"] == "video" else None
                io_object = await download_file_by_metadata_item(
                    media_item["url"], data=data, file_format=file_format
                )
                filename = io_object.name
                file_size = io_object.size
            else:  # if the url is a local file path, just add it to the media group
                try:
                    file_path = url2pathname(media_item["url"])
                    async with aiofiles.open(file_path, mode="rb") as f:
                        filename = os.path.basename(file_path)
                        content = await f.read()
                        io_object = NamedBytesIO(content=content, name=filename)
                    file_size = io_object.size
                except Exception as e:  # the url is not a valid file path
                    logger.error(e)
                    continue
            # check the file size
            if (
                    not TELEBOT_API_SERVER
            ):  # the official telegram bot api server only supports 50MB file
                if file_size > TELEGRAM_FILE_UPLOAD_LIMIT:
                    # if the size is over 50MB, skip this file
                    continue
            else:
                if file_size > TELEGRAM_FILE_UPLOAD_LIMIT_LOCAL_API:
                    # for local api sever, if the size is over 2GB, skip this file
                    continue
            # check media files' type and process them by their type
            if media_item["media_type"] == "image":
                image_url = media_item["url"]
                ext = await check_image_type(io_object)
                # jpg to jpeg, ignore case
                if ext.lower() == "jpg":
                    ext = "JPEG"
                io_object.seek(0)
                image = Image.open(io_object, formats=[ext])
                img_width, img_height = image.size
                ratio = float(max(img_height, img_width)) / float(
                    min(img_height, img_width)
                )
                # don't try to resize image if the ratio is too large
                if (
                        ratio < 5
                        or max(img_height, img_width) < TELEGRAM_IMAGE_DIMENSION_LIMIT
                ):
                    image = image_compressing(image, TELEGRAM_IMAGE_DIMENSION_LIMIT)
                    with BytesIO() as buffer:
                        # mime_type file format
                        image.save(buffer, format=ext)
                        buffer.seek(0)
                        resized_ratio = max(image.height, image.width) / min(
                            image.height, image.width
                        )
                        logger.debug(
                            f"resized image size: {buffer.getbuffer().nbytes}, ratio: {resized_ratio}, width: {image.width}, height: {image.height}"
                        )
                        media_group.append(InputMediaPhoto(buffer, filename=filename))
                # the image is not able to get json serialized
                logger.debug(
                    f"image size: {file_size}, ratio: {ratio}, width: {img_width}, height: {img_height}"
                )
                if (
                        file_size > TELEGRAM_IMAGE_SIZE_LIMIT
                        or img_width > TELEGRAM_IMAGE_DIMENSION_LIMIT
                        or img_height > TELEGRAM_IMAGE_DIMENSION_LIMIT
                ) and data["category"] not in ["xiaohongshu"]:
                    io_object = await download_file_by_metadata_item(
                        url=image_url, data=data
                    )
                    if not io_object.name.endswith(".gif"):
                        if not io_object.name.endswith(ext.lower()):
                            io_object.name = io_object.name + "." + ext.lower()
                        # TODO: it is not a good way to judge whether it is a gif...
                        file_group.append(
                            InputMediaDocument(io_object, parse_mode=ParseMode.HTML)
                        )
                        file_counter += 1
            elif media_item["media_type"] == "gif":
                io_object = await download_file_by_metadata_item(
                    url=media_item["url"],
                    data=data,
                    file_name="gif_image-" + str(media_counter) + ".gif",
                )
                io_object.name = io_object.name + ".gif"
                media_group.append(InputMediaAnimation(io_object))
            elif media_item["media_type"] == "video":
                media_group.append(InputMediaVideo(io_object, supports_streaming=True))
            # TODO: not have any services to store audio files for now, just a placeholder
            elif media_item["media_type"] == "audio":
                media_group.append(InputMediaAudio(io_object))
            elif media_item["media_type"] == "document":
                file_group.append(
                    InputMediaDocument(io_object, parse_mode=ParseMode.HTML)
                )
                file_counter += 1
            media_counter += 1
            logger.info(
                f"get the {media_counter}th media item,type: {media_item['media_type']}, url: {media_item['url']}"
            )
    # check if the media group is empty, if it is, return None
    if len(media_group) > 0:  # append the last media group
        media_message_group.append(media_group)
    if len(file_group) > 0:
        file_message_group.append(file_group)
    return media_message_group, file_message_group


async def send_debug_channel(message: str, context: CallbackContext) -> None:
    if TELEBOT_DEBUG_CHANNEL is not None:
        await context.bot.send_message(
            chat_id=TELEBOT_DEBUG_CHANNEL, text=message, parse_mode=ParseMode.HTML
        )
