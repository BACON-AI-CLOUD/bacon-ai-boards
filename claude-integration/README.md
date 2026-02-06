# Focalboard + Claude Code Integration

> AI-powered project management using Claude Code subscription (not per-token API costs)

## Overview

This integration embeds Claude AI capabilities into Focalboard using the **Claude Code CLI subscription** ($20/month flat rate) instead of expensive per-token API costs ($3/$15 per million tokens).

### Features

| Feature | Description | Model Used |
|---------|-------------|------------|
| **Card Description Generation** | AI-generated descriptions based on title and context | Sonnet |
| **Content Suggestions** | AI suggests content blocks (tasks, text) to add to cards | Haiku |
| **Card Summarization** | Quick AI summary of card content | Haiku |
| **Title Improvement** | Suggests clearer, more actionable titles | Haiku |
| **Natural Language Search** | Convert "urgent tasks due tomorrow" to filters | Haiku |

### Cost Comparison

| Method | Monthly Cost (1M tokens/month) | Notes |
|--------|-------------------------------|-------|
| **Claude API** | ~$9 - $45+ | Per-token billing |
| **Claude Code Subscription** | $20 flat | Unlimited within fair use |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Focalboard Web UI (React)                    │
│  • AIButton components                                          │
│  • AISuggestionPanel                                            │
│  • AISearchInput                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Proxy Service                          │
│  • Express.js HTTP server                                        │
│  • Rate limiting & concurrency control                           │
│  • Request routing                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Child Process
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code CLI                               │
│  • Subscription-based authentication                             │
│  • OAuth tokens in ~/.claude.json                                │
│  • Model selection (sonnet, opus, haiku)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Anthropic Cloud                               │
│  • Subscription billing (not per-token)                          │
│  • Same models as API                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

1. **Claude Code CLI** installed and authenticated:
   ```bash
   # Install globally
   npm install -g @anthropic-ai/claude-code

   # Authenticate (opens browser)
   claude login

   # Verify
   claude --print "Hello, world!"
   ```

2. **Docker & Docker Compose** installed

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to integration directory
cd focalboard/claude-integration/docker

# Start all services
docker-compose up -d

# Access Focalboard at http://localhost:80
```

### Option 2: Manual Setup

1. **Start Focalboard:**
   ```bash
   docker run -d -p 8000:8000 mattermost/focalboard
   ```

2. **Start Claude Proxy:**
   ```bash
   cd docker/claude-proxy
   npm install
   npm start
   ```

3. **Access Focalboard** at http://localhost:8000

## Integration Details

### Directory Structure

```
claude-integration/
├── README.md                          # This file
├── server/
│   ├── services/ai/
│   │   └── claude_service.go          # Go service (if using native integration)
│   └── api/
│       └── ai.go                      # API handlers
├── webapp/
│   └── src/components/ai/
│       ├── index.ts                   # Exports
│       ├── AIButton.tsx               # AI action buttons
│       ├── AISuggestionPanel.tsx      # Suggestions panel
│       ├── AISearchInput.tsx          # Natural language search
│       └── aiClient.ts                # API client & React hooks
└── docker/
    ├── docker-compose.yml             # Full stack deployment
    └── claude-proxy/
        ├── Dockerfile
        ├── package.json
        └── server.js                  # Node.js proxy server
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cards/{id}/description` | POST | Generate description |
| `/api/cards/{id}/suggestions` | GET | Get content suggestions |
| `/api/cards/{id}/summary` | GET | Get card summary |
| `/api/cards/{id}/improve-title` | POST | Improve card title |
| `/api/boards/{id}/search` | POST | Natural language search |
| `/api/prompt` | POST | Generic prompt endpoint |
| `/health` | GET | Health check |

### React Integration Example

```tsx
import {
    AIButton,
    GenerateDescriptionButton,
    AISuggestionPanel,
    AISearchInput,
    aiClient,
    useGenerateDescription,
} from './components/ai';

