// AISearchInput.tsx - Natural language search component
import React, { useState, useCallback, useRef, useEffect } from 'react';

// Types
interface SearchFilter {
    property: string;
    operator: string;
    value: any;
}

interface AISearchInputProps {
    boardId: string;
    onFiltersGenerated: (filters: SearchFilter[]) => void;
    availableProperties?: string[];
    placeholder?: string;
}

// Styles
const styles = {
    container: {
        position: 'relative' as const,
        width: '100%',
        maxWidth: '500px',
    },
    inputWrapper: {
        display: 'flex',
        alignItems: 'center',
        border: '1px solid #ddd',
        borderRadius: '8px',
        backgroundColor: 'white',
        overflow: 'hidden',
        transition: 'border-color 0.2s, box-shadow 0.2s',
    },
    inputWrapperFocused: {
        borderColor: '#5C5CFF',
        boxShadow: '0 0 0 3px rgba(92, 92, 255, 0.1)',
    },
    aiToggle: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        padding: '8px 12px',
        backgroundColor: '#f8f8ff',
        borderRight: '1px solid #ddd',
        cursor: 'pointer',
        fontSize: '13px',
        color: '#5C5CFF',
        fontWeight: 500,
        userSelect: 'none' as const,
        transition: 'background-color 0.2s',
    },
    aiToggleActive: {
        backgroundColor: '#5C5CFF',
        color: 'white',
    },
    input: {
        flex: 1,
        border: 'none',
        outline: 'none',
        padding: '10px 12px',
        fontSize: '14px',
        backgroundColor: 'transparent',
    },
    searchButton: {
        padding: '8px 16px',
        backgroundColor: '#5C5CFF',
        color: 'white',
        border: 'none',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
    },
    searchButtonDisabled: {
        backgroundColor: '#ccc',
        cursor: 'not-allowed',
    },
    dropdown: {
        position: 'absolute' as const,
        top: '100%',
        left: 0,
        right: 0,
        marginTop: '4px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        zIndex: 100,
        overflow: 'hidden',
    },
    dropdownHeader: {
        padding: '12px 16px',
        backgroundColor: '#f8f8ff',
        borderBottom: '1px solid #eee',
        fontSize: '12px',
        color: '#666',
    },
    filterList: {
        padding: '8px',
    },
    filterItem: {
        display: 'flex',
        alignItems: 'center',
        padding: '8px 12px',
        borderRadius: '4px',
        marginBottom: '4px',
        backgroundColor: '#f5f5f5',
        fontSize: '13px',
    },
    filterProperty: {
        fontWeight: 600,
        color: '#5C5CFF',
        marginRight: '8px',
    },
    filterOperator: {
        color: '#888',
        marginRight: '8px',
    },
    filterValue: {
        color: '#333',
    },
    applyButton: {
        width: '100%',
        padding: '10px',
        backgroundColor: '#5C5CFF',
        color: 'white',
        border: 'none',
        borderTop: '1px solid #eee',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 500,
    },
    exampleQueries: {
        padding: '12px 16px',
        fontSize: '12px',
        color: '#888',
        borderTop: '1px solid #eee',
    },
    exampleQuery: {
        display: 'inline-block',
        padding: '4px 8px',
        backgroundColor: '#f0f0f0',
        borderRadius: '4px',
        margin: '2px',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
    },
    loading: {
        padding: '20px',
        textAlign: 'center' as const,
        color: '#666',
    },
};

// Sparkle icon
const SparkleIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
    </svg>
);

