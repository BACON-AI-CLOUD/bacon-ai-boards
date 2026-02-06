// AIButton.tsx - AI action button component for Focalboard
import React, { useState, useCallback } from 'react';

// Types
interface AIButtonProps {
    label: string;
    icon?: React.ReactNode;
    onClick: () => Promise<void>;
    disabled?: boolean;
    loading?: boolean;
    variant?: 'primary' | 'secondary' | 'ghost';
    size?: 'small' | 'medium' | 'large';
    tooltip?: string;
}

// AI sparkle icon SVG
const SparkleIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg
        className={className}
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
        <path d="M5 3v4"/>
        <path d="M3 5h4"/>
        <path d="M19 17v4"/>
        <path d="M17 19h4"/>
    </svg>
);

// Loading spinner
const LoadingSpinner: React.FC<{ className?: string }> = ({ className }) => (
    <svg
        className={`animate-spin ${className || ''}`}
        width="16"
        height="16"
        viewBox="0 0 24 24"
    >
        <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
        />
        <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
    </svg>
);

// Styles
const styles = {
    button: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 12px',
        borderRadius: '4px',
        border: 'none',
        cursor: 'pointer',
        fontFamily: 'inherit',
        fontSize: '14px',
        fontWeight: 500,
        transition: 'all 0.2s ease',
    },
    primary: {
        backgroundColor: '#5C5CFF',
        color: 'white',
    },
    secondary: {
        backgroundColor: '#f0f0f0',
        color: '#333',
        border: '1px solid #ddd',
    },
    ghost: {
        backgroundColor: 'transparent',
        color: '#5C5CFF',
    },
    disabled: {
        opacity: 0.5,
        cursor: 'not-allowed',
    },
    small: {
        padding: '4px 8px',
        fontSize: '12px',
    },
    medium: {
        padding: '6px 12px',
        fontSize: '14px',
    },
    large: {
        padding: '8px 16px',
        fontSize: '16px',
    },
};

export const AIButton: React.FC<AIButtonProps> = ({
    label,
    icon,
    onClick,
    disabled = false,
    loading = false,
    variant = 'primary',
    size = 'medium',
    tooltip,
}) => {
    const [isLoading, setIsLoading] = useState(loading);

    const handleClick = useCallback(async () => {
        if (disabled || isLoading) return;

        setIsLoading(true);
        try {
            await onClick();
        } finally {
            setIsLoading(false);
        }
    }, [onClick, disabled, isLoading]);

    const buttonStyle = {
        ...styles.button,
        ...styles[variant],
        ...styles[size],
        ...(disabled || isLoading ? styles.disabled : {}),
    };

    return (
        <button
            style={buttonStyle}
            onClick={handleClick}
            disabled={disabled || isLoading}
            title={tooltip}
            type="button"
        >
            {isLoading ? (
                <LoadingSpinner />
            ) : (
                icon || <SparkleIcon />
            )}
            {label}
        </button>
    );
};

// Preset AI buttons for common actions
export const GenerateDescriptionButton: React.FC<{
    onGenerate: () => Promise<void>;
    disabled?: boolean;
}> = ({ onGenerate, disabled }) => (
    <AIButton
        label="Generate with AI"
        onClick={onGenerate}
        disabled={disabled}
        tooltip="Use AI to generate a description based on the card title and context"
        variant="ghost"
        size="small"
    />
);

export const SuggestContentButton: React.FC<{
    onSuggest: () => Promise<void>;
    disabled?: boolean;
}> = ({ onSuggest, disabled }) => (
    <AIButton
        label="AI Suggestions"
        onClick={onSuggest}
        disabled={disabled}
        tooltip="Get AI suggestions for content to add to this card"
        variant="secondary"
        size="small"
    />
);

export const SummarizeButton: React.FC<{
    onSummarize: () => Promise<void>;
    disabled?: boolean;
}> = ({ onSummarize, disabled }) => (
    <AIButton
        label="Summarize"
        onClick={onSummarize}
        disabled={disabled}
        tooltip="Generate an AI summary of this card"
        variant="ghost"
        size="small"
    />
);

export default AIButton;
