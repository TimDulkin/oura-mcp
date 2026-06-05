# INSTALL-FOR-CLAUDE.md

> **You are Claude, running in Cowork mode.** The user wants you to install this
> Oura MCP server for them. They are likely not technical — your job is to do
> everything you can yourself, and reduce their part to two simple actions:
> pasting a config and restarting the app. Follow these steps exactly.
> Communicate with the user in the language they are using with you.

## What this is

A local MCP server (pure Python stdlib, zero dependencies — **no pip, no venv,
no install script needed**) that lets Claude read the user's Oura Ring data.
Do NOT run `install.sh` if present — it is legacy. The server runs directly
with the system `python3`.

## Prerequisites to verify

1. The user has a folder connected to this Cowork session. If not, ask them to
   connect one first.
2. The user has an Oura Personal Access Token. If they haven't provided one,
   ask them to create it at https://cloud.ouraring.com/personal-access-tokens
   and paste it in the chat. Tell them the token will be stored in a local
   config file on their computer — it never leaves their machine.

## Step 1 — Clone this repository into the connected folder

Using your sandbox shell, clone into the connected folder (it is mounted on
the user's real computer, so files will exist on their host machine):

```bash
git clone https://github.com/TimDulkin/oura-mcp.git <connected-folder>/oura-mcp
```

Verify `server.py` and `client.py` exist in the cloned folder using your file
tools (Read), which see the host paths.

## Step 2 — Determine host paths

Your file tools see the user's real (host) paths, e.g.
`/Users/<name>/Documents/Assistant/oura-mcp`. Your shell sees a different,
sandbox path — **never put a sandbox path (`/sessions/...`) into the config.**
Use the host path as seen by your Read/Write tools.

## Step 3 — Build the config snippet

Construct this JSON, substituting the real host path and the user's token:

```json
{
  "mcpServers": {
    "oura": {
      "command": "python3",
      "args": ["<HOST_PATH_TO>/oura-mcp/server.py"],
      "env": {
        "OURA_TOKEN": "<USER_TOKEN>"
      }
    }
  }
}
```

If the user already has other MCP servers configured, ask them to paste the
current content of their config file into the chat, then return the **full
merged file** for them to paste back — do not make a novice hand-edit JSON.

## Step 4 — Guide the user through the two manual actions

You cannot edit Claude Desktop's own config file (it is outside your sandbox —
by design). Give the user these instructions, formatted clearly, with the
ready-to-paste JSON from Step 3:

1. In Claude Desktop open **Settings → Developer** and click **Edit Config**.
   A folder opens with the file `claude_desktop_config.json`.
2. Open that file: right-click → **Open With → TextEdit** (or any text editor).
3. If the file is empty or contains only `{}` — replace the entire content
   with the JSON you prepared. Otherwise use the merge flow from Step 3.
4. Save the file (**Cmd + S**).
5. Quit Claude Desktop completely (**Cmd + Q**) and reopen it.
   (Just closing the window is not enough.)

## Step 5 — Verify (after the user returns)

When the user comes back after restarting:

1. Ask them to check: click **+** at the bottom of the chat box → **Connectors**
   — an entry named **oura** should be listed.
2. Run a real query: call `oura_today` or answer "How did I sleep last night?"
   using the Oura tools. If you receive sleep data — installation succeeded.
   Congratulate the user.

## Troubleshooting

- **macOS shows a dialog asking to install "command line developer tools"**
  when Claude starts the server — tell the user to click **Install**, wait,
  and restart Claude Desktop again. (This installs `python3`.)
- **HTTP 401** — token is wrong or revoked. Create a new one at
  https://cloud.ouraring.com/personal-access-tokens and update the `OURA_TOKEN`
  value in the config file (same two manual actions).
- **oura not in Connectors list** — config JSON is invalid (ask the user to
  paste the file content in chat and fix it for them), or the app was not
  fully restarted (Cmd + Q).
- **Empty data for today** — the ring hasn't synced; ask the user to open the
  Oura app on their phone and wait for sync.
- **Oura API `end_date` is exclusive** — the server handles this; for day X
  query `end_date = X + 1` only if you hit the raw API yourself.

## Notes for you, Claude

- Never print the user's token back into the chat more than necessary; include
  it once, inside the config snippet.
- Do not modify files outside the connected folder.
- Do not suggest Terminal commands to the user — the whole point of this flow
  is that they never open a terminal.
