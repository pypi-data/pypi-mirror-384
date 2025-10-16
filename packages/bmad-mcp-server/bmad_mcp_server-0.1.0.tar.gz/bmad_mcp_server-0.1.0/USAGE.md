# BMAD MCP Server - Usage Guide

## Quick Start

### 1. Installation

```bash
cd bmad-mcp-server
uv venv
uv pip install -e .
```

### 2. Test the Server

Test that the server is working:

```bash
# Run the server in dev mode with MCP Inspector
uv run mcp dev src/bmad_mcp/server.py
```

This will open the MCP Inspector in your browser where you can:
- See available tools
- Run the `bmad` tool to see the greeting
- View the full output

### 3. Configure Claude Desktop

#### Option A: Manual Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

**Important:** Replace the path with your actual path to `bmad-mcp-server`.

#### Option B: Automatic Installation

```bash
cd /Users/mkellerman/GitHub/bmad-test-repo/bmad-mcp-server
uv run mcp install src/bmad_mcp/server.py --name "BMAD Personas"
```

### 4. Restart Claude Desktop

Quit and reopen Claude Desktop completely.

### 5. Use the Agent Persona

In a new Claude Desktop chat, open the MCP tools panel (plug icon) and execute the `bmad` tool. You can set the optional `user_name`, `language`, and `selection` arguments. The tool returns a greeting and menu; with `selection`, it executes that menu item using the embedded handlers (e.g., list workflows, run party-mode).

## What Happens When You Run `bmad`?

1. The MCP server loads the embedded `bmad-master.md` agent file
2. It loads config and substitutes variables ({user_name}, {language}, {project-root})
3. It parses the `<menu>` and renders a numbered list
4. With `selection`, it executes the matched menu item (action/workflow)

## Expected Output

After running `bmad`, you should see:

```
# BMAD Master Agent - Activated via MCP Server

**User:** [Your Name]
**Language:** English

**Important Notes:**
- All BMAD framework files are embedded in this MCP server
- When instructions reference {project-root}/bmad/..., those files are available as embedded resources
- The config.yaml is pre-loaded with your preferences
- You have access to all workflows, tasks, and agent definitions

---

<!-- Powered by BMAD-CORE™ -->

# BMad Master Executor, Knowledge Custodian, and Workflow Orchestrator

[Complete agent persona definition follows...]
```

## Expected Output (bmad tool)

Running the `bmad` tool returns something like:

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

Examples with selection:
- `selection: "2"` → Lists tasks from the embedded manifest (if any)
- `selection: "*list-workflows"` → Lists workflows from the embedded manifest
- `selection: "*party-mode"` → Loads the core workflow engine and initializes Party Mode with agent roster

## Troubleshooting

### Server Not Showing Up in Claude Desktop

1. Check the logs:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

2. Verify server runs manually:
   ```bash
   cd bmad-mcp-server
   uv run bmad-mcp-server
   ```

   Press Ctrl+C to stop. If it starts without errors, the server is working.

3. Check your config path is correct in `claude_desktop_config.json`

### Tool Not Appearing

1. Ensure the server is listed in connected MCP servers (plug icon)
2. Restart Claude Desktop completely
3. Check `~/Library/Logs/Claude/mcp*.log` for errors

### Import Errors

If you see Python import errors:

```bash
cd bmad-mcp-server
uv venv --force  # Recreate venv
uv pip install -e .  # Reinstall
```

## Advanced Usage

### Customizing Default Values

Edit `src/bmad_mcp/embedded/core/config.yaml` to set your defaults:

```yaml
user_name: Your Name
communication_language: English
output_folder: '{project-root}/docs'
```

These values are used when no arguments are provided to the tool.

### Using in Claude Code (VS Code Extension)

Add to your VS Code settings or workspace settings:

```json
{
  "mcp.servers": {
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

Then run the `bmad` tool in Claude Code.

## Next Steps

Once the master agent is loaded:

1. Say hello - the agent will greet you and show the menu
2. Explore available commands (type `*help`)
3. List workflows (`*list-workflows`)
4. Execute tasks (`*list-tasks`)

The agent has access to all embedded BMAD resources and can execute workflows, manage tasks, and orchestrate your work.
