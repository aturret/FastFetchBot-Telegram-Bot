from fastfetchbot_telegram_bot import FastFetchBot
from fastfetchbot_telegram_bot.config import FASTFETCHBOT_HOST_URL


def main() -> None:
    """Start the bot."""
    if not FASTFETCHBOT_HOST_URL:
        raise ValueError("FAST_FETCH_BOT_URL is not set")
    FastFetchBot().set_webhook(FASTFETCHBOT_HOST_URL)

    # Create the Application and pass it your bot's token.


if __name__ == "__main__":
    main()
