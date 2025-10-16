

CMD_NAUTEX_SETUP = 'uvx nautex setup'

NAUTEX_SECTION_START = '<!-- NAUTEX_SECTION_START -->'
NAUTEX_SECTION_END = '<!-- NAUTEX_SECTION_END -->'

NAUTEX_RULES_REFERENCE_CONTENT = """# Nautex MCP Integration

This project uses Nautex Model-Context-Protocol (MCP). Nautex manages requirements and task-driven LLM assisted development.
 
Whenever user requests to operate with nautex, the following applies: 

- read full Nautex workflow guidelines from `.nautex/CLAUDE.md`
- note that all paths managed by nautex are relative to the project root
- note primary workflow commands: `next_scope`, `tasks_update` 
- NEVER edit files in `.nautex` directory

"""

def rules_reference_content_for(rules_filename: str) -> str:
    """Reference section content parameterized by rules file name.

    Args:
        rules_filename: The filename stored under .nautex/ with full rules

    Returns:
        String content for the managed reference section
    """
    return f"""# Nautex MCP Integration

This project uses Nautex Model-Context-Protocol (MCP). Nautex manages requirements and task-driven LLM assisted development.
 
Whenever user requests to operate with nautex, the following applies: 

- read full Nautex workflow guidelines from `.nautex/{rules_filename}`
- note that all paths managed by nautex are relative to the project root
- note primary workflow commands: `next_scope`, `tasks_update` 
- NEVER edit files in `.nautex` directory

"""

DEFAULT_RULES_TEMPLATE = """# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

"""

def default_agents_rules_template_for(rules_filename: str, tool_name: str) -> str:
    """Default root rules template for generic coding agents (AGENTS.md).

    Args:
        rules_filename: The root-facing filename such as 'AGENTS.md'.
        tool_name: Human-friendly tool name, e.g. 'OpenCode', 'Codex'.

    Returns:
        A short Markdown template used when creating the root rules file.
    """
    return f"""# {rules_filename}

This file provides guidance to {tool_name} or similar coding agents when working with code in this repository.

"""