// In your card detail component
function CardDetail({ card }) {
    const { generate, loading, error } = useGenerateDescription();
    const [showSuggestions, setShowSuggestions] = useState(false);

    const handleGenerateDescription = async () => {
        const description = await generate({
            cardId: card.id,
            title: card.title,
            boardTitle: card.boardTitle,
            labels: card.labels,
        });
        if (description) {
            // Update card description
            updateCard(card.id, { description });
        }
    };

    return (
        <div>
            <h2>{card.title}</h2>

            {/* AI Description Button */}
            <GenerateDescriptionButton
                onGenerate={handleGenerateDescription}
                disabled={loading}
            />

            {/* AI Suggestions Panel */}
            <button onClick={() => setShowSuggestions(true)}>
                Get AI Suggestions
            </button>

            {showSuggestions && (
                <AISuggestionPanel
                    cardId={card.id}
                    cardTitle={card.title}
                    cardDescription={card.description}
                    onApplySuggestion={(suggestion) => {
                        // Add content block to card
                        addContentBlock(card.id, suggestion);
                    }}
                    onClose={() => setShowSuggestions(false)}
                />
            )}
        </div>
    );
}

// In your board header
function BoardHeader({ boardId }) {
    return (
        <AISearchInput
            boardId={boardId}
            onFiltersGenerated={(filters) => {
                // Apply filters to card view
                applyFilters(filters);
            }}
        />
    );
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_MODEL` | `sonnet` | Default model (sonnet, opus, haiku) |
| `CLAUDE_TIMEOUT` | `120` | Request timeout in seconds |
| `MAX_CONCURRENT` | `3` | Max concurrent AI requests |
| `PORT` | `8080` | Proxy server port |

### Claude Wrapper Script

For native Go integration, create `/home/bacon/bin/claude-wrapper`:

```bash
#!/bin/bash
export HOME=/home/bacon
exec /usr/bin/claude "$@"
```

### Sudoers (for multi-user deployment)

If running Focalboard as a different user:

```bash
# /etc/sudoers.d/focalboard-claude
focalboard ALL=(bacon) NOPASSWD: /home/bacon/bin/claude-wrapper
```

## Security Considerations

1. **Authentication Tokens**: Store in `~/.claude.json` with 600 permissions
2. **Rate Limiting**: Built-in rate limiting (30 req/min)
3. **Concurrency Control**: Max 3 concurrent AI requests
4. **Input Sanitization**: Prompts are sanitized before execution
5. **HTTPS**: All Anthropic communication over HTTPS

## Troubleshooting

### "Claude CLI not found"

```bash
# Verify installation
which claude
# Should show: /usr/bin/claude or similar

# If not found, reinstall
npm install -g @anthropic-ai/claude-code
```

### "Authentication failed"

```bash
# Re-authenticate
claude login

# Verify config exists
ls -la ~/.claude.json
```

### "Rate limit exceeded"

The proxy has built-in rate limiting. Wait 60 seconds and retry.

### "Timeout errors"

1. Increase `CLAUDE_TIMEOUT` environment variable
2. Use faster model (haiku instead of opus)
3. Simplify prompts

## Model Selection Guide

| Model | Best For | Speed | Quality |
|-------|----------|-------|---------|
| **Haiku** | Quick tasks, suggestions, search parsing | Fast | Good |
| **Sonnet** | General use, description generation | Medium | Very Good |
| **Opus** | Complex analysis, detailed content | Slow | Excellent |

## Development

### Running Tests

```bash
# Start services
docker-compose up -d

# Test health endpoint
curl http://localhost:8080/health

# Test description generation
curl -X POST http://localhost:8080/api/cards/test123/description \
    -H "Content-Type: application/json" \
    -d '{"context": {"title": "Implement user auth", "boardTitle": "Backend"}}'
```

### Adding New AI Features

1. Add endpoint to `server.js` or `ai.go`
2. Create React component in `webapp/src/components/ai/`
3. Add API method to `aiClient.ts`
4. Export from `index.ts`

## Related Resources

- [Claude Code CLI Documentation](https://docs.anthropic.com/claude-code)
- [Focalboard Documentation](https://www.focalboard.com/docs/)
- [Claude Code Wrapper Skill](/home/bacon/.claude/skills/claude-code-wrapper/SKILL.md)

## License

MIT License - See LICENSE file for details

---

**Integration by:** BACON-AI Framework
**Last Updated:** January 2026
