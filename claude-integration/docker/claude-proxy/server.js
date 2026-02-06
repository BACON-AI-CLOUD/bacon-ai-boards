/**
 * Claude Code CLI HTTP Proxy Server
 *
 * This server wraps the Claude Code CLI to provide HTTP API access
 * using subscription-based licensing instead of per-token API costs.
 *
 * Architecture:
 * HTTP Request → Express Server → Child Process (claude CLI) → Response
 *
 * Environment Variables:
 * - CLAUDE_MODEL: Default model (sonnet, opus, haiku) [default: sonnet]
 * - CLAUDE_TIMEOUT: Request timeout in seconds [default: 120]
 * - MAX_CONCURRENT: Max concurrent requests [default: 3]
 * - PORT: Server port [default: 8080]
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { spawn } = require('child_process');

const app = express();

// Configuration
const CONFIG = {
    port: parseInt(process.env.PORT || '8080'),
    defaultModel: process.env.CLAUDE_MODEL || 'sonnet',
    timeout: parseInt(process.env.CLAUDE_TIMEOUT || '120') * 1000,
    maxConcurrent: parseInt(process.env.MAX_CONCURRENT || '3'),
};

// Semaphore for rate limiting concurrent requests
let activeRequests = 0;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '1mb' }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 30, // 30 requests per minute
    message: { error: 'Rate limit exceeded. Please try again later.' },
});
app.use('/api/', limiter);

/**
 * Execute Claude CLI command
 * @param {Object} options - Execution options
 * @param {string} options.prompt - The prompt to send
 * @param {string} options.systemPrompt - Optional system prompt
 * @param {string} options.model - Model to use
 * @param {number} options.maxTokens - Max tokens in response
 * @returns {Promise<string>} - Claude's response
 */
async function executeClaudeCommand(options) {
    const { prompt, systemPrompt, model = CONFIG.defaultModel, maxTokens } = options;

    // Check concurrent request limit
    if (activeRequests >= CONFIG.maxConcurrent) {
        throw new Error('Server is busy. Please try again later.');
    }

    activeRequests++;

    try {
        const args = ['--print', '--model', model];

        if (systemPrompt) {
            args.push('--system-prompt', systemPrompt);
        }

        // Note: Claude CLI doesn't support --max-tokens, handled by model limits
        args.push(prompt);

        return await new Promise((resolve, reject) => {
            const proc = spawn('claude', args, {
                timeout: CONFIG.timeout,
                env: { ...process.env, HOME: process.env.HOME },
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', (code) => {
                if (code === 0) {
                    resolve(stdout.trim());
                } else {
                    reject(new Error(stderr || `Claude CLI exited with code ${code}`));
                }
            });

            proc.on('error', (err) => {
                reject(new Error(`Failed to start Claude CLI: ${err.message}`));
            });

            // Handle timeout
            setTimeout(() => {
                proc.kill();
                reject(new Error('Request timed out'));
            }, CONFIG.timeout);
        });
    } finally {
        activeRequests--;
    }
}

// API Routes

/**
 * Health check endpoint
 */
app.get('/health', async (req, res) => {
    try {
        // Quick health check - just verify CLI is accessible
        await executeClaudeCommand({
            prompt: 'Say OK',
            model: 'haiku',
            maxTokens: 5,
        });
        res.json({ status: 'healthy', service: 'claude-proxy' });
    } catch (error) {
        res.status(503).json({ status: 'unhealthy', error: error.message });
    }
});

/**
 * Generate card description
 * POST /api/cards/:cardId/description
 */
