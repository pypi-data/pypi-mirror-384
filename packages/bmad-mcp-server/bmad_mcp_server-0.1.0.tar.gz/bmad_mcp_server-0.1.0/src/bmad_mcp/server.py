"""BMAD MCP Server - Main entry point."""

import asyncio
from mcp.server.fastmcp import FastMCP
from .resources import load_embedded_file, load_config
import re
import xml.etree.ElementTree as ET

# Initialize FastMCP server
mcp = FastMCP("BMAD Agent Personas")


def main():
    """Entry point for the MCP server."""
    # Run the server with stdio transport (default)
    mcp.run()


@mcp.tool()
def bmad(
    user_name: str = "User",
    language: str = "English",
    selection: str | None = None,
) -> str:
    """
    Single entrypoint tool that loads the embedded BMad Master persona and
    greets the user with a dynamic menu. Optionally executes a selected menu
    item (e.g., *list-workflows, *party-mode).

    Args:
        user_name: Your name for personalized interactions
        language: Preferred communication language (default: English)
        selection: Optional number or trigger to execute a menu item

    Returns:
        A greeting from the Master persona with its capabilities menu or the
        result of executing the selected menu item.
    """
    # Step 2: Load config (mandatory). If this fails, STOP and report error.
    try:
        cfg = load_config()
    except Exception as e:
        return f"ERROR: Failed to load core/config.yaml — {e}"

    if (not user_name or user_name == "User") and cfg.get("user_name"):
        user_name = cfg["user_name"]
    if (not language or language == "English") and cfg.get("communication_language"):
        language = cfg["communication_language"]

    # Load agent XML block from embedded file and parse menu/items dynamically
    agent_md = load_embedded_file("core/agents/bmad-master.md")
    m = re.search(r"```xml\s*(.*?)\s*```", agent_md, re.S)
    if not m:
        return "ERROR: Could not find agent XML block in bmad-master.md"

    xml_text = m.group(1)
    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        return f"ERROR: Failed to parse agent XML — {e}"

    agent_name = root.attrib.get("name", "BMad Master")
    agent_icon = root.attrib.get("icon", "🧙")

    menu_el = root.find(".//menu")
    if menu_el is None:
        return "ERROR: Agent XML has no <menu> section"

    items: list[dict] = []
    for item in menu_el.findall("item"):
        cmd = item.attrib.get("cmd", "").strip()
        desc = (item.text or "").strip()
        attrs = {k: v for k, v in item.attrib.items() if k != "cmd"}
        if cmd and desc:
            items.append({"cmd": cmd, "desc": desc, "attrs": attrs})

    if not items:
        return "ERROR: Agent <menu> contains no items"

    def show_menu() -> str:
        lines: list[str] = []
        lines.append(f"{agent_icon} The {agent_name} greets {user_name}.")
        lines.append(f"Communication Language: {language}")
        lines.append("")
        for idx, it in enumerate(items, start=1):
            lines.append(f"{idx}. {it['cmd']} - {it['desc']}")
        lines.append("")
        lines.append("Awaiting selection (enter a number or trigger).")
        return "\n".join(lines)

    def resolve_embedded_path(path: str) -> str:
        # Replace variable placeholders and normalize embedded location
        p = path.replace("{project-root}/", "").replace("{project_root}/", "")
        if p.startswith("bmad/"):
            p = p[len("bmad/"):]
        if p.startswith("src/"):
            p = p[len("src/"):]
        # Some yaml points to src/core/... keep only after first '/core' or '/bmm' etc.
        p = p.lstrip("/")
        return p

    def handle_action(action_text: str) -> str:
        txt = action_text.strip()
        # Action referencing internal prompt id (not used in current persona)
        if txt.startswith("#"):
            return f"NOT IMPLEMENTED: action reference '{txt}' not found in agent."

        # list all tasks from PATH
        m_tasks = re.search(r"list all tasks from\s+(.+)$", txt, re.I)
        if m_tasks:
            raw = m_tasks.group(1).strip()
            rel = resolve_embedded_path(raw)
            try:
                content = load_embedded_file(rel)
            except Exception as e:
                return f"ERROR: Unable to load tasks manifest '{raw}' → {e}"
            import csv, io
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            if not rows:
                return "No tasks found in manifest."
            out = ["Available Tasks:"]
            for i, r in enumerate(rows, 1):
                name = r.get("name") or "(unnamed)"
                desc = (r.get("description") or "").strip()
                mod = (r.get("module") or "").strip()
                out.append(f"{i}. {name} — {desc} [{mod}]")
            return "\n".join(out)

        # list all workflows from PATH
        m_wf = re.search(r"list all workflows from\s+(.+)$", txt, re.I)
        if m_wf:
            raw = m_wf.group(1).strip()
            rel = resolve_embedded_path(raw)
            try:
                content = load_embedded_file(rel)
            except Exception as e:
                return f"ERROR: Unable to load workflow manifest '{raw}' → {e}"
            import csv, io
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            if not rows:
                return "No workflows found in manifest."
            out = ["Available Workflows:"]
            for i, r in enumerate(rows, 1):
                name = r.get("name") or "(unnamed)"
                desc = (r.get("description") or "").strip()
                mod = (r.get("module") or "").strip()
                path = (r.get("path") or "").strip()
                out.append(f"{i}. {name} — {desc} [{mod}] ({path})")
            return "\n".join(out)

        # Default: echo instruction text
        return f"Executing: {txt}"

    def handle_workflow(workflow_path: str) -> str:
        raw = workflow_path.strip()
        if raw.lower() == "todo":
            return "Workflow not implemented yet (path is 'todo')."

        rel = resolve_embedded_path(raw)
        # Load core workflow engine xml
        try:
            core_xml = load_embedded_file("core/tasks/workflow.xml")
        except Exception as e:
            return f"ERROR: Unable to load core workflow engine → {e}"

        # Load workflow yaml
        try:
            import yaml
            wf_yaml = load_embedded_file(rel)
            wf = yaml.safe_load(wf_yaml) or {}
        except Exception as e:
            return f"ERROR: Unable to load workflow config '{raw}' → {e}"

        # Resolve important paths
        agent_manifest_path = resolve_embedded_path(str(wf.get("agent_manifest", "")).replace("{project_root}", "{project-root}"))
        agent_overrides_glob = resolve_embedded_path(str(wf.get("agent_overrides", "")).replace("{project_root}", "{project-root}"))
        instructions_path = resolve_embedded_path(str(wf.get("instructions", "")).replace("{project_root}", "{project-root}"))

        # Step 1: Load agent roster
        import csv, io, glob
        roster = []
        agents_loaded = 0
        overrides_applied = 0
        if agent_manifest_path:
            try:
                manifest_content = load_embedded_file(agent_manifest_path)
                reader = csv.DictReader(io.StringIO(manifest_content))
                for row in reader:
                    if not row:
                        continue
                    roster.append({k: (v or "").strip() for k, v in row.items()})
                agents_loaded = len(roster)
            except Exception as e:
                return f"ERROR: Unable to load agent manifest '{agent_manifest_path}' → {e}"

        # Overrides (optional): look up files matching the pattern under embedded
        # We don't write files; just note whether any exist.
        # Since load_embedded_file doesn't support globs, we will best-effort detect the folder.
        if agent_overrides_glob and "*" in agent_overrides_glob:
            # Try to list via filesystem under embedded
            from pathlib import Path
            embedded_dir = Path(__file__).parent / "embedded"
            # Convert glob path to filesystem
            glob_path = str(embedded_dir / agent_overrides_glob)
            for _ in glob.glob(glob_path):
                overrides_applied += 1

        # Step 2: Announce and list participants
        lines: list[str] = []
        lines.append("Loaded core workflow engine (workflow.xml)")
        lines.append(f"Workflow: {wf.get('name', '(unnamed)')} — {wf.get('description', '')}")
        lines.append("")
        lines.append("🎉 PARTY MODE ACTIVATED! 🎉")
        lines.append("All agents are here for a group discussion!")
        lines.append("")
        lines.append("Participating agents:")
        if roster:
            for r in roster:
                display = r.get("displayName") or r.get("name") or "(unknown)"
                title = r.get("title") or ""
                role = r.get("role") or ""
                lines.append(f"- {display} ({title}): {role}")
        else:
            lines.append("- (none found)")
        lines.append("")
        lines.append(f"{agents_loaded} agents ready to collaborate!")
        lines.append("")
        lines.append("What would you like to discuss with the team?")
        lines.append("[Awaiting user response…]")
        return "\n".join(lines)

    def select_item(sel: str) -> list[dict]:
        s = sel.strip()
        # Number → execute menu item[n]
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= len(items):
                return [items[idx - 1]]
            return []
        # Text → case-insensitive substring match against cmd and desc
        s_low = s.lower()
        matches = [it for it in items if s_low in it["cmd"].lower() or s_low in it["desc"].lower()]
        return matches

    # If no selection provided, just show greeting + menu and wait
    if not selection:
        return show_menu()

    # Find matching menu item(s)
    matches = select_item(selection)
    if not matches:
        return f"Not recognized: '{selection}'. Try a number or trigger."
    if len(matches) > 1:
        opts = ", ".join(f"{m['cmd']}" for m in matches[:5])
        more = "" if len(matches) <= 5 else f" (+{len(matches)-5} more)"
        return f"Multiple matches: {opts}{more}. Please clarify."

    item = matches[0]
    attrs = item["attrs"]
    cmd = item["cmd"]
    desc = item["desc"]

    # Dispatch by attributes
    if "action" in attrs:
        return handle_action(attrs["action"])
    if "workflow" in attrs:
        return handle_workflow(attrs["workflow"])

    # Fallback: help shows menu
    if cmd == "*help":
        return show_menu()
    if cmd == "*exit":
        return "Exit requested. Confirm exit? (y/n)"

    return f"No handler for '{cmd}'. Try *help."


if __name__ == "__main__":
    main()
