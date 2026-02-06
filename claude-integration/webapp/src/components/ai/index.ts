// AI Components for Focalboard
// Export all AI-related components and utilities

// Components
export { AIButton, GenerateDescriptionButton, SuggestContentButton, SummarizeButton } from './AIButton';
export { AISuggestionPanel } from './AISuggestionPanel';
export { AISearchInput } from './AISearchInput';

// API Client and Hooks
export {
    aiClient,
    useGenerateDescription,
    useSuggestions,
    useNaturalLanguageSearch,
    AIError,
} from './aiClient';

// Types
export type {
    CardContext,
    ContentSuggestion,
    GeneratedDescription,
    ImproveTitleResult,
    SearchFilter,
    HealthStatus,
} from './aiClient';