app.post('/api/cards/:cardId/description', async (req, res) => {
    try {
        const { context } = req.body;

        if (!context || !context.title) {
            return res.status(400).json({ error: 'Card context with title is required' });
        }

        const systemPrompt = `You are an assistant helping users write clear, actionable card descriptions for a project management tool similar to Trello or Notion.

Guidelines:
- Be concise but comprehensive
- Use bullet points for lists
- Include acceptance criteria when relevant
- Focus on what needs to be done
- Keep descriptions under 200 words`;

        const prompt = `Generate a description for a card with the following context:

Title: ${context.title}
Board: ${context.boardTitle || 'Unknown'}
Labels: ${(context.labels || []).join(', ') || 'None'}
Current description: ${context.description || 'None'}

Please write a clear, actionable description that helps team members understand what needs to be done.`;

        const description = await executeClaudeCommand({
            prompt,
            systemPrompt,
            model: 'sonnet',
        });

        res.json({ description, model: 'sonnet' });
    } catch (error) {
        console.error('Error generating description:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Get content suggestions
 * GET /api/cards/:cardId/suggestions
 */
app.get('/api/cards/:cardId/suggestions', async (req, res) => {
    try {
        const { title, description } = req.query;

        if (!title) {
            return res.status(400).json({ error: 'Card title is required' });
        }

        const systemPrompt = `You are helping suggest content blocks for a project management card.
Output a JSON array of suggestions with type (text, checkbox, divider) and content.
Only output valid JSON, no markdown formatting.`;

        const prompt = `Based on this card, suggest 3-5 content blocks to add:

Title: ${title}
Description: ${description || 'None'}

Output format (JSON array):
[{"type": "checkbox", "content": "Task item", "confidence": 0.9}, ...]`;

        const response = await executeClaudeCommand({
            prompt,
            systemPrompt,
            model: 'haiku',
        });

        let suggestions;
        try {
            suggestions = JSON.parse(response);
        } catch {
            suggestions = [{ type: 'text', content: response, confidence: 0.5 }];
        }

        res.json({ suggestions });
    } catch (error) {
        console.error('Error getting suggestions:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Get card summary
 * GET /api/cards/:cardId/summary
 */
app.get('/api/cards/:cardId/summary', async (req, res) => {
    try {
        const { title, description } = req.query;

        if (!title) {
            return res.status(400).json({ error: 'Card title is required' });
        }

        const systemPrompt = `You are summarizing project cards. Be extremely concise - max 2 sentences.`;

        const prompt = `Summarize this card in 1-2 sentences:

Title: ${title}
Description: ${description || 'None'}`;

        const summary = await executeClaudeCommand({
            prompt,
            systemPrompt,
            model: 'haiku',
            maxTokens: 100,
        });

        res.json({ summary });
    } catch (error) {
        console.error('Error getting summary:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Improve card title
 * POST /api/cards/:cardId/improve-title
 */
app.post('/api/cards/:cardId/improve-title', async (req, res) => {
    try {
        const { title, description } = req.body;

        if (!title) {
            return res.status(400).json({ error: 'Title is required' });
        }

        const systemPrompt = `You suggest improved titles for project cards. Output only the improved title, nothing else.
Titles should be: concise (under 60 chars), action-oriented, clear about what needs to be done.`;

        const prompt = `Suggest an improved title for this card:

Current title: ${title}
Description: ${description || 'None'}

Output only the improved title:`;

        const improvedTitle = await executeClaudeCommand({
            prompt,
            systemPrompt,
            model: 'haiku',
            maxTokens: 50,
        });

        res.json({ improved_title: improvedTitle.trim(), original: title });
    } catch (error) {
        console.error('Error improving title:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Parse natural language search query
 * POST /api/boards/:boardId/search
 */
app.post('/api/boards/:boardId/search', async (req, res) => {
    try {
        const { query, available_properties } = req.body;

        if (!query) {
            return res.status(400).json({ error: 'Query is required' });
        }

        const properties = available_properties || [
            'assignee',
            'priority',
            'status',
            'dueDate',
            'labels',
        ];

        const systemPrompt = `You convert natural language queries into JSON filter objects for a project management tool.
Output only valid JSON with filter criteria. Available filter keys: ${properties.join(', ')}.
Use operators: equals, contains, gt (greater than), lt (less than), between.
Output only valid JSON, no markdown.`;

        const prompt = `Convert this search query to filters:

Query: "${query}"

Output format:
{"filters": [{"property": "status", "operator": "equals", "value": "in progress"}]}`;

        const response = await executeClaudeCommand({
            prompt,
            systemPrompt,
            model: 'haiku',
        });

        let filters;
        try {
            filters = JSON.parse(response);
        } catch {
            filters = { filters: [] };
        }

        res.json({ query, filters });
    } catch (error) {
        console.error('Error parsing search query:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Generic prompt endpoint for custom AI operations
 * POST /api/prompt
 */
app.post('/api/prompt', async (req, res) => {
    try {
        const { prompt, systemPrompt, model, maxTokens } = req.body;

        if (!prompt) {
            return res.status(400).json({ error: 'Prompt is required' });
        }

        const response = await executeClaudeCommand({
            prompt,
            systemPrompt,
            model: model || CONFIG.defaultModel,
            maxTokens,
        });

        res.json({
            content: response,
            model: model || CONFIG.defaultModel,
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('Error executing prompt:', error);
        res.status(500).json({ error: error.message });
    }
});

// Error handler
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(CONFIG.port, () => {
    console.log(`Claude Proxy Server running on port ${CONFIG.port}`);
    console.log(`Configuration:
  - Default Model: ${CONFIG.defaultModel}
  - Timeout: ${CONFIG.timeout / 1000}s
  - Max Concurrent: ${CONFIG.maxConcurrent}
`);
});
