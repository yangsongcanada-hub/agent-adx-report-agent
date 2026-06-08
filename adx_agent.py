"""
ADX report agent example.

Usage:
    python adx_agent.py
    python adx_agent.py "Send the ap account ADX report for 2026-06-01 to 2026-06-05 to test@example.com"

MOCK mode is enabled by default: emails are not sent, only printed to the terminal.
To send real emails, configure SMTP_* in .env and set MOCK_EMAIL=false.
"""

from __future__ import annotations

import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent

load_dotenv()

REPORT_DIR = Path(__file__).parent / "reports"
MOCK_EMAIL = os.getenv("MOCK_EMAIL", "true").lower() != "false"

ACCOUNTS = {
    "rs": {"name": "RS Account", "token_env": "ADX_RS_TOKEN"},
    "ap": {"name": "AP Account", "token_env": "ADX_AP_TOKEN"},
}

SYSTEM_PROMPT = """
You are an ADX report assistant. When the user asks to send a report, follow these rules:

1. Account must be rs or ap only
2. Dates must be in YYYY-MM-DD format; if the user does not specify dates, default to yesterday
3. Always call fetch_adx_report first to get the report file path
4. Then call send_report_email to send the email
5. If the recipient email is missing, ask the user; do not guess the email address
6. After completion, briefly summarize in English: account, date range, recipient, and send result
"""


def fetch_adx_report(
    account: Literal["rs", "ap"],
    start_date: str,
    end_date: str,
) -> str:
    """Fetch ADX report for rs or ap account and save it as a local CSV file.

    Args:
        account: Account code, must be 'rs' or 'ap'.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
    """
    if account not in ACCOUNTS:
        return f"Error: unknown account '{account}', must be rs or ap"

    account_info = ACCOUNTS[account]
    token = os.getenv(account_info["token_env"])

    # TODO: Replace with real ADX fetch logic, for example:
    # response = requests.get(
    #     "https://your-adx-api.example.com/report",
    #     params={"account": account, "start": start_date, "end": end_date},
    #     headers={"Authorization": f"Bearer {token}"},
    # )
    # response.raise_for_status()
    # report_path.write_bytes(response.content)

    REPORT_DIR.mkdir(exist_ok=True)
    report_path = REPORT_DIR / f"adx_{account}_{start_date}_{end_date}.csv"

    report_path.write_text(
        "\n".join(
            [
                "account,start_date,end_date,impressions,revenue",
                f"{account},{start_date},{end_date},1000,50.00",
                f"{account},{start_date},{end_date},1200,60.00",
            ]
        ),
        encoding="utf-8",
    )

    token_status = "configured" if token else "missing (mock data only)"
    return (
        f"Report saved to {report_path}. "
        f"Account={account_info['name']}, token={token_status}"
    )


def send_report_email(
    to_email: str,
    subject: str,
    report_path: str,
) -> str:
    """Send ADX report file to the specified email address.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        report_path: Local path to the report file returned by fetch_adx_report.
    """
    path = Path(report_path)
    if not path.exists():
        # If fetch_adx_report returned a description string, try to extract the path
        marker = "Report saved to "
        if marker in report_path:
            extracted = report_path.split(marker, 1)[1].split(". ", 1)[0]
            path = Path(extracted)

    if not path.exists():
        return f"Error: report file not found: {report_path}"

    if MOCK_EMAIL:
        return (
            f"[MOCK] Email prepared\n"
            f"  to: {to_email}\n"
            f"  subject: {subject}\n"
            f"  attachment: {path}\n"
            f"Set MOCK_EMAIL=false and configure SMTP_* in .env to send for real."
        )

    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
        return "Error: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM must be set in .env"

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(f"ADX report attached: {path.name}")

    msg.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="octet-stream",
        filename=path.name,
    )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)

    return f"Report sent to {to_email}"


agent = create_agent(
    model="deepseek:deepseek-chat",
    tools=[fetch_adx_report, send_report_email],
    system_prompt=SYSTEM_PROMPT,
)


def run(user_message: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
    last_message = result["messages"][-1]
    if hasattr(last_message, "content") and last_message.content:
        return last_message.content
    return str(last_message.content_blocks)


def print_message_trace(result: dict) -> None:
    print("\n--- Message trace ---")
    for index, message in enumerate(result["messages"]):
        print(f"\n[{index}] {type(message).__name__}")
        if message.content:
            print(f"  content: {message.content}")
        if getattr(message, "tool_calls", None):
            for tool_call in message.tool_calls:
                print(f"  tool_call: {tool_call['name']}({tool_call['args']})")
        if getattr(message, "tool_call_id", None):
            print(f"  tool_call_id: {message.tool_call_id}")


def run_once(user_input: str) -> None:
    print(f"User: {user_input}\n")
    print(f"MOCK_EMAIL={MOCK_EMAIL}\n")

    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    print_message_trace(result)
    print("\n--- Final reply ---")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    default_message = "Send yesterday's ADX report for the rs account to song@example.com"

    # Usage:
    # 1) With args: python adx_agent.py "Send the ap report to xxx@xx.com"
    # 2) Without args: python adx_agent.py then type interactively
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        run_once(user_input)
    else:
        print(f"MOCK_EMAIL={MOCK_EMAIL}\n")
        print("Interactive mode: the model will ask follow-up questions when info is missing.")
        print("Type exit to quit.\n")

        messages: list[dict] = [{"role": "user", "content": default_message}]

        first = input(f"Enter your first message (Enter for default: {default_message})> ").strip()
        if first:
            messages = [{"role": "user", "content": first}]

        while True:
            user_input = messages[-1]["content"]
            if user_input.lower() == "exit":
                sys.exit(0)

            result = agent.invoke({"messages": messages})
            print_message_trace(result)
            final_text = result["messages"][-1].content
            print("\n--- Final reply ---")
            print(final_text)

            next_user = input("\nContinue the conversation (type exit to quit)> ").strip()
            if not next_user:
                continue
            if next_user.lower() == "exit":
                sys.exit(0)

            messages = result["messages"]
            messages.append({"role": "user", "content": next_user})
