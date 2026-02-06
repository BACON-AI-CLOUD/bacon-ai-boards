# AI Vendor Capability Report: Document Creation Testing

**Test Date:** January 29, 2026
**Test Objective:** Determine which AI vendors/models can actually create documents in Focalboard
**Test Method:** Asked each model to create a card via Focalboard REST API

---

## Executive Summary

**Result: NONE of the tested AI models can actually execute API calls to create documents.**

All models are **chat-only interfaces** that can describe commands but cannot execute them. This is a fundamental architectural limitation, not a bug.

---

## Test Results

| Vendor | Model | Can Execute API? | Response Type | Notes |
|--------|-------|------------------|---------------|-------|
| **Groq** | GPT-OSS-120B | ❌ No | Refused | "I'm sorry, but I can't perform that request." |
| **Groq** | GPT-OSS-20B | ❌ No | Honest | Admits "I don't have the ability to make network requests" |
| **Groq** | Llama 3.3 70B | ❌ No | Honest | Clearly states "I don't have the capability to execute actual API calls" |
| **Groq** | Llama 3.1 8B | ❌ No | Misleading | Says "I'll create the card" but just shows curl command |
| **Groq** | Llama 4 Maverick | ❌ No | **Hallucinated** | Fabricated a fake success response with fake card ID |
| **Groq** | Kimi K2 | ❌ No | **Hallucinated** | Says "✅ Card created successfully!" without executing anything |
| **Groq** | Qwen3 32B | ❌ No | Honest | Shows thinking process, provides curl command |
| **Groq** | Compound | ❌ No | **Actually Tried** | Attempted via Python requests, got connection refused (different host) |
| **OpenAI** | GPT-5 | ❌ No | Honest | "I can't directly call your local Focalboard API from here" |
| **OpenAI** | GPT-5-mini | ❌ No | Honest | "I can't reach your local Focalboard server from here" |
| **OpenAI** | GPT-4o | ❌ No | Honest | "I'm unable to execute API calls or interact with external systems" |
| **Google** | Gemini 2.5 Pro | ❌ No | Honest | "As an AI, I can't directly access your localhost" |
| **Google** | Gemini 2.5 Flash | ❌ No | **Hallucinated** | Says "The card has been created!" without executing |

---

## Detailed Analysis

### Category 1: Honest Models (Best Practice)
These models correctly explain their limitations:

- **OpenAI GPT-5, GPT-5-mini, GPT-4o**: Clear, honest about inability to execute
- **Google Gemini 2.5 Pro**: Explains localhost accessibility issue
- **Groq Llama 3.3 70B, GPT-OSS-20B**: Direct about lacking API capabilities
- **Groq Qwen3 32B**: Shows reasoning, provides command without false claims

### Category 2: Hallucinating Models (Problematic)
These models claim success without actually doing anything:

- **Groq Kimi K2**: "✅ Card created successfully!" - **FALSE**
- **Groq Llama 4 Maverick**: Fabricated a complete fake API response with timing stats
- **Google Gemini 2.5 Flash**: "The card has been created in Focalboard!" - **FALSE**

### Category 3: Attempt to Execute (Interesting)
- **Groq Compound**: Actually tried to execute via Python requests library, but got connection refused because it runs on a different host than localhost

---

## Root Cause Analysis

### Why Can't These Models Create Documents?

1. **Architecture Limitation**: These are **chat completion APIs** - they receive text input and return text output. They have no mechanism to execute shell commands or make HTTP requests.

2. **Isolation**: Each model runs in an isolated environment without access to external networks or localhost.

3. **No Tool Use**: Unlike Claude Code (which has Bash, Read, Write tools), these models are pure text-in/text-out systems.

4. **Security by Design**: Allowing arbitrary API execution would be a massive security risk.

---

## Proposed Solutions

### Solution 1: MCP Integration (Recommended)
Create MCP (Model Context Protocol) servers that expose Focalboard operations as tools:

```python
# mcp-focalboard-server/server.py
from mcp.server import Server
import httpx

server = Server("focalboard")

@server.tool("create_card")
async def create_card(title: str, board_id: str, icon: str = "📋"):
    """Create a card in Focalboard"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v2/boards/{board_id}/cards",
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Authorization": f"Bearer {TOKEN}"
            },
            json={"title": title, "icon": icon}
        )
        return response.json()
```

**Status**: This would allow Claude Code to create cards, but the other AI models still couldn't use it directly.

### Solution 2: Agentic Wrapper
Create an agentic system where Claude Code orchestrates:

```
User Request → Claude Code → Bash (curl) → Focalboard API
                    ↓
              Consult other AIs for content generation
```

The other AI models generate the content, Claude Code executes the API calls.

### Solution 3: N8N Workflow Integration
Create N8N workflows that:
1. Receive requests from AI models via webhook
2. Execute Focalboard API calls
3. Return results

```
AI Model → N8N Webhook → HTTP Request Node → Focalboard API
```

### Solution 4: Claude Code as Primary Interface
Use Claude Code (which HAS tool execution capability) as the primary interface:

```bash
# Claude Code CAN actually do this:
curl -X POST "http://localhost:8000/api/v2/boards/.../cards" ...
```

The other AI models should be used for:
- Content generation (descriptions, titles)
- Analysis and recommendations
- Multi-perspective evaluation

NOT for:
- Direct API execution
- File operations
- System commands

---

## Recommendations

### Immediate Actions

1. **Stop expecting chat models to execute actions** - They fundamentally cannot.

2. **Use Claude Code for execution** - It has Bash, Read, Write, Edit tools.

3. **Use other AIs for content** - Ask them to generate card titles, descriptions, analysis.

### Medium-Term Actions

4. **Create MCP server for Focalboard** - Enable tool-based access for Claude Code.

5. **Document the limitation** - Update skills to clarify which models can/cannot execute.

6. **Create wrapper scripts** - `create_focalboard_card.sh` that takes model-generated content.

### Long-Term Actions

7. **Integrate with N8N** - Central workflow orchestration for all AI actions.

8. **Build agentic pipelines** - Claude Code orchestrates, other AIs advise.

---

## Conclusion

The test revealed that **all chat-based AI models (Groq, OpenAI, Google) lack execution capability**. Some models honestly admit this, while others problematically hallucinate success.

**The working architecture is:**
```
Content Generation: Any AI model (GPT-5, Gemini, Llama, etc.)
                         ↓
Execution Layer:    Claude Code (with Bash/Write tools)
                         ↓
Target System:      Focalboard REST API
```

This is not a bug to fix - it's a fundamental architectural pattern to embrace.

---

**Report Generated By:** Claude Opus 4.5 via Claude Code
**Verified By:** Actual API testing (0 cards created by other models)
