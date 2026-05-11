# Claude Desktop / Code integration

## Claude Desktop

`%APPDATA%\Claude\claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "architect-companion": {
      "command": "architect-companion-mcp"
    }
  }
}
```

## Claude Code

`.claude/settings.json` (project) or `~/.claude/settings.json` (global):

```json
{
  "mcpServers": {
    "architect-companion": {
      "command": "architect-companion-mcp"
    }
  }
}
```

Restart the client. The tools appear under the `architect-companion`
server. Prompts become available as slash commands:
`/architect-companion__design_build`, `/architect-companion__compare_builds`,
`/architect-companion__troubleshoot_build`, etc.
