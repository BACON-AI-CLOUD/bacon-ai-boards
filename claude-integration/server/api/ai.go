// Package api provides AI-powered REST endpoints for Focalboard
package api

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/mattermost/focalboard/server/model"
	"github.com/mattermost/focalboard/server/services/ai"
)

// AIHandler handles AI-related API requests
type AIHandler struct {
	claude *ai.ClaudeService
}

// NewAIHandler creates a new AI handler
func NewAIHandler(claude *ai.ClaudeService) *AIHandler {
	return &AIHandler{claude: claude}
}

// RegisterAIRoutes registers AI-related routes
func (h *AIHandler) RegisterAIRoutes(r *mux.Router, sessionRequired func(http.HandlerFunc) http.HandlerFunc) {
	// AI routes under /api/v2/ai
	aiRouter := r.PathPrefix("/ai").Subrouter()

	// Card AI endpoints
	aiRouter.HandleFunc("/cards/{cardID}/description", sessionRequired(h.handleGenerateDescription)).Methods("POST")
	aiRouter.HandleFunc("/cards/{cardID}/suggestions", sessionRequired(h.handleGetSuggestions)).Methods("GET")
	aiRouter.HandleFunc("/cards/{cardID}/summary", sessionRequired(h.handleGetSummary)).Methods("GET")
	aiRouter.HandleFunc("/cards/{cardID}/improve-title", sessionRequired(h.handleImproveTitle)).Methods("POST")

	// Board AI endpoints
	aiRouter.HandleFunc("/boards/{boardID}/search", sessionRequired(h.handleNaturalLanguageSearch)).Methods("POST")

	// Health check
	aiRouter.HandleFunc("/health", h.handleHealth).Methods("GET")
}

// GenerateDescriptionRequest represents a request to generate a card description
type GenerateDescriptionRequest struct {
	Context ai.CardContext `json:"context"`
}

// GenerateDescriptionResponse represents the response with generated description
type GenerateDescriptionResponse struct {
	Description string `json:"description"`
	Model       string `json:"model"`
}

// handleGenerateDescription generates a description for a card
func (h *AIHandler) handleGenerateDescription(w http.ResponseWriter, r *http.Request) {
	// swagger:operation POST /ai/cards/{cardID}/description generateCardDescription
	//
	// Generates an AI-powered description for a card
	//
	// ---
	// produces:
	// - application/json
	// parameters:
	// - name: cardID
	//   in: path
	//   description: Card ID
	//   required: true
	//   type: string
	// - name: Body
	//   in: body
	//   description: Card context for description generation
	//   required: true
	//   schema:
	//     "$ref": "#/definitions/GenerateDescriptionRequest"
	// security:
	// - BearerAuth: []
	// responses:
	//   '200':
	//     description: success
	//     schema:
	//       "$ref": "#/definitions/GenerateDescriptionResponse"
	//   default:
	//     description: internal error
	//     schema:
	//       "$ref": "#/definitions/ErrorResponse"

	cardID := mux.Vars(r)["cardID"]

	body, err := io.ReadAll(r.Body)
	if err != nil {
		errorResponse(w, model.NewErrBadRequest(err.Error()))
		return
	}

	var req GenerateDescriptionRequest
	if err := json.Unmarshal(body, &req); err != nil {
		errorResponse(w, model.NewErrBadRequest(err.Error()))
		return
	}

	// Ensure card ID matches
	req.Context.CardID = cardID

	description, err := h.claude.GenerateCardDescription(r.Context(), req.Context)
	if err != nil {
		errorResponse(w, err)
		return
	}

	resp := GenerateDescriptionResponse{
		Description: description,
		Model:       "sonnet",
	}

	jsonResponse(w, http.StatusOK, resp)
}

// SuggestionsResponse contains content block suggestions
type SuggestionsResponse struct {
	Suggestions []ai.ContentSuggestion `json:"suggestions"`
}

// handleGetSuggestions returns AI suggestions for card content
func (h *AIHandler) handleGetSuggestions(w http.ResponseWriter, r *http.Request) {
	// swagger:operation GET /ai/cards/{cardID}/suggestions getCardSuggestions
	//
	// Gets AI-powered content suggestions for a card
	//
	// ---
	// produces:
	// - application/json
	// parameters:
	// - name: cardID
	//   in: path
	//   description: Card ID
	//   required: true
	//   type: string
	// - name: title
	//   in: query
	//   description: Card title
	//   required: true
	//   type: string
	// - name: description
	//   in: query
	//   description: Card description
	//   required: false
	//   type: string
	// security:
	// - BearerAuth: []
	// responses:
	//   '200':
	//     description: success
	//     schema:
	//       "$ref": "#/definitions/SuggestionsResponse"
	//   default:
	//     description: internal error
	//     schema:
	//       "$ref": "#/definitions/ErrorResponse"

	cardID := mux.Vars(r)["cardID"]
	query := r.URL.Query()

	context := ai.CardContext{
		CardID:      cardID,
		Title:       query.Get("title"),
		Description: query.Get("description"),
	}

	suggestions, err := h.claude.SuggestContentBlocks(r.Context(), context)
	if err != nil {
		errorResponse(w, err)
		return
	}

	jsonResponse(w, http.StatusOK, SuggestionsResponse{Suggestions: suggestions})
}

// SummaryResponse contains a card summary
type SummaryResponse struct {
	Summary string `json:"summary"`
}

