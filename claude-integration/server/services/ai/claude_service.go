// Package ai provides Claude Code CLI integration for Focalboard
// This service wraps the Claude Code CLI to provide AI-powered features
// using subscription-based licensing instead of per-token API costs.
package ai

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
	"sync"
	"time"
)

// ClaudeService wraps the Claude Code CLI for AI operations
type ClaudeService struct {
	wrapperPath    string        // Path to claude-wrapper script
	homeDir        string        // Home directory with Claude auth
	defaultModel   string        // Default model to use (sonnet, opus, haiku)
	timeout        time.Duration // Request timeout
	mu             sync.Mutex    // Mutex for serializing requests
	maxConcurrent  int           // Max concurrent requests
	semaphore      chan struct{} // Semaphore for rate limiting
}

// ClaudeServiceConfig holds configuration for the Claude service
type ClaudeServiceConfig struct {
	WrapperPath   string        `json:"wrapper_path"`
	HomeDir       string        `json:"home_dir"`
	DefaultModel  string        `json:"default_model"`
	Timeout       time.Duration `json:"timeout"`
	MaxConcurrent int           `json:"max_concurrent"`
}

// AIRequest represents a request to the Claude AI
type AIRequest struct {
	Prompt       string `json:"prompt"`
	SystemPrompt string `json:"system_prompt,omitempty"`
	Model        string `json:"model,omitempty"`
	MaxTokens    int    `json:"max_tokens,omitempty"`
}

// AIResponse represents a response from Claude AI
type AIResponse struct {
	Content   string `json:"content"`
	Model     string `json:"model"`
	Timestamp int64  `json:"timestamp"`
	TokensIn  int    `json:"tokens_in,omitempty"`
	TokensOut int    `json:"tokens_out,omitempty"`
}

// CardContext provides context for AI operations on cards
type CardContext struct {
	CardID      string            `json:"card_id"`
	Title       string            `json:"title"`
	Description string            `json:"description,omitempty"`
	Properties  map[string]any    `json:"properties,omitempty"`
	BoardTitle  string            `json:"board_title,omitempty"`
	Labels      []string          `json:"labels,omitempty"`
}

// ContentSuggestion represents an AI-suggested content block
type ContentSuggestion struct {
	Type        string `json:"type"`        // text, checkbox, etc.
	Content     string `json:"content"`
	Confidence  float64 `json:"confidence"`
	Explanation string `json:"explanation,omitempty"`
}

// NewClaudeService creates a new Claude service instance
func NewClaudeService(config ClaudeServiceConfig) (*ClaudeService, error) {
	if config.WrapperPath == "" {
		config.WrapperPath = "/home/bacon/bin/claude-wrapper"
	}
	if config.HomeDir == "" {
		config.HomeDir = "/home/bacon"
	}
	if config.DefaultModel == "" {
		config.DefaultModel = "sonnet"
	}
	if config.Timeout == 0 {
		config.Timeout = 120 * time.Second
	}
	if config.MaxConcurrent == 0 {
		config.MaxConcurrent = 3
	}

	service := &ClaudeService{
		wrapperPath:   config.WrapperPath,
		homeDir:       config.HomeDir,
		defaultModel:  config.DefaultModel,
		timeout:       config.Timeout,
		maxConcurrent: config.MaxConcurrent,
		semaphore:     make(chan struct{}, config.MaxConcurrent),
	}

	// Verify Claude CLI is accessible
	if err := service.verifySetup(); err != nil {
		return nil, fmt.Errorf("claude service setup verification failed: %w", err)
	}

	return service, nil
}

// verifySetup checks that the Claude CLI is properly configured
func (s *ClaudeService) verifySetup() error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, s.wrapperPath, "--version")
	cmd.Env = append(cmd.Env, fmt.Sprintf("HOME=%s", s.homeDir))

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("claude-wrapper not accessible: %w", err)
	}
	return nil
}

// Execute runs a prompt through Claude and returns the response
func (s *ClaudeService) Execute(ctx context.Context, req AIRequest) (*AIResponse, error) {
	// Acquire semaphore slot
	select {
	case s.semaphore <- struct{}{}:
		defer func() { <-s.semaphore }()
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	model := req.Model
	if model == "" {
		model = s.defaultModel
	}

	args := []string{
		"--print",
		"--model", model,
		"--output-format", "text",
	}

	if req.SystemPrompt != "" {
		args = append(args, "--system-prompt", req.SystemPrompt)
	}

	if req.MaxTokens > 0 {
		args = append(args, "--max-tokens", fmt.Sprintf("%d", req.MaxTokens))
	}

	args = append(args, req.Prompt)

	// Create timeout context
	execCtx, cancel := context.WithTimeout(ctx, s.timeout)
	defer cancel()

	cmd := exec.CommandContext(execCtx, s.wrapperPath, args...)
	cmd.Env = append(cmd.Env, fmt.Sprintf("HOME=%s", s.homeDir))

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("claude execution failed: %w, stderr: %s", err, stderr.String())
	}

	return &AIResponse{
		Content:   strings.TrimSpace(stdout.String()),
		Model:     model,
		Timestamp: time.Now().Unix(),
	}, nil
}

