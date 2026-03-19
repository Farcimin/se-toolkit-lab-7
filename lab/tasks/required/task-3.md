# Intent-Based Natural Language Routing

The bot currently only responds to slash commands. In this task, you make it understand plain text — the user types a question in natural language, and the bot uses an LLM to figure out what data to fetch and how to answer.

## What you will build

An intent router that accepts plain text messages, sends them to an LLM along with tool definitions (your backend API endpoints), and composes a response from the results.

```terminal
$ python bot/bot.py --test "which lab has the lowest pass rate?"
Based on the data, Lab 03 has the lowest average pass rate at 62.3%.
Here's the breakdown by task:
- Backend API: 58.1% (145 attempts)
- Security Hardening: 66.5% (132 attempts)
```

This builds directly on Lab 6 — you reuse the pattern of giving an LLM a set of tools and letting it decide which to call. The difference: in Lab 6 you built a CLI agent, here the agent is embedded inside a user-facing Telegram bot.

## How it works

```
User: "which lab has the worst results?"
Bot:  → sends message + tool definitions to LLM
      → LLM decides: call get_pass_rates for each lab
      → bot executes the API calls
      → LLM summarizes the results
      → bot sends formatted response to user
```

The LLM receives:
1. The user's message
2. A list of available tools (your backend API endpoints as function schemas)
3. The system prompt explaining the bot's role

The LLM responds with tool calls. Your bot executes them against the real backend, feeds the results back, and the LLM produces the final answer.

## Required tools

Define **all** backend endpoints as tools the LLM can call. This gives the intent router enough variety to handle diverse questions.

| Tool name | Endpoint | Description for LLM |
|-----------|----------|-------------------|
| `get_items` | `GET /items/` | Get the list of labs and tasks in the LMS |
| `get_learners` | `GET /learners/` | Get enrolled students and their groups |
| `get_scores` | `GET /analytics/scores?lab=` | Get score distribution (4 buckets) for a lab |
| `get_pass_rates` | `GET /analytics/pass-rates?lab=` | Get per-task average scores and attempt counts |
| `get_timeline` | `GET /analytics/timeline?lab=` | Get submissions per day for a lab |
| `get_groups` | `GET /analytics/groups?lab=` | Get per-group average scores and student counts |
| `get_top_learners` | `GET /analytics/top-learners?lab=&limit=` | Get top N learners by average score |
| `get_completion_rate` | `GET /analytics/completion-rate?lab=` | Get completion rate percentage for a lab |
| `trigger_sync` | `POST /pipeline/sync` | Trigger ETL sync to refresh data from autochecker |

Example tool schema:

```python
{
    "type": "function",
    "function": {
        "name": "get_pass_rates",
        "description": "Get per-task average scores and attempt counts for a lab",
        "parameters": {
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
            },
            "required": ["lab"],
        },
    },
}
```

## Scenarios to cover

Your intent router should handle these categories:

**Direct data queries (single API call):**

| User message | Expected behavior |
|---|---|
| "what labs are available?" | Calls `get_items`, lists labs |
| "how many students are enrolled?" | Calls `get_learners`, counts |
| "show me scores for lab 4" | Calls `get_pass_rates(lab="lab-04")`, formats results |
| "who are the top 5 students?" | Calls `get_top_learners(limit=5)`, formats leaderboard |
| "which group is doing best in lab 3?" | Calls `get_groups(lab="lab-03")`, ranks groups |
| "how many submissions were there today?" | Calls `get_timeline`, filters recent |

**Multi-step reasoning (multiple API calls):**

| User message | Expected behavior |
|---|---|
| "which lab has the lowest pass rate?" | Calls `get_items` → `get_pass_rates` per lab → compares |
| "compare group A and group B" | Calls `get_groups` → filters → compares |

**Fallback / ambiguous:**

| User message | Expected behavior |
|---|---|
| "hello" | Friendly greeting + hint about capabilities |
| "asdfgh" | "I didn't understand. Here's what I can help with..." |
| "lab 4" | Clarify: "What about lab 4? I can show scores, pass rates..." |

## Inline buttons

Add inline keyboard buttons or a reply keyboard so users can discover available actions without typing. For example, after `/start`, show buttons for common queries.

## Deliverables

### 1. Intent router (`bot/handlers/intent.py` or similar)

Accepts plain text (no `/` prefix), sends to LLM with tool definitions, executes tool calls, returns formatted response. Must work in `--test` mode.

### 2. All 9 tools defined and wired

Each tool from the table above must be defined as a function schema and have a working implementation that calls the corresponding backend endpoint.

### 3. Fallback handling

Unknown or ambiguous input returns a helpful message listing capabilities — not a crash or empty response.

### 4. Inline buttons

Keyboard markup (inline or reply) for common actions. Must be present in the source code.

## Acceptance criteria

- [ ] `--test "what labs are available"` (no `/` prefix) returns a non-empty answer (at least 20 characters).
- [ ] `--test "which lab has the lowest pass rate"` returns an answer mentioning a specific lab.
- [ ] `--test "asdfgh"` returns a helpful message, not a crash or empty response.
- [ ] Source code contains keyboard/button setup (`InlineKeyboardMarkup`, `ReplyKeyboardMarkup`, or equivalent).
- [ ] Source code defines at least 9 tool/function schemas for the LLM.
- [ ] Changes follow the Git workflow (issue, branch, PR, review, merge).

## Working with your coding agent

This is the most complex task — take it step by step. The key concept is **LLM tool use / function calling**: you give the LLM a list of tools it can call, and it decides which one(s) to use based on the user's message.

**Understanding tool use:**

> Explain LLM function calling / tool use. How does the LLM decide which tool to call? What's the difference between the system prompt and tool definitions?

> Show me a minimal example: one tool, one user message, the full message flow (user → LLM → tool_call → execute → feed back → final answer). I want to understand the loop.

**Designing tools:**

> Here are my backend endpoints [paste the table from the task]. Help me design tool schemas for them. What makes a good tool description — why does description quality matter more than prompt engineering?

> I have 9 tools defined. Before implementing the loop, walk me through: if the user says "which lab has the lowest pass rate?", what should the LLM's reasoning look like? Which tools would it call and in what order?

**Debugging intent routing:**

> The LLM keeps returning a text answer instead of calling a tool. Help me debug — show me the messages I'm sending and explain what might be wrong.

> Test this: `--test "which lab has the lowest pass rate?"`. The answer is wrong. Help me trace through: what tools were called, what data came back, where did the reasoning go wrong?

**Fallback handling:**

> The user typed "asdfgh". What should happen? Implement a fallback that's helpful, not just "I don't understand." Explain why good fallbacks matter for UX.