// handleGetSummary returns an AI-generated summary of a card
func (h *AIHandler) handleGetSummary(w http.ResponseWriter, r *http.Request) {
	// swagger:operation GET /ai/cards/{cardID}/summary getCardSummary
	//
	// Gets an AI-generated summary of a card
	//
	// ---
	// produces:
	// - application/json
	// parameters:
	// - name: cardID
	//   in: path
	//   description: Card ID
	//   required: true
	//   type: string
	// - name: title
	//   in: query
	//   description: Card title
	//   required: true
	//   type: string
	// - name: description
	//   in: query
	//   description: Card description
	//   required: false
	//   type: string
	// security:
	// - BearerAuth: []
	// responses:
	//   '200':
	//     description: success
	//     schema:
	//       "$ref": "#/definitions/SummaryResponse"
	//   default:
	//     description: internal error
	//     schema:
	//       "$ref": "#/definitions/ErrorResponse"

	cardID := mux.Vars(r)["cardID"]
	query := r.URL.Query()

	context := ai.CardContext{
		CardID:      cardID,
		Title:       query.Get("title"),
		Description: query.Get("description"),
	}

	summary, err := h.claude.SummarizeCard(r.Context(), context, nil)
	if err != nil {
		errorResponse(w, err)
		return
	}

	jsonResponse(w, http.StatusOK, SummaryResponse{Summary: summary})
}

// ImproveTitleRequest contains the title to improve
type ImproveTitleRequest struct {
	Title       string `json:"title"`
	Description string `json:"description"`
}

// ImproveTitleResponse contains the improved title
type ImproveTitleResponse struct {
	ImprovedTitle string `json:"improved_title"`
	Original      string `json:"original"`
}

// handleImproveTitle suggests an improved title for a card
func (h *AIHandler) handleImproveTitle(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		errorResponse(w, model.NewErrBadRequest(err.Error()))
		return
	}

	var req ImproveTitleRequest
	if err := json.Unmarshal(body, &req); err != nil {
		errorResponse(w, model.NewErrBadRequest(err.Error()))
		return
	}

	improved, err := h.claude.ImproveTitle(r.Context(), req.Title, req.Description)
	if err != nil {
		errorResponse(w, err)
		return
	}

	jsonResponse(w, http.StatusOK, ImproveTitleResponse{
		ImprovedTitle: improved,
		Original:      req.Title,
	})
}

// NaturalSearchRequest contains a natural language search query
type NaturalSearchRequest struct {
	Query               string   `json:"query"`
	AvailableProperties []string `json:"available_properties"`
}

// NaturalSearchResponse contains parsed filters from natural language
type NaturalSearchResponse struct {
	Query   string                 `json:"query"`
	Filters map[string]interface{} `json:"filters"`
}

// handleNaturalLanguageSearch parses natural language into search filters
func (h *AIHandler) handleNaturalLanguageSearch(w http.ResponseWriter, r *http.Request) {
	// swagger:operation POST /ai/boards/{boardID}/search naturalLanguageSearch
	//
	// Parses natural language search query into filters
	//
	// ---
	// produces:
	// - application/json
	// parameters:
	// - name: boardID
	//   in: path
	//   description: Board ID
	//   required: true
	//   type: string
	// - name: Body
	//   in: body
	//   description: Natural language query
	//   required: true
	//   schema:
	//     "$ref": "#/definitions/NaturalSearchRequest"
	// security:
	// - BearerAuth: []
	// responses:
	//   '200':
	//     description: success
	//     schema:
	//       "$ref": "#/definitions/NaturalSearchResponse"
	//   default:
	//     description: internal error
	//     schema:
	//       "$ref": "#/definitions/ErrorResponse"

	body, err := io.ReadAll(r.Body)
	if err != nil {
		errorResponse(w, model.NewErrBadRequest(err.Error()))
		return
	}

	var req NaturalSearchRequest
	if err := json.Unmarshal(body, &req); err != nil {
		errorResponse(w, model.NewErrBadRequest(err.Error()))
		return
	}

	if req.AvailableProperties == nil {
		req.AvailableProperties = []string{"assignee", "priority", "status", "dueDate", "labels"}
	}

	filters, err := h.claude.ParseNaturalLanguageQuery(r.Context(), req.Query, req.AvailableProperties)
	if err != nil {
		errorResponse(w, err)
		return
	}

	jsonResponse(w, http.StatusOK, NaturalSearchResponse{
		Query:   req.Query,
		Filters: filters,
	})
}

// HealthResponse contains the health status
type HealthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
}

// handleHealth checks the health of the AI service
func (h *AIHandler) handleHealth(w http.ResponseWriter, r *http.Request) {
	err := h.claude.Health(r.Context())
	if err != nil {
		jsonResponse(w, http.StatusServiceUnavailable, HealthResponse{
			Status:  "unhealthy",
			Service: "claude",
		})
		return
	}

	jsonResponse(w, http.StatusOK, HealthResponse{
		Status:  "healthy",
		Service: "claude",
	})
}

// Helper functions

func jsonResponse(w http.ResponseWriter, code int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(data)
}

func errorResponse(w http.ResponseWriter, err error) {
	w.Header().Set("Content-Type", "application/json")

	code := http.StatusInternalServerError
	if model.IsErrBadRequest(err) {
		code = http.StatusBadRequest
	} else if model.IsErrUnauthorized(err) {
		code = http.StatusUnauthorized
	} else if model.IsErrForbidden(err) {
		code = http.StatusForbidden
	} else if model.IsErrNotFound(err) {
		code = http.StatusNotFound
	}

	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
}
