// aiClient.ts - Claude AI API client for Focalboard
// This client communicates with the Focalboard backend which proxies to Claude Code CLI

interface CardContext {
    cardId: string;
    title: string;
    description?: string;
    boardTitle?: string;
    labels?: string[];
    properties?: Record<string, any>;
}

interface ContentSuggestion {
    type: string;
    content: string;
    confidence: number;
    explanation?: string;
}

interface GeneratedDescription {
    description: string;
    model: string;
}

interface ImproveTitleResult {
    improvedTitle: string;
    original: string;
}

interface SearchFilter {
    property: string;
    operator: string;
    value: any;
}

interface HealthStatus {
    status: 'healthy' | 'unhealthy';
    service: string;
}

// API base URL - can be overridden for different environments
const API_BASE = '/api/v2/ai';

// Common headers for all requests
const getHeaders = (): HeadersInit => ({
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest', // Required for CSRF protection
});

// Error handling wrapper
class AIError extends Error {
    constructor(
        message: string,
        public statusCode: number,
        public details?: any
    ) {
        super(message);
        this.name = 'AIError';
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new AIError(
            errorData.error || `Request failed with status ${response.status}`,
            response.status,
            errorData
        );
    }
    return response.json();
}

/**
 * Claude AI API Client
 *
 * Usage:
 * ```typescript
 * import { aiClient } from './aiClient';
 *
 * // Generate description
 * const desc = await aiClient.generateDescription({
 *   cardId: '123',
 *   title: 'Implement login feature',
 *   boardTitle: 'Product Backlog'
 * });
 *
 * // Get suggestions
 * const suggestions = await aiClient.getSuggestions('123', 'My Task');
 *
 * // Natural language search
 * const filters = await aiClient.parseSearchQuery('board123', 'urgent tasks due tomorrow');
 * ```
 */
export const aiClient = {
    /**
     * Generate a description for a card using AI
     */
    async generateDescription(context: CardContext): Promise<GeneratedDescription> {
        const response = await fetch(`${API_BASE}/cards/${context.cardId}/description`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ context }),
        });
        return handleResponse<GeneratedDescription>(response);
    },

    /**
     * Get AI-powered content suggestions for a card
     */
    async getSuggestions(
        cardId: string,
        title: string,
        description?: string
    ): Promise<ContentSuggestion[]> {
        const params = new URLSearchParams({ title });
        if (description) {
            params.append('description', description);
        }

        const response = await fetch(
            `${API_BASE}/cards/${cardId}/suggestions?${params}`,
            { headers: getHeaders() }
        );
        const data = await handleResponse<{ suggestions: ContentSuggestion[] }>(response);
        return data.suggestions;
    },

    /**
     * Get an AI-generated summary of a card
     */
    async getSummary(
        cardId: string,
        title: string,
        description?: string
    ): Promise<string> {
        const params = new URLSearchParams({ title });
        if (description) {
            params.append('description', description);
        }

        const response = await fetch(
            `${API_BASE}/cards/${cardId}/summary?${params}`,
            { headers: getHeaders() }
        );
        const data = await handleResponse<{ summary: string }>(response);
        return data.summary;
    },

    /**
     * Suggest an improved title for a card
     */
    async improveTitle(
        cardId: string,
        title: string,
        description?: string
    ): Promise<ImproveTitleResult> {
        const response = await fetch(`${API_BASE}/cards/${cardId}/improve-title`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ title, description }),
        });
        const data = await handleResponse<{ improved_title: string; original: string }>(response);
        return {
            improvedTitle: data.improved_title,
            original: data.original,
        };
    },

    /**
     * Parse a natural language search query into filter objects
     */
    async parseSearchQuery(
        boardId: string,
        query: string,
        availableProperties?: string[]
    ): Promise<SearchFilter[]> {
        const response = await fetch(`${API_BASE}/boards/${boardId}/search`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                query,
                available_properties: availableProperties || [
                    'assignee',
                    'priority',
                    'status',
                    'dueDate',
                    'labels',
                ],
            }),
        });
        const data = await handleResponse<{ filters: { filters: SearchFilter[] } }>(response);
        return data.filters.filters || [];
    },

    /**
     * Check the health of the AI service
     */
    async checkHealth(): Promise<HealthStatus> {
        const response = await fetch(`${API_BASE}/health`, {
            headers: getHeaders(),
        });
        return handleResponse<HealthStatus>(response);
    },
};

// React hooks for AI operations
import { useState, useCallback } from 'react';

/**
 * Hook for generating card descriptions
 */
export function useGenerateDescription() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generate = useCallback(async (context: CardContext): Promise<string | null> => {
        setLoading(true);
        setError(null);
        try {
            const result = await aiClient.generateDescription(context);
            return result.description;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate description');
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return { generate, loading, error };
}

/**
 * Hook for getting content suggestions
 */
export function useSuggestions() {
    const [suggestions, setSuggestions] = useState<ContentSuggestion[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchSuggestions = useCallback(async (
        cardId: string,
        title: string,
        description?: string
    ) => {
        setLoading(true);
        setError(null);
        try {
            const result = await aiClient.getSuggestions(cardId, title, description);
            setSuggestions(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch suggestions');
            setSuggestions([]);
        } finally {
            setLoading(false);
        }
    }, []);

    return { suggestions, fetchSuggestions, loading, error };
}

/**
 * Hook for natural language search
 */
export function useNaturalLanguageSearch(boardId: string) {
    const [filters, setFilters] = useState<SearchFilter[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const search = useCallback(async (query: string) => {
        setLoading(true);
        setError(null);
        try {
            const result = await aiClient.parseSearchQuery(boardId, query);
            setFilters(result);
            return result;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to parse search query');
            setFilters([]);
            return [];
        } finally {
            setLoading(false);
        }
    }, [boardId]);

    const clearFilters = useCallback(() => {
        setFilters([]);
    }, []);

    return { filters, search, clearFilters, loading, error };
}

export default aiClient;
export { AIError };
export type {
    CardContext,
    ContentSuggestion,
    GeneratedDescription,
    ImproveTitleResult,
    SearchFilter,
    HealthStatus,
};
