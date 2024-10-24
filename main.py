from bot.application import run_bot
from config import FASTFETCH_BOT_URL


def main() -> None:
    """Start the bot."""
    if not FASTFETCH_BOT_URL:
        raise ValueError("FAST_FETCH_BOT_URL is not set")
    run_bot()

    # Create the Application and pass it your bot's token.


if __name__ == "__main__":
    main()
