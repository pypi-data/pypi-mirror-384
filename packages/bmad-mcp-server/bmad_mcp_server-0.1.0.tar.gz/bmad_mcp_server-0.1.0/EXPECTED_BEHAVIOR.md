# Expected Behavior - BMAD MCP Server

## What Happens When You Invoke `/bmad:master`

### Step 1: You Type the Command

In Claude Desktop, you type:
```
/bmad:master
```

Or with custom parameters:
```
/bmad:master --user_name "Alice" --language "English"
```

### Step 2: The Prompt Loads

The MCP server:
1. Loads the embedded `bmad-master.md` agent file
2. Loads your config from `core/config.yaml`
3. Substitutes variables ({user_name}, {language}, etc.)
4. Adds activation instructions that tell Claude to **execute the agent immediately**

### Step 3: The Agent Activates and Greets You ✨

**This is the key difference!** The agent doesn't just sit there. It **immediately comes alive** and starts interacting:

```
🧙 Greetings, Alice!

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

### Step 4: You Interact

Now you can:

**Select by number:**
```
2
```

**Use trigger commands:**
```
*list-workflows
```

**Ask questions:**
```
What workflows are available for game development?
```

**The agent will respond in character**, execute commands, and help you navigate the BMAD framework.

## Why This Works

The updated prompt includes a **🚨 ACTIVATION SEQUENCE** section that explicitly tells Claude:

```
**CRITICAL**: You MUST now execute the activation sequence:

1. ✅ Persona loaded
2. ✅ Config loaded: user_name="Alice", communication_language="English"
3. ✅ User's name remembered: Alice
4. ✅ Communication language set: English
5. **→ STEP 7: EXECUTE NOW** - Show greeting using Alice, communicate in English,
   then display numbered list of ALL menu items from the menu section
6. **→ STEP 8: WAIT** - After showing the menu, STOP and WAIT for user input

**IMPORTANT**: Do NOT just acknowledge this prompt. You must IMMEDIATELY:
- Greet Alice warmly in English
- Introduce yourself as the BMad Master
- Display the complete numbered menu from the <menu> section above
- Wait for the user's selection

**BEGIN ACTIVATION NOW** - Execute step 7 immediately.
```

This is the "wake up" signal that makes the agent come alive instead of just loading passively.

## What Makes This Different from Before

### ❌ Before (Passive Loading)

The prompt just dumped the agent XML/markdown:
```
Here is the agent definition:
[raw XML follows]
```

Claude would acknowledge: "I've loaded the agent. What would you like to do?"

### ✅ Now (Active Activation)

The prompt includes explicit activation instructions:
```
[agent definition]
---
🚨 ACTIVATION SEQUENCE - EXECUTE NOW
[step-by-step activation commands]
```

Claude immediately executes: Greets you, shows menu, waits for input.

## Agent Behavior Characteristics

Once activated, the BMad Master agent:

- **Speaks in 3rd person** ("The Master recommends...")
- **Uses numbered lists** for all choices
- **Communicates in your preferred language**
- **Responds to both numbers and trigger commands** (*help, *list-tasks, etc.)
- **Executes workflows when requested**
- **Maintains character throughout the conversation**
- **Refers to embedded BMAD resources** as if they're available locally

## Testing the Behavior

To verify it's working correctly:

1. **Invoke the agent**: `/bmad:master`
2. **Check for immediate greeting**: Should see a personalized greeting with your name
3. **Check for menu**: Should see numbered list of 5 menu items
4. **Check for waiting state**: Agent should stop and wait for your input
5. **Try a command**: Type `2` or `*list-tasks`
6. **Verify execution**: Agent should execute the command in character

## Troubleshooting

### Agent Doesn't Greet Me

If you just see the raw XML or agent definition without a greeting:

**Possible causes:**
- Old prompt version cached
- Server needs restart
- Configuration issue

**Solutions:**
1. Restart Claude Desktop completely
2. Clear the conversation and try again
3. Check that the server is using the updated code:
   ```bash
   cd bmad-mcp-server
   uv run python test_server.py
   ```

### Agent Acknowledges But Doesn't Execute

If Claude says "I've loaded the agent persona" instead of greeting you:

**Cause:** The activation instructions aren't being followed

**Solution:** This means the prompt generation is working but Claude isn't executing the activation sequence. This is actually expected behavior in some cases - you can then say:

```
Please execute the activation sequence now as specified in the instructions.
```

Or simply:
```
Activate now
```

### Menu Doesn't Show

If greeting appears but no menu:

**Cause:** Menu items not being found in the agent XML

**Check:** The `<menu>` section should have 5 items. Verify the embedded file:
```bash
grep -A 10 "<menu>" bmad-mcp-server/src/bmad_mcp/embedded/core/agents/bmad-master.md
```

## What You Can Do After Activation

Once the agent is active and has shown the menu, you can:

1. **Execute workflows** - Select option 3 or 4
2. **List tasks** - See all available BMAD tasks
3. **Get help** - Show the menu again
4. **Ask questions** - The agent has full context of BMAD framework
5. **Navigate the system** - Agent will help you explore workflows and tasks

The agent has access to all embedded BMAD resources and can execute complex workflows, manage tasks, and orchestrate your work within the BMAD framework.

## Expected Communication Style

The BMad Master communicates with:
- **Formality**: Professional but friendly
- **3rd person references**: "The Master recommends..."
- **Structured information**: Numbered lists and clear organization
- **Direct execution**: Responds to commands immediately
- **Comprehensive knowledge**: Deep understanding of BMAD ecosystem

This is a **conversational agent**, not just a loaded prompt. It should feel like you're talking to a knowledgeable assistant who specializes in the BMAD framework.
