# oura-mcp

MCP server for Oura Ring — analyze your sleep, readiness, and HRV from Claude.

The Oura app shows you today's numbers. This server lets Claude see **weeks of data at once** — finding patterns, correlations, and trends that a single-day view can't surface.

## Requirements

- Python 3.10+
- [Oura Ring](https://ouraring.com/) with an active subscription
- [Claude Desktop](https://claude.ai/download) or [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Oura Personal Access Token (free) — [get one here](https://cloud.ouraring.com/personal-access-tokens)

## Quick start

```bash
git clone https://github.com/team-dulkin/oura-mcp.git
cd oura-mcp
./install.sh          # creates venv, installs deps, guides token setup
```

The installer prints a JSON snippet — paste it into your Claude config and restart Claude.

### Manual token setup

If you skipped the token step during install:

```bash
# Option A: config file
mkdir -p ~/.config/oura-mcp
echo "YOUR_TOKEN" > ~/.config/oura-mcp/token
chmod 600 ~/.config/oura-mcp/token

# Option B: environment variable
export OURA_TOKEN="YOUR_TOKEN"
```

## Available tools (20)

### Daily summaries

| Tool | Description |
|------|-------------|
| `oura_today` | Sleep + readiness + activity snapshot for one day |
| `oura_sleep` | Detailed sleep sessions: REM/deep/light durations, HR, HRV |
| `oura_readiness` | Readiness score, temperature deviation, contributors |
| `oura_activity` | Activity score, steps, calories, contributors |
| `oura_stress` | Daytime stress vs recovery seconds |
| `oura_resilience` | Long-term resilience level and contributors |
| `oura_spo2` | Overnight blood oxygen (SpO2) percentage |
| `oura_cardiovascular_age` | Predicted vascular age (18–100) |
| `oura_vo2_max` | VO2 max estimate |
| `oura_sleep_time` | Optimal bedtime recommendation |

### Detailed / session data

| Tool | Description |
|------|-------------|
| `oura_workouts` | Auto-detected workouts: type, HR, calories, distance |
| `oura_sessions` | Guided sessions: meditation, breathing, nap, relaxation |
| `oura_heart_rate` | 5-min HR samples with source (awake/rest/sleep/workout) |
| `oura_tags` | Enhanced tags with comments and duration |
| `oura_rest_mode` | Rest mode periods (sick days, recovery) |

### Trends (multi-day)

| Tool | Description |
|------|-------------|
| `oura_trends` | Sleep + readiness scores for last N days |
| `oura_temp_trend` | Temperature deviation trend for last N days |

### Account / device

| Tool | Description |
|------|-------------|
| `oura_personal_info` | Age, weight, height, biological sex |
| `oura_ring_configuration` | Ring model, color, size, firmware version |

## Example prompts

- "How did I sleep last week? Any patterns?"
- "Show my HRV and readiness trend for the past 30 days"
- "Compare my stress levels on workdays vs weekends this month"
- "What's my cardiovascular age? How does it compare to my real age?"
- "When should I go to bed tonight based on Oura's recommendation?"

## Troubleshooting

**Token not found**
Set `OURA_TOKEN` env var or create `~/.config/oura-mcp/token` with your PAT.

**HTTP 401 Unauthorized**
Your token expired or was revoked. Generate a new one at [cloud.ouraring.com/personal-access-tokens](https://cloud.ouraring.com/personal-access-tokens).

**HTTP 429 Rate Limited**
Oura allows 5,000 API calls/day. Wait and try again, or ask Claude to batch queries.

**Empty data for a specific date**
Oura's API treats `end_date` as exclusive. The server handles this correctly, but if you query the raw API directly, use `end_date = target_date + 1`.

**Tools not showing in Claude**
1. Verify the config snippet is in the right file and valid JSON
2. Fully quit Claude (Cmd+Q on Mac) and reopen
3. Check the server starts: `.venv/bin/python server.py` (should hang waiting for stdio input — Ctrl+C to exit)

## How it works

Two files, pure Python stdlib (no requests, no aiohttp):

- `client.py` — HTTP wrapper with a hardcoded `api.ouraring.com` base URL. Token loaded once at startup, never logged.
- `server.py` — MCP tool definitions using the [Anthropic MCP SDK](https://github.com/anthropics/python-sdk). Each tool maps to one or more Oura API v2 endpoints.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome.
