// AISuggestionPanel.tsx - Panel displaying AI-generated suggestions
import React, { useState, useEffect } from 'react';

// Types
interface ContentSuggestion {
    type: 'text' | 'checkbox' | 'divider' | 'h1' | 'h2' | 'h3';
    content: string;
    confidence: number;
    explanation?: string;
}

interface AISuggestionPanelProps {
    cardId: string;
    cardTitle: string;
    cardDescription?: string;
    onApplySuggestion: (suggestion: ContentSuggestion) => void;
    onClose: () => void;
}

// Styles
const styles = {
    overlay: {
        position: 'fixed' as const,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
    },
    panel: {
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
        width: '500px',
        maxWidth: '90vw',
        maxHeight: '80vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column' as const,
    },
    header: {
        padding: '16px 20px',
        borderBottom: '1px solid #eee',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    headerTitle: {
        margin: 0,
        fontSize: '16px',
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
    },
    closeButton: {
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '4px',
        borderRadius: '4px',
        color: '#666',
    },
    content: {
        padding: '16px 20px',
        overflowY: 'auto' as const,
        flex: 1,
    },
    loading: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        color: '#666',
    },
    suggestionList: {
        listStyle: 'none',
        padding: 0,
        margin: 0,
    },
    suggestionItem: {
        padding: '12px',
        borderRadius: '6px',
        border: '1px solid #e0e0e0',
        marginBottom: '8px',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
    },
    suggestionItemHover: {
        borderColor: '#5C5CFF',
        backgroundColor: '#f8f8ff',
    },
    suggestionHeader: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '8px',
    },
    typeTag: {
        fontSize: '11px',
        fontWeight: 600,
        textTransform: 'uppercase' as const,
        padding: '2px 6px',
        borderRadius: '4px',
        backgroundColor: '#e8e8ff',
        color: '#5C5CFF',
    },
    confidence: {
        fontSize: '12px',
        color: '#888',
    },
    suggestionContent: {
        fontSize: '14px',
        color: '#333',
        lineHeight: 1.5,
    },
    applyButton: {
        marginTop: '8px',
        padding: '6px 12px',
        fontSize: '13px',
        backgroundColor: '#5C5CFF',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
    },
    error: {
        padding: '20px',
        textAlign: 'center' as const,
        color: '#d32f2f',
    },
    footer: {
        padding: '12px 20px',
        borderTop: '1px solid #eee',
        fontSize: '12px',
        color: '#888',
        textAlign: 'center' as const,
    },
};

// AI client for fetching suggestions
const fetchSuggestions = async (
    cardId: string,
    title: string,
    description?: string
): Promise<ContentSuggestion[]> => {
    const params = new URLSearchParams({ title });
    if (description) params.append('description', description);

    const response = await fetch(
        `/api/v2/ai/cards/${cardId}/suggestions?${params}`,
        {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        }
    );

    if (!response.ok) {
        throw new Error('Failed to fetch suggestions');
    }

    const data = await response.json();
    return data.suggestions;
};

// Type icons
const TypeIcon: React.FC<{ type: string }> = ({ type }) => {
    const icons: Record<string, string> = {
        text: '📝',
        checkbox: '☑️',
        divider: '➖',
        h1: 'H1',
        h2: 'H2',
        h3: 'H3',
    };
    return <span>{icons[type] || '📄'}</span>;
};

// Sparkle icon for header
const SparkleIcon = () => (
    <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#5C5CFF"
        strokeWidth="2"
    >
        <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
    </svg>
);

export const AISuggestionPanel: React.FC<AISuggestionPanelProps> = ({
    cardId,
    cardTitle,
    cardDescription,
    onApplySuggestion,
    onClose,
}) => {
    const [suggestions, setSuggestions] = useState<ContentSuggestion[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

    useEffect(() => {
        const loadSuggestions = async () => {
            setLoading(true);
            setError(null);
            try {
                const result = await fetchSuggestions(cardId, cardTitle, cardDescription);
                setSuggestions(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load suggestions');
            } finally {
                setLoading(false);
            }
        };

        loadSuggestions();
    }, [cardId, cardTitle, cardDescription]);

    const handleApply = (suggestion: ContentSuggestion) => {
        onApplySuggestion(suggestion);
    };

    return (
        <div style={styles.overlay} onClick={onClose}>
            <div style={styles.panel} onClick={(e) => e.stopPropagation()}>
                <div style={styles.header}>
                    <h3 style={styles.headerTitle}>
                        <SparkleIcon />
                        AI Suggestions
                    </h3>
                    <button style={styles.closeButton} onClick={onClose}>
                        ✕
                    </button>
                </div>

                <div style={styles.content}>
                    {loading && (
                        <div style={styles.loading}>
                            <span>✨ Generating suggestions...</span>
                        </div>
                    )}

                    {error && (
                        <div style={styles.error}>
                            <p>{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                style={{
                                    ...styles.applyButton,
                                    backgroundColor: '#d32f2f',
                                }}
                            >
                                Retry
                            </button>
                        </div>
                    )}

                    {!loading && !error && suggestions.length === 0 && (
                        <div style={styles.loading}>
                            <span>No suggestions available</span>
                        </div>
                    )}

                    {!loading && !error && suggestions.length > 0 && (
                        <ul style={styles.suggestionList}>
                            {suggestions.map((suggestion, index) => (
                                <li
                                    key={index}
                                    style={{
                                        ...styles.suggestionItem,
                                        ...(hoveredIndex === index ? styles.suggestionItemHover : {}),
                                    }}
                                    onMouseEnter={() => setHoveredIndex(index)}
                                    onMouseLeave={() => setHoveredIndex(null)}
                                >
                                    <div style={styles.suggestionHeader}>
                                        <span style={styles.typeTag}>
                                            <TypeIcon type={suggestion.type} /> {suggestion.type}
                                        </span>
                                        <span style={styles.confidence}>
                                            {Math.round(suggestion.confidence * 100)}% confidence
                                        </span>
                                    </div>
                                    <div style={styles.suggestionContent}>
                                        {suggestion.content}
                                    </div>
                                    {suggestion.explanation && (
                                        <div style={{ ...styles.confidence, marginTop: '4px' }}>
                                            💡 {suggestion.explanation}
                                        </div>
                                    )}
                                    <button
                                        style={styles.applyButton}
                                        onClick={() => handleApply(suggestion)}
                                    >
                                        Add to Card
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div style={styles.footer}>
                    Powered by Claude AI • Using subscription-based access
                </div>
            </div>
        </div>
    );
};

export default AISuggestionPanel;
