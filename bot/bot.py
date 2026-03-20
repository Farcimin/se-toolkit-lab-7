"""Bot entry point — supports --test mode and Telegram polling."""
# Task1, Task2, Task3
import argparse
import asyncio
import sys

from handlers import handle_start, handle_help, handle_health, handle_labs, handle_scores
from services.intent_router import route


async def dispatch(text: str) -> str:
    """Route a text input to the appropriate handler and return the response."""
    text = text.strip()

    if text == "/start":
        return await handle_start()
    elif text == "/help":
        return await handle_help()
    elif text == "/health":
        return await handle_health()
    elif text == "/labs":
        return await handle_labs()
    elif text.startswith("/scores"):
        parts = text.split(maxsplit=1)
        lab = parts[1] if len(parts) > 1 else None
        return await handle_scores(lab)
    elif text.startswith("/"):
        return await handle_help()
    else:
        # Free text — route through LLM intent router
        return await route(text)


def test_mode(command: str) -> None:
    """Run a single command in test mode and print the response."""
    response = asyncio.run(dispatch(command))
    print(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument("--test", type=str, help="Test a command without Telegram (e.g. --test '/start')")
    args = parser.parse_args()

    if args.test:
        test_mode(args.test)
        sys.exit(0)

    # Telegram polling mode
    from config import BOT_TOKEN

    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is not set. Check .env.bot.secret", file=sys.stderr)
        sys.exit(1)

    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

        async def _tg_start(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Available Labs", callback_data="query:what labs are available?"),
                    InlineKeyboardButton("Health Check", callback_data="query:/health"),
                ],
                [
                    InlineKeyboardButton("Help", callback_data="query:/help"),
                    InlineKeyboardButton("Top Students", callback_data="query:who are the top 5 students in lab-04?"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(await handle_start(), reply_markup=reply_markup)

        async def _tg_help(update, context):
            await update.message.reply_text(await handle_help())

        async def _tg_health(update, context):
            await update.message.reply_text(await handle_health())

        async def _tg_labs(update, context):
            await update.message.reply_text(await handle_labs())

        async def _tg_scores(update, context):
            lab = " ".join(context.args) if context.args else None
            await update.message.reply_text(await handle_scores(lab))

        async def _tg_message(update, context):
            response = await dispatch(update.message.text)
            await update.message.reply_text(response)

        async def _tg_callback(update, context):
            query = update.callback_query
            await query.answer()
            text = query.data.removeprefix("query:")
            response = await dispatch(text)
            await query.message.reply_text(response)

        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", _tg_start))
        app.add_handler(CommandHandler("help", _tg_help))
        app.add_handler(CommandHandler("health", _tg_health))
        app.add_handler(CommandHandler("labs", _tg_labs))
        app.add_handler(CommandHandler("scores", _tg_scores))
        app.add_handler(CallbackQueryHandler(_tg_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _tg_message))

        print("Bot is starting...")
        app.run_polling()
    except ImportError:
        print("Error: python-telegram-bot is not installed. Run: uv sync", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
