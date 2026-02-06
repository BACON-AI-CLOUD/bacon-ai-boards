# MCP Focalboard Server

A Model Context Protocol (MCP) server for Focalboard project management. Enables AI assistants to manage boards, cards, and tasks through well-designed tools.

## Features

- **10 Tools** for complete Focalboard management
- **FastMCP Framework** with Pydantic input validation
- **Dual Response Formats**: Markdown (human-readable) or JSON (machine-readable)
- **Pagination Support** for large boards
- **Actionable Error Messages** to guide correct usage
- **Tool Annotations** (readOnlyHint, destructiveHint, etc.)

## Quick Start

### 1. Install Dependencies

```bash
cd mcp-focalboard-server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Get Focalboard Auth Token

```bash
curl -s -X POST "http://localhost:8000/api/v2/login" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"type":"normal","username":"your-user","password":"your-pass"}' | jq -r '.token'
```

### 3. Configure Claude Code

Add to your `~/.claude.json` at **root level** (not under `projects`):

```json
{
  "mcpServers": {
    "focalboard": {
      "command": "python",
      "args": ["/home/bacon/bacon-ai/projects/focalboard/mcp-focalboard-server/server.py"],
      "env": {
        "FOCALBOARD_URL": "http://localhost:8000",
        "FOCALBOARD_TOKEN": "your-token-here"
      }
    }
  }
}
```

### 4. Restart Claude Code

Run `/mcp` to verify the server appears in the list.

## Available Tools

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `focalboard_list_boards` | List all boards for a team | ✅ |
| `focalboard_get_board` | Get board details with property definitions | ✅ |
| `focalboard_list_cards` | List cards with pagination | ✅ |
| `focalboard_get_card` | Get single card details | ✅ |
| `focalboard_search_cards` | Search cards by title | ✅ |
| `focalboard_get_board_statistics` | Get card counts by status/priority | ✅ |
| `focalboard_create_card` | Create a new card | ❌ |
| `focalboard_update_card` | Update card title/icon/properties | ❌ |
| `focalboard_delete_card` | Delete a card (destructive) | ❌ |
| `focalboard_bulk_create_cards` | Create multiple cards at once | ❌ |

## Usage Examples

### List Boards
```
Use focalboard_list_boards with team_id="0" for personal boards
```

### Create a Task Card
```
1. First, get board property IDs:
   focalboard_get_board(board_id="your-board-id")

2. Then create card with properties:
   focalboard_create_card(
     board_id="your-board-id",
     title="P01-T01 ── Create empathy map",
     icon="💭",
     properties={
       "status-prop-id": "not-started-option-id",
       "priority-prop-id": "high-option-id"
     }
   )
```

### Search for Tasks
```
focalboard_search_cards(board_id="...", query="P01")  # Find Phase 1 tasks
```

### Get Project Statistics
```
focalboard_get_board_statistics(board_id="...")  # Shows cards by status/priority
```

## Property Value Formats

When setting card properties, use these formats:

| Type | Format | Example |
|------|--------|---------|
| Select | Option ID string | `"ayz81h9f3dwp..."` |
| MultiSelect | Array of option IDs | `["id1", "id2"]` |
| Text | String | `"Some text"` |
| Number | String | `"8"` |
| Date | Object with timestamp | `{"from": 1738540800000}` |
| Person | User ID | `"user-id-here"` |

## Response Formats

All read tools support `response_format` parameter:

- **markdown** (default): Human-readable formatted output
- **json**: Machine-readable structured data with pagination metadata

## API Notes

- Focalboard API v2 requires `X-Requested-With: XMLHttpRequest` header (CSRF protection)
- All dates use Unix timestamps in **milliseconds**
- Number properties are stored as **strings** (e.g., `"8"` not `8`)
- Use `disable_notify=true` for bulk operations to avoid notification spam

## Troubleshooting

### "Authentication failed"
- Check that `FOCALBOARD_TOKEN` is valid and not expired
- Get a new token using the login endpoint

### "Resource not found"
- Verify the board_id or card_id is correct
- Use `focalboard_list_boards` to find valid board IDs

### "CSRF token failed"
- This server handles CSRF automatically via `X-Requested-With` header
- If you see this, the server may need updating

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
python -m py_compile server.py
```

## License

MIT
