# oura-mcp

MCP server for Oura Ring — analyze your sleep, readiness, and HRV from Claude.

The Oura app shows you today's numbers. This server lets Claude see **weeks of data at once** — finding patterns, correlations, and trends that a single-day view can't surface.

**Zero dependencies.** Pure Python stdlib — no pip, no venv, no install script. If you have `python3`, it runs.

## Requirements

- [Oura Ring](https://ouraring.com/) with an active subscription
- [Claude Desktop](https://claude.com/download) (paid plan for Cowork) or [Claude Code](https://code.claude.com)
- Oura Personal Access Token (free) — [get one here](https://cloud.ouraring.com/personal-access-tokens)
- Python 3.9+ (preinstalled on macOS with developer tools; macOS will offer to install it on first run)

## Install with Claude Cowork (no terminal)

The easiest way — let Claude install it for you. In a Cowork session with a connected folder, paste:

> Install the Oura MCP server from this repository: https://github.com/TimDulkin/oura-mcp
> Follow INSTALL-FOR-CLAUDE.md from the repository.
> Here is my Oura token: YOUR_TOKEN

Claude clones the repo into your folder, prepares the config with your paths and token, and walks you through the two remaining clicks (paste config, restart Claude). See [INSTALL-FOR-CLAUDE.md](INSTALL-FOR-CLAUDE.md) for what Claude does under the hood.

## Manual install

Clone the repo anywhere:

```bash
git clone https://github.com/TimDulkin/oura-mcp.git
```

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`, reachable via **Settings → Developer → Edit Config**):

```json
{
  "mcpServers": {
    "oura": {
      "command": "python3",
      "args": ["/ABSOLUTE/PATH/TO/oura-mcp/server.py"],
      "env": {
        "OURA_TOKEN": "YOUR_TOKEN"
      }
    }
  }
}
```

For Claude Code, add the same `mcpServers` block to `.claude/settings.json`.

Then fully restart Claude (Cmd+Q) and try: *"How did I sleep last night?"*

### Token alternatives

Instead of the `env` block you can store the token in a file:

```bash
mkdir -p ~/.config/oura-mcp
echo "YOUR_TOKEN" > ~/.config/oura-mcp/token
chmod 600 ~/.config/oura-mcp/token
```

## Available tools (19)

### Daily summaries

| Tool                      | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| `oura_today`              | Sleep + readiness + activity snapshot for one day          |
| `oura_sleep`              | Detailed sleep sessions: REM/deep/light durations, HR, HRV |
| `oura_readiness`          | Readiness score, temperature deviation, contributors       |
| `oura_activity`           | Activity score, steps, calories, contributors              |
| `oura_stress`             | Daytime stress vs recovery seconds                         |
| `oura_resilience`         | Long-term resilience level and contributors                |
| `oura_spo2`               | Overnight blood oxygen (SpO2) percentage                   |
| `oura_cardiovascular_age` | Predicted vascular age (18–100)                            |
| `oura_vo2_max`            | VO2 max estimate                                           |
| `oura_sleep_time`         | Optimal bedtime recommendation                             |

### Detailed / session data

| Tool              | Description                                             |
| ----------------- | ------------------------------------------------------- |
| `oura_workouts`   | Auto-detected workouts: type, HR, calories, distance    |
| `oura_sessions`   | Guided sessions: meditation, breathing, nap, relaxation |
| `oura_heart_rate` | 5-min HR samples with source (awake/rest/sleep/workout) |
| `oura_tags`       | Enhanced tags with comments and duration                |
| `oura_rest_mode`  | Rest mode periods (sick days, recovery)                 |

### Trends (multi-day)

| Tool              | Description                                 |
| ----------------- | ------------------------------------------- |
| `oura_trends`     | Sleep + readiness scores for last N days    |
| `oura_temp_trend` | Temperature deviation trend for last N days |

### Account / device

| Tool                      | Description                               |
| ------------------------- | ----------------------------------------- |
| `oura_personal_info`      | Age, weight, height, biological sex       |
| `oura_ring_configuration` | Ring model, color, size, firmware version |

## Example prompts

- "How did I sleep last week? Any patterns?"
- "Show my HRV and readiness trend for the past 30 days"
- "Compare my stress levels on workdays vs weekends this month"
- "What's my cardiovascular age? How does it compare to my real age?"
- "When should I go to bed tonight based on Oura's recommendation?"

## Troubleshooting

**Token not found** — Set `OURA_TOKEN` in the config `env` block, or create `~/.config/oura-mcp/token` with your PAT.

**HTTP 401 Unauthorized** — Your token expired or was revoked. Generate a new one at [cloud.ouraring.com/personal-access-tokens](https://cloud.ouraring.com/personal-access-tokens).

**HTTP 429 Rate Limited** — Oura allows 5,000 API calls/day. Wait and try again, or ask Claude to batch queries.

**Empty data for a specific date** — Oura's API treats `end_date` as exclusive. The server handles this correctly, but if you query the raw API directly, use `end_date = target_date + 1`. For today's data, make sure the ring has synced with the Oura app first.

**macOS asks to install "command line developer tools"** — Click Install. This is a one-time setup that provides `python3`. Restart Claude afterwards.

**Tools not showing in Claude**

1. Verify the config snippet is in the right file and valid JSON
2. Fully quit Claude (Cmd+Q on Mac) and reopen
3. Check the server starts: `python3 server.py` (should hang waiting for stdio input — Ctrl+C to exit)

## How it works

Two files, pure Python stdlib (no requests, no aiohttp, no MCP SDK):

- `client.py` — HTTP wrapper with a hardcoded `api.ouraring.com` base URL. Token loaded once at first use, never logged.
- `server.py` — tool definitions plus a minimal implementation of the [MCP](https://modelcontextprotocol.io/) stdio transport (newline-delimited JSON-RPC 2.0). Each tool maps to one or more Oura API v2 endpoints.

The zero-dependency design is deliberate: it means Claude itself can install this server for non-technical users — no pip, no venv, nothing to compile. See [INSTALL-FOR-CLAUDE.md](INSTALL-FOR-CLAUDE.md).

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome.
