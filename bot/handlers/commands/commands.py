"""Command handlers — pure functions that take input and return text.

These handlers have no dependency on Telegram. They are called by both
the --test CLI mode and the Telegram bot.
"""

import httpx

from services.lms_client import LMSClient


_client = LMSClient()


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
        "/scores <lab> — Show per-task pass rates for a lab"
    )


async def handle_health() -> str:
    try:
        items = await _client.get_items()
        return f"Backend is healthy. {len(items)} items available."
    except httpx.ConnectError as e:
        return f"Backend error: connection refused ({e.request.url.host}:{e.request.url.port}). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except httpx.RequestError as e:
        return f"Backend error: {e}. Check that the services are running."


async def handle_labs() -> str:
    try:
        items = await _client.get_items()
        labs = [item for item in items if item.get("type") == "lab"]
        if not labs:
            return "No labs found."
        lines = ["Available labs:"]
        for lab in labs:
            title = lab.get("title", "Untitled")
            lines.append(f"- {title}")
        return "\n".join(lines)
    except httpx.ConnectError as e:
        return f"Backend error: connection refused ({e.request.url.host}:{e.request.url.port}). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except httpx.RequestError as e:
        return f"Backend error: {e}. Check that the services are running."


async def handle_scores(lab: str | None = None) -> str:
    if not lab:
        return "Usage: /scores <lab-name>\nExample: /scores lab-04"
    try:
        pass_rates = await _client.get_pass_rates(lab)
        if not pass_rates:
            return f"No score data found for {lab}."
        lines = [f"Pass rates for {lab}:"]
        for task in pass_rates:
            title = task.get("title", "Unknown task")
            rate = task.get("pass_rate", 0)
            attempts = task.get("attempts", 0)
            lines.append(f"- {title}: {rate:.1f}% ({attempts} attempts)")
        return "\n".join(lines)
    except httpx.ConnectError as e:
        return f"Backend error: connection refused ({e.request.url.host}:{e.request.url.port}). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except httpx.RequestError as e:
        return f"Backend error: {e}. Check that the services are running."
