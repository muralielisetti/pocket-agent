# pocket-agent

A minimal ReAct-style agent in ~150 lines of Python. No framework — just a
loop that lets a local LLM call tools (shell, file read/write, list dir)
until it has a final answer. Everything runs locally via [Ollama](https://ollama.com).

## Why

Most agent tutorials hide the loop behind a framework. This repo is the
loop, in plain Python, so you can see exactly how "reason -> act -> observe"
works under the hood.

## Requirements

- macOS (or any OS with Ollama support)
- [Ollama](https://ollama.com) — `brew install ollama`
- Python 3.9+

## Setup

```bash
brew install ollama
brew services start ollama
ollama pull qwen2.5:3b

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/python agent.py "list the files in the current directory and tell me which one is largest"
```

The agent will print each tool call it makes and its result, then the final
answer.

## How it works

1. The task is sent to the model along with a list of available tools
   (JSON schema, OpenAI-style function calling, supported natively by Ollama).
2. If the model responds with a tool call, `agent.py` executes it locally
   and feeds the result back as a `tool` message.
3. This repeats (up to `MAX_TURNS`) until the model responds with plain text
   instead of a tool call — that's the final answer.

## Safety note

The `run_shell` tool executes arbitrary shell commands with your user
permissions. This is intentional (it's what makes the agent useful) but
means you should only give it tasks you'd be comfortable running yourself,
and review what it's about to do.

## License

MIT
