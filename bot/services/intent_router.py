"""LLM-powered intent router with tool calling loop."""

import json
import sys

import httpx

from config import LLM_API_BASE_URL, LLM_API_KEY, LLM_API_MODEL
from services.lms_client import LMSClient

_client = LMSClient()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get all items (labs, tasks, steps) from the LMS. Returns a list of items with id, type, title, description, and parent_id. Use this to find out which labs exist.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get all enrolled students. Returns a list of learners with external_id, student_group, and enrolled_at.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution for a lab (4 score buckets). Shows how many students scored in each range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a lab. Shows how well students are doing on each task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day for a lab. Shows activity over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group performance metrics for a lab. Shows average scores and student counts per student group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by average score for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                    "limit": {"type": "integer", "description": "Number of top learners to return (default 5)"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a lab. Shows what percentage of students scored >= 60.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL pipeline to refresh data from the autochecker. Use when the user asks to update or sync data.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are an LMS Bot assistant that helps students and instructors query a Learning Management System. "
    "You have access to tools that fetch data from the LMS backend API. "
    "Use these tools to answer questions about labs, scores, students, and course data. "
    "When a user asks a question, decide which tool(s) to call. "
    "If a question requires data from multiple labs, call the appropriate tool for each lab. "
    "Lab identifiers are like 'lab-01', 'lab-02', etc. If the user says 'lab 4', convert it to 'lab-04'. "
    "Always provide concise, data-driven answers. Format numbers nicely. "
    "If the user sends a greeting, respond friendly and briefly explain what you can do. "
    "If the user sends gibberish or something unclear, respond helpfully and list your capabilities."
)


async def _execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool call and return the result as a JSON string."""
    try:
        if name == "get_items":
            result = await _client.get_items()
        elif name == "get_learners":
            result = await _client.get_learners()
        elif name == "get_scores":
            result = await _client.get_scores(arguments["lab"])
        elif name == "get_pass_rates":
            result = await _client.get_pass_rates(arguments["lab"])
        elif name == "get_timeline":
            result = await _client.get_timeline(arguments["lab"])
        elif name == "get_groups":
            result = await _client.get_groups(arguments["lab"])
        elif name == "get_top_learners":
            limit = arguments.get("limit", 5)
            result = await _client.get_top_learners(arguments["lab"], limit)
        elif name == "get_completion_rate":
            result = await _client.get_completion_rate(arguments["lab"])
        elif name == "trigger_sync":
            result = await _client.trigger_sync()
        else:
            result = {"error": f"Unknown tool: {name}"}
        return json.dumps(result, default=str)
    except httpx.ConnectError as e:
        return json.dumps({"error": f"Connection refused ({e.request.url.host}:{e.request.url.port})"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code} {e.response.reason_phrase}"})
    except httpx.RequestError as e:
        return json.dumps({"error": str(e)})


async def route(user_message: str) -> str:
    """Route a natural language message through the LLM with tool calling."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    max_iterations = 10

    try:
        async with httpx.AsyncClient() as http:
            for _ in range(max_iterations):
                resp = await http.post(
                    f"{LLM_API_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": LLM_API_MODEL,
                        "messages": messages,
                        "tools": TOOLS,
                    },
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()

                choice = data["choices"][0]
                message = choice["message"]
                messages.append(message)

                tool_calls = message.get("tool_calls")
                if not tool_calls:
                    return message.get("content", "I couldn't generate a response.")

                for tc in tool_calls:
                    fn = tc["function"]
                    args = json.loads(fn["arguments"]) if fn["arguments"] else {}
                    print(f"[tool] LLM called: {fn['name']}({json.dumps(args)})", file=sys.stderr)

                    result = await _execute_tool(fn["name"], args)
                    result_preview = result[:80] + "..." if len(result) > 80 else result
                    print(f"[tool] Result: {result_preview}", file=sys.stderr)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })

                print(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM", file=sys.stderr)

        return "I couldn't complete the request after multiple steps."

    except httpx.ConnectError as e:
        return f"LLM error: connection refused ({e.request.url.host}:{e.request.url.port}). Check that the LLM service is running."
    except httpx.HTTPStatusError as e:
        return f"LLM error: HTTP {e.response.status_code}. Check LLM API credentials and service status."
    except httpx.RequestError as e:
        return f"LLM error: {e}"