// API call to parse natural language
const parseNaturalLanguageQuery = async (
    boardId: string,
    query: string,
    availableProperties: string[]
): Promise<{ filters: SearchFilter[] }> => {
    const response = await fetch(`/api/v2/ai/boards/${boardId}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
            query,
            available_properties: availableProperties,
        }),
    });

    if (!response.ok) {
        throw new Error('Failed to parse query');
    }

    return response.json();
};

export const AISearchInput: React.FC<AISearchInputProps> = ({
    boardId,
    onFiltersGenerated,
    availableProperties = ['assignee', 'priority', 'status', 'dueDate', 'labels'],
    placeholder = 'Search cards...',
}) => {
    const [query, setQuery] = useState('');
    const [aiMode, setAiMode] = useState(false);
    const [focused, setFocused] = useState(false);
    const [loading, setLoading] = useState(false);
    const [parsedFilters, setParsedFilters] = useState<SearchFilter[] | null>(null);
    const [showDropdown, setShowDropdown] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const exampleQueries = [
        'urgent tasks due this week',
        'assigned to John',
        'high priority bugs',
        'completed last month',
    ];

    const handleSearch = useCallback(async () => {
        if (!query.trim() || !aiMode) return;

        setLoading(true);
        try {
            const result = await parseNaturalLanguageQuery(boardId, query, availableProperties);
            setParsedFilters(result.filters as SearchFilter[]);
            setShowDropdown(true);
        } catch (error) {
            console.error('Search parse error:', error);
        } finally {
            setLoading(false);
        }
    }, [query, boardId, availableProperties, aiMode]);

    const handleApplyFilters = useCallback(() => {
        if (parsedFilters) {
            onFiltersGenerated(parsedFilters);
            setShowDropdown(false);
            setQuery('');
            setParsedFilters(null);
        }
    }, [parsedFilters, onFiltersGenerated]);

    const handleExampleClick = (example: string) => {
        setQuery(example);
        setAiMode(true);
        inputRef.current?.focus();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && aiMode) {
            handleSearch();
        }
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (!(e.target as Element).closest('.ai-search-container')) {
                setShowDropdown(false);
            }
        };

        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    return (
        <div style={styles.container} className="ai-search-container">
            <div
                style={{
                    ...styles.inputWrapper,
                    ...(focused ? styles.inputWrapperFocused : {}),
                }}
            >
                <div
                    style={{
                        ...styles.aiToggle,
                        ...(aiMode ? styles.aiToggleActive : {}),
                    }}
                    onClick={() => setAiMode(!aiMode)}
                    title="Toggle AI-powered search"
                >
                    <SparkleIcon />
                    AI
                </div>
                <input
                    ref={inputRef}
                    style={styles.input}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    onKeyDown={handleKeyDown}
                    placeholder={aiMode ? 'Ask in natural language...' : placeholder}
                />
                <button
                    style={{
                        ...styles.searchButton,
                        ...((!query.trim() || loading) ? styles.searchButtonDisabled : {}),
                    }}
                    onClick={aiMode ? handleSearch : undefined}
                    disabled={!query.trim() || loading}
                >
                    {loading ? '...' : '🔍'}
                </button>
            </div>

            {showDropdown && (
                <div style={styles.dropdown}>
                    {loading ? (
                        <div style={styles.loading}>
                            ✨ Parsing your query...
                        </div>
                    ) : parsedFilters && parsedFilters.length > 0 ? (
                        <>
                            <div style={styles.dropdownHeader}>
                                Generated filters from: "{query}"
                            </div>
                            <div style={styles.filterList}>
                                {parsedFilters.map((filter, index) => (
                                    <div key={index} style={styles.filterItem}>
                                        <span style={styles.filterProperty}>
                                            {filter.property}
                                        </span>
                                        <span style={styles.filterOperator}>
                                            {filter.operator}
                                        </span>
                                        <span style={styles.filterValue}>
                                            {String(filter.value)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                            <button style={styles.applyButton} onClick={handleApplyFilters}>
                                Apply Filters
                            </button>
                        </>
                    ) : (
                        <div style={styles.loading}>
                            No filters generated. Try a different query.
                        </div>
                    )}
                </div>
            )}

            {aiMode && !showDropdown && query.length === 0 && (
                <div style={styles.dropdown}>
                    <div style={styles.exampleQueries}>
                        <strong>Try asking:</strong>
                        <div style={{ marginTop: '8px' }}>
                            {exampleQueries.map((example, index) => (
                                <span
                                    key={index}
                                    style={styles.exampleQuery}
                                    onClick={() => handleExampleClick(example)}
                                >
                                    {example}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AISearchInput;
