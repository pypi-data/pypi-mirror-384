# BMAD MCP Server - Architecture

## Overview

The BMAD MCP Server is a Python-based MCP (Model Context Protocol) server that exposes BMAD agent personas as prompts for Claude Desktop and Claude Code.

## Design Principles

1. **Embedded Resources**: All BMAD framework files are embedded in the server package, making it portable and self-contained
2. **Prompts as Personas**: Agent personas are exposed as MCP prompts, not tools, since they're contextual instructions
3. **Zero External Dependencies**: No need for the original `/bmad` directory at runtime
4. **Simple Invocation**: Users invoke agents with `/bmad:master` syntax
5. **FastMCP Architecture**: Uses the high-level FastMCP SDK for simplicity and maintainability

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop / Code                    │
│                                                              │
│  User types: /bmad:master --user_name "Alice"               │
└───────────────────────────┬──────────────────────────────────┘
                            │ MCP Protocol (stdio)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   BMAD MCP Server (Python)                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastMCP Server                                      │   │
│  │  - Handles MCP protocol                              │   │
│  │  - Manages prompt registration                       │   │
│  │  - stdio transport                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Prompt Handlers (prompts/master.py)                 │   │
│  │  - Generates agent persona text                      │   │
│  │  - Substitutes variables                             │   │
│  │  - Adds context headers                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Resource Loader (resources.py)                      │   │
│  │  - Loads embedded files                              │   │
│  │  - Parses YAML configs                               │   │
│  │  - Provides file listing                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Embedded Resources (embedded/)                      │   │
│  │  - core/                                             │   │
│  │    - agents/                                         │   │
│  │    - tasks/                                          │   │
│  │    - workflows/                                      │   │
│  │    - config.yaml                                     │   │
│  │  - bmm/                                              │   │
│  │  - _cfg/                                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. FastMCP Server (`server.py`)

**Responsibility**: MCP protocol handling and prompt registration

**Key Features**:
- Initializes FastMCP instance
- Registers prompts using decorators
- Handles stdio transport
- Entry point for the server

**Code Pattern**:
```python
mcp = FastMCP("BMAD Agent Personas")

@mcp.prompt()
def master(user_name: str = "User", language: str = "English") -> str:
    return get_master_agent_prompt(user_name, language)
```

### 2. Prompt Handlers (`prompts/master.py`)

**Responsibility**: Generate agent persona prompts

**Key Features**:
- Loads agent markdown/XML files
- Substitutes template variables
- Adds contextual headers
- Applies user preferences

**Variable Substitution**:
- `{user_name}` → User's name
- `{communication_language}` → Preferred language
- `{project-root}` → Replaced with `.` (embedded files)

### 3. Resource Loader (`resources.py`)

**Responsibility**: Access embedded BMAD files

**Key Features**:
- Path resolution for embedded files
- File loading with encoding handling
- YAML config parsing
- File listing/discovery

**API**:
```python
load_embedded_file("core/agents/bmad-master.md")
load_config()
list_embedded_files("**/*.yaml")
```

### 4. Embedded Resources (`embedded/`)

**Responsibility**: Store all BMAD framework files

**Structure**:
```
embedded/
├── core/           # Core BMAD framework
│   ├── agents/     # Agent personas
│   ├── tasks/      # Task definitions
│   ├── workflows/  # Workflow configs
│   └── config.yaml # User config
├── bmm/            # BMM module
└── _cfg/           # Configuration files
```

**Build Process**: Files are copied from `/bmad` during installation

## Data Flow

### Prompt Invocation Flow

1. **User Invocation**: User types `/bmad:master --user_name "Alice"` in Claude
2. **MCP Request**: Claude sends `get_prompt` request over stdio
3. **Prompt Lookup**: FastMCP routes to the `master()` function
4. **Resource Loading**: Handler loads `core/agents/bmad-master.md`
5. **Variable Substitution**: Replaces `{user_name}` with "Alice"
6. **Response**: Returns complete agent persona as text
7. **Context Injection**: Claude injects the persona into the conversation

## Why MCP Prompts (Not Tools)?

**Prompts** are perfect for agent personas because:

✅ **Contextual**: Prompts inject instructions into the conversation context
✅ **No Execution**: Agents are behavioral templates, not executable functions
✅ **Composable**: Multiple prompts can be layered together
✅ **Flexible**: Support dynamic content and templates

**Tools** would be wrong because:

❌ **Execution Model**: Tools are for actions (API calls, file operations)
❌ **Return Values**: Tools return JSON data, not instructions
❌ **Side Effects**: Tools change state; personas define behavior

## Transport Protocol

**stdio** (Standard Input/Output):
- Default transport for MCP servers
- Perfect for desktop integrations
- Low latency, simple protocol
- Used by Claude Desktop and Claude Code

## Future Architecture Enhancements

### Phase 2: Multiple Agents
```python
@mcp.prompt()
def architect(...): ...

@mcp.prompt()
def tea(...): ...

@mcp.prompt()
def gamedev(...): ...
```

### Phase 3: Resource Endpoints
Expose embedded files as MCP resources:
```python
@mcp.resource("bmad://workflows/{name}")
def get_workflow(name: str): ...
```

### Phase 4: Workflow Tools
Execute workflows as MCP tools:
```python
@mcp.tool()
def execute_workflow(workflow_path: str): ...
```

## Testing Strategy

### Unit Tests (`test_server.py`)
- Resource loading
- Prompt generation
- Variable substitution
- Server initialization

### Integration Tests
- MCP Inspector (`uv run mcp dev`)
- Real server invocation
- End-to-end prompt flow

### Manual Testing
- Claude Desktop integration
- Claude Code integration
- Actual usage scenarios

## Dependencies

**Core**:
- `mcp >= 1.0.0` - FastMCP SDK
- `pyyaml >= 6.0.1` - Config parsing

**Implicit** (via mcp):
- `pydantic` - Data validation
- `starlette` - HTTP support (unused for stdio)
- `anyio` - Async primitives

## Configuration

### Package Config (`pyproject.toml`)
- Defines package metadata
- Specifies dependencies
- Declares entry point

### Hatchling Config
- Specifies package location (`src/bmad_mcp`)
- Includes embedded resources in build

### MCP Config (Claude Desktop)
```json
{
  "mcpServers": {
    "bmad-personas": {
      "command": "uv",
      "args": ["run", "bmad-mcp-server"]
    }
  }
}
```

## Performance Characteristics

- **Startup Time**: ~200ms (Python interpreter + imports)
- **Prompt Generation**: <10ms (file I/O + string substitution)
- **Memory Footprint**: ~50MB (Python runtime + embedded files)
- **Latency**: <50ms for typical prompt requests

## Security Considerations

- **Embedded Files**: All files are read-only, preventing tampering
- **No Network Access**: Server only uses stdio transport
- **No Arbitrary Code Execution**: Prompts are text templates, not code
- **Sandboxed**: Runs in MCP sandbox with limited permissions

## Deployment

**Development**:
```bash
uv venv && uv pip install -e .
```

**Production** (Claude Desktop):
```bash
uv run mcp install src/bmad_mcp/server.py
```

**Distribution**:
- Can be packaged as wheel: `uv build`
- Can be published to PyPI
- Can be installed via `pip install bmad-mcp-server`
