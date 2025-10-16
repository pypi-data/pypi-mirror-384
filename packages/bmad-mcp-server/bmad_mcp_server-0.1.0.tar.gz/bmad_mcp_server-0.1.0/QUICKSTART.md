# BMAD MCP Server - Quick Start Guide

## ✅ Installation Complete!

Your BMAD MCP Server is installed and configured for Claude Desktop.

## 🚀 Next Steps

### 1. Restart Claude Desktop

**IMPORTANT**: You must completely quit and restart Claude Desktop for the MCP server to be detected.

**How to restart on macOS**:
1. Click "Claude" in the menu bar
2. Select "Quit Claude Desktop" (or press ⌘Q)
3. Open Claude Desktop again from Applications

### 2. Verify Server is Running

After restarting Claude Desktop:

1. Open a new conversation
2. Look for the 🔌 (plug) icon in the bottom-right corner
3. Click it to see "Connected MCP Servers"
4. You should see **"bmad-personas"** listed

**If you don't see it**:
- Check the logs: `tail -f ~/Library/Logs/Claude/mcp*.log`
- Verify the server runs manually: `cd bmad-mcp-server && uv run bmad-mcp-server`

### 3. Run the BMAD Tool

In any Claude Desktop conversation, open the MCP tools panel (plug icon) and execute the `bmad` tool (optional args: `user_name`, `language`, `selection`).

**What happens**:
- The tool loads the embedded Master persona
- It greets you and shows its menu (parsed from the persona)

### 4. Customize (Optional)

You can pass custom parameters in the tool pane: `user_name`, `language`, and optionally `selection`.

Or edit the defaults in:
```
bmad-mcp-server/src/bmad_mcp/embedded/core/config.yaml
```

## 🎯 Expected Result

After running `bmad`, the agent will greet you in the Master persona and show a numbered menu.

You should see something like:

```
🧙 Greetings, [Your Name]!

The BMad Master stands ready to serve. Master-level expertise in the BMAD Core
Platform at your command, with comprehensive knowledge of all resources, tasks,
and workflows.

The Master presents the following capabilities:

1. *help - Show numbered menu
2. *list-tasks - List Available Tasks
3. *list-workflows - List Workflows
4. *party-mode - Group chat with all agents
5. *exit - Exit with confirmation

Select a numbered option or use the trigger command. The Master awaits your directive.
```

**What just happened:**
- ✅ The agent persona loaded
- ✅ Your config was read (name, language)
- ✅ The agent **activated itself** and greeted you
- ✅ The menu is displayed
- ✅ The agent is waiting for your command

**The agent is now alive and ready to interact!**

## 📝 Available Commands

Once the agent is active, you can use:

- `*help` - Show the menu
- `*list-tasks` - List all available tasks
- `*list-workflows` - List all workflows
- `*party-mode` - Group chat with all agents
- `*exit` - Exit the agent mode

## 🔧 Troubleshooting

### Server Not Appearing

**Check the config**:
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Should show:
```json
{
  "mcpServers": {
    "bmad-personas": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/mkellerman/GitHub/bmad-test-repo/bmad-mcp-server",
        "bmad-mcp-server"
      ]
    }
  }
}
```

**Test the server manually**:
```bash
cd /Users/mkellerman/GitHub/bmad-test-repo/bmad-mcp-server
uv run bmad-mcp-server
```

Press Ctrl+C to stop. If it starts without errors, the server works.

**Check logs**:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

### Tool Not Showing

1. Ensure the server appears under connected MCP servers (plug icon)
2. Restart Claude Desktop again

### Import Errors

If you see errors in the logs:

```bash
cd /Users/mkellerman/GitHub/bmad-test-repo/bmad-mcp-server
uv venv --force
uv pip install -e .
```

Then restart Claude Desktop.

## 📚 More Information

- **Full Documentation**: See [README.md](README.md)
- **Usage Guide**: See [USAGE.md](USAGE.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Run Tests**: `uv run python test_server.py`

## 🎉 You're All Set!

Your BMAD MCP Server is ready to use. Just restart Claude Desktop and run the `bmad` tool to activate the agent!

---

**Configuration Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Server Location**: `/Users/mkellerman/GitHub/bmad-test-repo/bmad-mcp-server`
**Test Command**: `cd bmad-mcp-server && uv run python test_server.py`
