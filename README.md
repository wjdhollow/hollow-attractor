# Hollow Attractor

Cross-session personal memory and task protocol for Claude, implemented as an MCP server.

Claude has no memory between sessions. Hollow Attractor gives it a persistent, structured workspace — tracked in a local git repo, read and written through MCP tools, never sent anywhere.

---

## How it works

Hollow Attractor runs as a local MCP server connected to Claude Desktop. Each session, Claude loads your current state and picks up where it left off — open tasks, decisions, questions, and a running log.

Everything lives in `~/.hollow-attractor/` as plain text files under git. No cloud, no account, no sync. Your data stays on your machine.

### Key concepts

| Term | Meaning |
|------|---------|
| **Worldline** | A named workspace — one project, one scope |
| **Attractor** | The global context; entry point for each session |
| **Ship Log** | Global index of all worldlines and recent updates |
| **Divergence** | A tracked relationship between two worldlines |
| **Anneal** | Manual compaction of a worldline with optional intent |
| **Imprint** | Plain-text state export for backup or migration |

---

## Install

**Requirements:** Python 3.10+, git, [Claude Desktop](https://claude.ai/download)

```bash
pip install hollow-attractor
hollow init
```

Then add the MCP server to Claude Desktop. Edit `claude_desktop_config.json`:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hollow-attractor": {
      "command": "hollow"
    }
  }
}
```

Restart Claude Desktop.

---

## Usage

Start a session in Claude Desktop and say:

> *hollow, start*

Claude will load the `hollow_start` prompt, read your Ship Log, and resume your current worldline.

From there you can create worldlines, add tasks, log decisions, track open questions, and commit state — all through conversation.

See [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) for the full protocol and [`SCHEMAS.md`](SCHEMAS.md) for file formats.

---

## Status

V1 is complete and in active daily use. The core protocol is stable.

Planned next:
- `pip install hollow-attractor` + `hollow init` CLI
- Homebrew formula
- Hosted sync (V2)

---

## Support

If Hollow Attractor is useful to you, consider sponsoring development:

[![GitHub Sponsors](https://img.shields.io/github/sponsors/wjdhollow?style=flat&label=Sponsor)](https://github.com/sponsors/wjdhollow)

---

## License

MIT
