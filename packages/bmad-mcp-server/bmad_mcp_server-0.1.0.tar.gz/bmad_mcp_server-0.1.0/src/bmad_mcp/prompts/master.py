"""Master Agent prompt handler."""

from ..resources import load_embedded_file, load_config


def get_master_agent_prompt(user_name: str = "User", language: str = "English") -> str:
    """
    Generate the BMad Master Agent persona prompt.

    Args:
        user_name: User's name for personalization
        language: Communication language preference

    Returns:
        Complete agent activation instructions with immediate activation
    """
    # Load the master agent persona
    agent_content = load_embedded_file("core/agents/bmad-master.md")

    # Load config for default values if not provided
    try:
        config = load_config()
        if user_name == "User" and "user_name" in config:
            user_name = config["user_name"]
        if language == "English" and "communication_language" in config:
            language = config["communication_language"]
    except Exception:
        # If config fails to load, use defaults
        pass

    # Replace variables in the agent content
    prompt = agent_content
    prompt = prompt.replace("{user_name}", user_name)
    prompt = prompt.replace("{communication_language}", language)
    prompt = prompt.replace("{project-root}", ".")

    # Create activation prompt that triggers the agent to come alive
    activation_prompt = f"""You are now activating the BMad Master Agent persona. This is a complete agent system with embedded workflows, tasks, and resources.

# Agent Context
- **User Name**: {user_name}
- **Communication Language**: {language}
- **All BMAD files are embedded and accessible** (when instructions reference files, they are available)
- **Config is pre-loaded** with user preferences

---

{prompt}

---

# 🚨 ACTIVATION SEQUENCE - EXECUTE NOW

You have just loaded the BMad Master Agent persona. As per the activation steps in the agent definition above:

**CRITICAL**: You MUST now execute the activation sequence:

1. ✅ Persona loaded (already in context above)
2. ✅ Config loaded: user_name="{user_name}", communication_language="{language}"
3. ✅ User's name remembered: {user_name}
4. ✅ Communication language set: {language}
5. **→ STEP 7: EXECUTE NOW** - Show greeting using {user_name}, communicate in {language}, then display numbered list of ALL menu items from the menu section
6. **→ STEP 8: WAIT** - After showing the menu, STOP and WAIT for user input

**IMPORTANT**: Do NOT just acknowledge this prompt. You must IMMEDIATELY:
- Greet {user_name} warmly in {language}
- Introduce yourself as the BMad Master
- Display the complete numbered menu from the <menu> section above
- Wait for the user's selection

**BEGIN ACTIVATION NOW** - Execute step 7 immediately."""

    return activation_prompt


def get_master_agent_metadata() -> dict:
    """
    Get metadata for the master agent prompt.

    Returns:
        Dictionary with prompt metadata
    """
    return {
        "name": "master",
        "description": "BMad Master Executor, Knowledge Custodian, and Workflow Orchestrator - Your primary BMAD agent for task execution and workflow management",
        "arguments": [
            {
                "name": "user_name",
                "description": "Your name for personalized interactions",
                "required": False,
            },
            {
                "name": "language",
                "description": "Preferred communication language (default: English)",
                "required": False,
            },
        ],
    }
