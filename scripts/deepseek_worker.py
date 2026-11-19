#!/usr/bin/env python3
"""
Autonomous worker engine for DeepSeek via OpenAI-compatible API.
Used by scripts/night.sh as --engine deepseek.
"""
import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from openai import OpenAI

DEFAULT_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.reformboss.com/v1")
DEFAULT_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-1acfb1049625af6b99b05a511bc8929beb5cd966b6395aec")
DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4.1-flash")

SYSTEM_PROMPT = """You are an autonomous coding worker named 'deepseek' in an active software project.
You work in your dedicated repository worktree.

Your instructions:
1. Fetch and read `night/TASKS.md` from the lead's branch.
2. Check for tasks assigned to `(deepseek)`, e.g. `- [ ] T... (deepseek) ...`.
3. If there are NO unfinished tasks tagged `(deepseek)`, output exactly "IDLE" and exit.
4. If there is a task tagged `(deepseek)`:
   - Make sure your branch is up to date with origin.
   - Implement the task cleanly and carefully.
   - Test your changes thoroughly (e.g. `uv run python -m auditenv.check`).
   - Record what you did in `night/LOG.md`.
   - Git add, commit with a concise message, and push your branch to origin.
   - Ensure the lead can merge or cherry-pick your work cleanly.
5. Work step-by-step using tools. When finished, summarize your work.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in the repository workspace and return stdout, stderr, and exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command line to run."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents at the given relative or absolute path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite full text content to a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "content": {"type": "string", "description": "The exact content to write."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": "Replace a specific target string with a replacement string in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "target": {"type": "string", "description": "Exact text to find and replace."},
                    "replacement": {"type": "string", "description": "New text to substitute."}
                },
                "required": ["path", "target", "replacement"]
            }
        }
    }
]

def execute_tool(name, args):
    try:
        if name == "run_command":
            cmd = args.get("command", "")
            proc = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180
            )
            out = proc.stdout
            err = proc.stderr
            if len(out) > 8000:
                out = out[:4000] + "\n...[truncated]...\n" + out[-4000:]
            if len(err) > 4000:
                err = err[:2000] + "\n...[truncated]...\n" + err[-2000:]
            return json.dumps({"exit_code": proc.returncode, "stdout": out, "stderr": err})

        elif name == "read_file":
            p = Path(args.get("path", "")).resolve()
            if not p.exists():
                return json.dumps({"error": f"File not found: {p}"})
            text = p.read_text(errors="replace")
            if len(text) > 16000:
                text = text[:8000] + "\n...[truncated]...\n" + text[-8000:]
            return json.dumps({"content": text})

        elif name == "write_file":
            p = Path(args.get("path", "")).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args.get("content", ""))
            return json.dumps({"success": True, "path": str(p), "bytes_written": len(args.get("content", ""))})

        elif name == "replace_in_file":
            p = Path(args.get("path", "")).resolve()
            if not p.exists():
                return json.dumps({"error": f"File not found: {p}"})
            text = p.read_text(errors="replace")
            target = args.get("target", "")
            replacement = args.get("replacement", "")
            if target not in text:
                return json.dumps({"error": f"Target string not found in {p}"})
            new_text = text.replace(target, replacement, 1)
            p.write_text(new_text)
            return json.dumps({"success": True, "path": str(p)})

        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def call_api_with_retry(client, model, messages, tools):
    for attempt in range(8):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                timeout=45.0
            )
        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["gateway_restarting", "500", "502", "503", "504", "bad_response_body", "connection", "timeout", "timed out"]):
                time.sleep(2 * (attempt + 1))
                continue
            raise
    raise RuntimeError("Failed after 8 retry attempts")

def main():
    parser = argparse.ArgumentParser(description="DeepSeek Worker CLI")
    parser.add_argument("-p", "--prompt", required=True, help="Task prompt")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base API URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API Key")
    parser.add_argument("--max-turns", type=int, default=25, help="Max tool turn iterations")
    parser.add_argument("--output-format", default="json", choices=["json", "text"], help="Output format")
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": args.prompt}
    ]

    final_text = ""
    for turn in range(args.max_turns):
        resp = call_api_with_retry(client, args.model, messages, TOOLS)
        choice = resp.choices[0]
        msg = choice.message
        messages.append(msg)

        if not msg.tool_calls:
            final_text = msg.content or ""
            break

        for tc in msg.tool_calls:
            fname = tc.function.name
            try:
                fargs = json.loads(tc.function.arguments)
            except Exception:
                fargs = {}
            t_res = execute_tool(fname, fargs)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": t_res
            })

    # If the response explicitly signals IDLE or no tasks
    if "IDLE" in final_text or "no tasks tagged" in final_text.lower():
        if args.output_format == "json":
            print(json.dumps({"status": "SUCCESS", "response": "IDLE"}))
        else:
            print("IDLE")
    else:
        if args.output_format == "json":
            print(json.dumps({"status": "SUCCESS", "response": final_text}))
        else:
            print(final_text)

if __name__ == "__main__":
    main()
