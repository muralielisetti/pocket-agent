#!/usr/bin/env python3
"""pocket-agent: a minimal ReAct-style tool-using agent on top of a local Ollama model."""

import json
import subprocess
import sys
from pathlib import Path

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"
MAX_TURNS = 8

SYSTEM_PROMPT = (
    "You are pocket-agent, a careful local assistant that can use tools to "
    "accomplish tasks on this machine. Think step by step. Use a tool when "
    "it helps you make progress. When you have the final answer, reply with "
    "plain text and no further tool calls."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command on the user's Mac and return its stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file, overwriting it if it exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "content": {"type": "string", "description": "Content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path."}
                },
                "required": ["path"],
            },
        },
    },
]


def run_shell(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return (result.stdout + result.stderr).strip() or "(no output)"
    except Exception as e:
        return f"error: {e}"


def read_file(path: str) -> str:
    try:
        return Path(path).expanduser().read_text()
    except Exception as e:
        return f"error: {e}"


def write_file(path: str, content: str) -> str:
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"wrote {len(content)} bytes to {p}"
    except Exception as e:
        return f"error: {e}"


def list_dir(path: str) -> str:
    try:
        return "\n".join(sorted(p.name for p in Path(path).expanduser().iterdir()))
    except Exception as e:
        return f"error: {e}"


TOOL_IMPL = {
    "run_shell": run_shell,
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
}


def call_model(messages):
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]


def run(task: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for turn in range(1, MAX_TURNS + 1):
        message = call_model(messages)
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            print(message.get("content", "").strip())
            return

        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)

            print(f"[turn {turn}] -> {name}({args})")
            impl = TOOL_IMPL.get(name)
            output = impl(**args) if impl else f"error: unknown tool {name}"
            print(f"[turn {turn}] <- {output[:300]}")

            messages.append({"role": "tool", "content": str(output)})

    print("(reached max turns without a final answer)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python agent.py "your task here"')
        sys.exit(1)
    run(" ".join(sys.argv[1:]))
