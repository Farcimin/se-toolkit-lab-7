# Bot Development Plan

## Overview

This Telegram bot provides a conversational interface to the LMS backend API. Students can check scores, view available labs, get health status, and ask natural language questions about the course.

## Task 1: Scaffold and CLI Test Mode

Set up the project structure with a `bot/` directory containing an entry point (`bot.py`), a handler layer (`handlers/`), services (`services/`), and configuration (`config.py`). The entry point supports a `--test` CLI flag that invokes handlers directly and prints the response to stdout, enabling offline verification without a Telegram connection. Handlers are pure functions that take input and return text — they have no dependency on Telegram. This architecture allows the same logic to be used by both the `--test` CLI mode and the Telegram bot.

## Task 2: Backend Integration

Connect handlers to the LMS backend API using `httpx`. Implement the `/health` command (check backend availability), `/labs` (list available labs), and `/scores <lab>` (fetch score distribution for a given lab). All API calls go through a single `LMSClient` service that reads `LMS_API_URL` and `LMS_API_KEY` from the environment.

## Task 3: Intent Routing and LLM Integration

Add natural language intent routing so that free-text messages like "what labs are available" are classified and dispatched to the correct handler. Use an LLM API (via `LLM_API_KEY`) to classify user intent and extract parameters. Fall back to a help message when intent is unclear.

## Task 4: Deployment

Dockerize the bot, add it to `docker-compose.yml`, and deploy on the VM. Ensure the bot starts automatically, reconnects on failure, and logs errors. Verify end-to-end: Telegram message -> bot -> backend API -> response.
