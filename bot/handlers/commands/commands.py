"""Command handlers — pure functions that take input and return text.

These handlers have no dependency on Telegram. They are called by both
the --test CLI mode and the Telegram bot.
"""


async def handle_start() -> str:
    return (
        "Welcome to the LMS Bot!\n"
        "I can help you check scores, view labs, and more.\n"
        "Type /help to see available commands."
    )


async def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start  — Welcome message\n"
        "/help   — Show this help\n"
        "/health — Check backend status\n"
        "/labs   — List available labs\n"
        "/scores <lab> — Show score distribution for a lab"
    )


async def handle_health() -> str:
    return "Backend status: not implemented yet"


async def handle_labs() -> str:
    return "Labs listing: not implemented yet"


async def handle_scores(lab: str | None = None) -> str:
    if not lab:
        return "Usage: /scores <lab-name>\nExample: /scores lab-04"
    return f"Scores for {lab}: not implemented yet"