// GenerateCardDescription generates a description for a card based on context
func (s *ClaudeService) GenerateCardDescription(ctx context.Context, card CardContext) (string, error) {
	systemPrompt := `You are an assistant helping users write clear, actionable card descriptions for a project management tool similar to Trello or Notion.

Guidelines:
- Be concise but comprehensive
- Use bullet points for lists
- Include acceptance criteria when relevant
- Focus on what needs to be done
- Keep descriptions under 200 words`

	prompt := fmt.Sprintf(`Generate a description for a card with the following context:

Title: %s
Board: %s
Labels: %s
Current description: %s

Please write a clear, actionable description that helps team members understand what needs to be done.`,
		card.Title,
		card.BoardTitle,
		strings.Join(card.Labels, ", "),
		card.Description,
	)

	resp, err := s.Execute(ctx, AIRequest{
		Prompt:       prompt,
		SystemPrompt: systemPrompt,
		Model:        "sonnet",
	})
	if err != nil {
		return "", err
	}

	return resp.Content, nil
}

// SuggestContentBlocks suggests content blocks to add to a card
func (s *ClaudeService) SuggestContentBlocks(ctx context.Context, card CardContext) ([]ContentSuggestion, error) {
	systemPrompt := `You are helping suggest content blocks for a project management card.
Output a JSON array of suggestions with type (text, checkbox, divider) and content.
Only output valid JSON, no markdown formatting.`

	prompt := fmt.Sprintf(`Based on this card, suggest 3-5 content blocks to add:

Title: %s
Description: %s

Output format (JSON array):
[{"type": "checkbox", "content": "Task item", "confidence": 0.9}, ...]`,
		card.Title,
		card.Description,
	)

	resp, err := s.Execute(ctx, AIRequest{
		Prompt:       prompt,
		SystemPrompt: systemPrompt,
		Model:        "haiku", // Use faster model for suggestions
	})
	if err != nil {
		return nil, err
	}

	var suggestions []ContentSuggestion
	if err := json.Unmarshal([]byte(resp.Content), &suggestions); err != nil {
		// If JSON parsing fails, return a single text suggestion
		return []ContentSuggestion{{
			Type:       "text",
			Content:    resp.Content,
			Confidence: 0.5,
		}}, nil
	}

	return suggestions, nil
}

// SummarizeCard generates a brief summary of a card's content
func (s *ClaudeService) SummarizeCard(ctx context.Context, card CardContext, comments []string) (string, error) {
	systemPrompt := `You are summarizing project cards. Be extremely concise - max 2 sentences.`

	commentsText := ""
	if len(comments) > 0 {
		commentsText = fmt.Sprintf("\n\nComments:\n%s", strings.Join(comments, "\n"))
	}

	prompt := fmt.Sprintf(`Summarize this card in 1-2 sentences:

Title: %s
Description: %s%s`,
		card.Title,
		card.Description,
		commentsText,
	)

	resp, err := s.Execute(ctx, AIRequest{
		Prompt:       prompt,
		SystemPrompt: systemPrompt,
		Model:        "haiku",
		MaxTokens:    100,
	})
	if err != nil {
		return "", err
	}

	return resp.Content, nil
}

// ParseNaturalLanguageQuery converts natural language to filter parameters
func (s *ClaudeService) ParseNaturalLanguageQuery(ctx context.Context, query string, availableProperties []string) (map[string]interface{}, error) {
	systemPrompt := `You convert natural language queries into JSON filter objects for a project management tool.
Output only valid JSON with filter criteria. Available filter keys: assignee, priority, status, dueDate, labels.
Use operators: equals, contains, gt (greater than), lt (less than), between.
Output only valid JSON, no markdown.`

	prompt := fmt.Sprintf(`Convert this search query to filters:

Query: "%s"
Available properties: %s

Output format:
{"filters": [{"property": "status", "operator": "equals", "value": "in progress"}]}`,
		query,
		strings.Join(availableProperties, ", "),
	)

	resp, err := s.Execute(ctx, AIRequest{
		Prompt:       prompt,
		SystemPrompt: systemPrompt,
		Model:        "haiku",
	})
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	if err := json.Unmarshal([]byte(resp.Content), &result); err != nil {
		return nil, fmt.Errorf("failed to parse filter response: %w", err)
	}

	return result, nil
}

// ImproveTitle suggests an improved title for a card
func (s *ClaudeService) ImproveTitle(ctx context.Context, currentTitle string, description string) (string, error) {
	systemPrompt := `You suggest improved titles for project cards. Output only the improved title, nothing else.
Titles should be: concise (under 60 chars), action-oriented, clear about what needs to be done.`

	prompt := fmt.Sprintf(`Suggest an improved title for this card:

Current title: %s
Description: %s

Output only the improved title:`,
		currentTitle,
		description,
	)

	resp, err := s.Execute(ctx, AIRequest{
		Prompt:       prompt,
		SystemPrompt: systemPrompt,
		Model:        "haiku",
		MaxTokens:    50,
	})
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(resp.Content), nil
}

// Health checks if the Claude service is healthy
func (s *ClaudeService) Health(ctx context.Context) error {
	_, err := s.Execute(ctx, AIRequest{
		Prompt:    "Say OK",
		Model:     "haiku",
		MaxTokens: 5,
	})
	return err
}
