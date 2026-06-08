# ADX Report Agent

A conversational AI agent built with [LangChain](https://github.com/langchain-ai/langchain) that fetches **Google Ad Exchange (ADX) reports** and **emails them on request**. Instead of clicking through dashboards or writing scripts, you describe what you need in plain language—the agent handles account selection, date ranges, report retrieval, and delivery.

## What it does

- Understands natural-language requests such as *"Send yesterday's ADX report for the AP account to team@example.com"*
- Fetches ADX reports for supported accounts (`rs`, `ap`) over a given date range
- Sends the report as an email attachment
- Asks follow-up questions when required details (e.g. recipient email) are missing
- Runs in **mock mode** by default so you can develop and test without sending real emails

## How it works

The agent is powered by **DeepSeek** and exposes two tools:

| Tool | Description |
|------|-------------|
| `fetch_adx_report` | Downloads an ADX report for a given account and date range, saves it as a CSV under `reports/` |
| `send_report_email` | Sends the report file to a specified email address |

The LLM orchestrates these tools based on your conversation. A system prompt enforces rules such as valid accounts, date format (`YYYY-MM-DD`), and asking for a recipient when none is provided.

## Quick start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [DeepSeek API key](https://platform.deepseek.com/)

### Installation

```bash
git clone git@github-personal:yangsongcanada-hub/adx-report-agent.git
cd adx-report-agent

uv sync
cp .env.example .env
# Edit .env and set DEEPSEEK_API_KEY
```

### Run

**One-shot command:**

```bash
uv run python adx_agent.py "Send the ap account ADX report for 2026-06-01 to 2026-06-05 to test@example.com"
```

**Interactive mode:**

```bash
uv run python adx_agent.py
```

Type your request at the prompt. Enter `exit` to quit.

## Configuration

Copy `.env.example` to `.env` and fill in the values:

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes | API key for the DeepSeek chat model |
| `ADX_RS_TOKEN` | For live API | Token for the RS ADX account |
| `ADX_AP_TOKEN` | For live API | Token for the AP ADX account |
| `MOCK_EMAIL` | No | `true` (default) prints email details instead of sending |
| `SMTP_HOST` | For real email | SMTP server hostname |
| `SMTP_PORT` | For real email | SMTP port (default: `587`) |
| `SMTP_USER` | For real email | SMTP username |
| `SMTP_PASSWORD` | For real email | SMTP password |
| `SMTP_FROM` | For real email | Sender address |

### Mock mode (default)

With `MOCK_EMAIL=true`, the agent still fetches reports and prepares emails, but output is printed to the terminal instead of being sent. This is useful for local development and demos.

To send real emails, set `MOCK_EMAIL=false` and configure the `SMTP_*` variables.

### ADX API integration

Report fetching currently uses **mock CSV data** for demonstration. To connect to a real Google ADX API, update the `fetch_adx_report` function in `adx_agent.py` (see the `TODO` comment) and provide the appropriate account tokens in `.env`.

## Example conversation

```
User: Send yesterday's ADX report for the rs account to song@example.com

Agent:
  → fetch_adx_report(account="rs", start_date="2026-06-07", end_date="2026-06-07")
  → send_report_email(to_email="song@example.com", subject="...", report_path="...")

Final reply: Report for RS Account (2026-06-07) prepared and sent to song@example.com.
```

## Project structure

```
.
├── adx_agent.py      # Main agent: tools, prompts, CLI entry point
├── get_weather.py    # LangChain agent example (weather demo)
├── test.py           # DeepSeek model smoke test
├── reports/          # Generated report files (git-ignored)
├── .env.example      # Environment variable template
└── pyproject.toml    # Project metadata and dependencies
```

## Tech stack

- [LangChain](https://python.langchain.com/) — agent framework and tool calling
- [LangChain DeepSeek](https://pypi.org/project/langchain-deepseek/) — DeepSeek chat model integration
- [uv](https://docs.astral.sh/uv/) — dependency and virtual environment management

## License

MIT
