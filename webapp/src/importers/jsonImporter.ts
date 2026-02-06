// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {Board, BoardsAndBlocks, IPropertyTemplate, MemberRole} from '../blocks/board'
import {BoardView} from '../blocks/boardView'
import {Card} from '../blocks/card'
import {Block} from '../blocks/block'
import {Utils} from '../utils'
import mutator from '../mutator'

/**
 * Result interface for JSON import operations
 */
interface ImportResult {
    success: boolean
    boardId?: string
    error?: string
    boardsCreated?: number
    blocksCreated?: number
}

/**
 * JSON export schema for BACON-AI-BOARDS
 */
interface BoardJsonExport {
    version: '1.0'
    format: 'bacon-ai-boards-json'
    exportDate: number
    board: {
        id: string
        title: string
        description: string
        icon?: string
        type: string
        cardProperties: IPropertyTemplate[]
        properties: Record<string, string | string[]>
    }
    views: BoardView[]
    cards: Card[]
    blocks: Block[]
}

/**
 * JSON Importer for BACON-AI-BOARDS
 * Imports board data from JSON files following the BoardJsonExport schema
 */
class JsonImporter {
    /**
     * Opens a file picker dialog and imports board data from a selected JSON file
     * @param onComplete Callback function called when import completes
     */
    static importBoardJson(onComplete?: (result: ImportResult) => void): void {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.json'
        input.onchange = async () => {
            const file = input.files && input.files[0]
            if (file) {
                const result = await JsonImporter.processJsonFile(file)
                onComplete?.(result)
            } else {
                onComplete?.({
                    success: false,
                    error: 'No file selected',
                })
            }
        }

        input.style.display = 'none'
        document.body.appendChild(input)
        input.click()

        // Clean up input element after file dialog closes
        setTimeout(() => {
            if (input.parentNode) {
                input.parentNode.removeChild(input)
            }
        }, 1000)
    }

    /**
     * Processes a JSON file and imports the board data
     * @param file The JSON file to process
     * @returns ImportResult with success status and details
     */
    private static async processJsonFile(file: File): Promise<ImportResult> {
        try {
            const data = await JsonImporter.parseJsonFile(file)

            const validationResult = JsonImporter.validateSchema(data)
            if (!validationResult.valid) {
                return {
                    success: false,
                    error: validationResult.error,
                }
            }

            return await JsonImporter.importBoardData(data as BoardJsonExport)
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            Utils.logError(`JsonImporter: Error processing file: ${errorMessage}`)
            return {
                success: false,
                error: `Failed to process file: ${errorMessage}`,
            }
        }
    }

    /**
     * Parses a JSON file and returns the parsed object
     * @param file The file to parse
     * @returns Parsed JSON object
     */
    private static async parseJsonFile(file: File): Promise<unknown> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = (event) => {
                try {
                    const content = event.target?.result as string
                    const parsed = JSON.parse(content)
                    resolve(parsed)
                } catch (error) {
                    reject(new Error('Invalid JSON format'))
                }
            }
            reader.onerror = () => {
                reject(new Error('Failed to read file'))
            }
            reader.readAsText(file)
        })
    }

    /**
     * Validates that the JSON data matches the expected BoardJsonExport schema
     * @param data The parsed JSON data to validate
     * @returns Validation result with valid flag and optional error message
     */
    private static validateSchema(data: unknown): {valid: boolean, error?: string} {
        if (!data || typeof data !== 'object') {
            return {valid: false, error: 'Invalid data: expected an object'}
        }

        const obj = data as Record<string, unknown>

        // Validate version
        if (obj.version !== '1.0') {
            return {valid: false, error: `Unsupported version: ${obj.version}. Expected version 1.0`}
        }

        // Validate format
        if (obj.format !== 'bacon-ai-boards-json') {
            return {valid: false, error: `Invalid format: ${obj.format}. Expected bacon-ai-boards-json`}
        }

        // Validate exportDate
        if (typeof obj.exportDate !== 'number') {
            return {valid: false, error: 'Missing or invalid exportDate'}
        }

        // Validate board
        if (!obj.board || typeof obj.board !== 'object') {
            return {valid: false, error: 'Missing or invalid board data'}
        }

        const board = obj.board as Record<string, unknown>
        if (!board.id || typeof board.id !== 'string') {
            return {valid: false, error: 'Board is missing required field: id'}
        }
        if (!board.title || typeof board.title !== 'string') {
            return {valid: false, error: 'Board is missing required field: title'}
        }
        if (typeof board.description !== 'string') {
            return {valid: false, error: 'Board is missing required field: description'}
        }
        if (!board.type || typeof board.type !== 'string') {
            return {valid: false, error: 'Board is missing required field: type'}
        }
        if (!Array.isArray(board.cardProperties)) {
            return {valid: false, error: 'Board is missing required field: cardProperties (must be an array)'}
        }
        if (!board.properties || typeof board.properties !== 'object') {
            return {valid: false, error: 'Board is missing required field: properties'}
        }

        // Validate views array
        if (!Array.isArray(obj.views)) {
            return {valid: false, error: 'Missing or invalid views array'}
        }

        // Validate cards array
        if (!Array.isArray(obj.cards)) {
            return {valid: false, error: 'Missing or invalid cards array'}
        }

        // Validate blocks array
        if (!Array.isArray(obj.blocks)) {
            return {valid: false, error: 'Missing or invalid blocks array'}
        }

        // Validate each view has required fields
        for (let i = 0; i < (obj.views as unknown[]).length; i++) {
            const view = (obj.views as unknown[])[i] as Record<string, unknown>
            if (!view.id || !view.boardId) {
                return {valid: false, error: `View at index ${i} is missing required fields (id, boardId)`}
            }
        }

        // Validate each card has required fields
        for (let i = 0; i < (obj.cards as unknown[]).length; i++) {
            const card = (obj.cards as unknown[])[i] as Record<string, unknown>
            if (!card.id || !card.boardId) {
                return {valid: false, error: `Card at index ${i} is missing required fields (id, boardId)`}
            }
        }

        // Validate each block has required fields
        for (let i = 0; i < (obj.blocks as unknown[]).length; i++) {
            const block = (obj.blocks as unknown[])[i] as Record<string, unknown>
            if (!block.id || !block.boardId) {
                return {valid: false, error: `Block at index ${i} is missing required fields (id, boardId)`}
            }
        }

        return {valid: true}
    }

    /**
     * Imports the board data using the mutator API
     * @param data The validated BoardJsonExport data
     * @returns ImportResult with success status and created board ID
     */
    private static async importBoardData(data: BoardJsonExport): Promise<ImportResult> {
        try {
            // Create the board object from the export data
            const board: Board = {
                id: data.board.id,
                teamId: '', // Will be set by the server based on context
                createdBy: '',
                modifiedBy: '',
                type: data.board.type as 'O' | 'P',
                minimumRole: MemberRole.None,
                title: data.board.title,
                description: data.board.description,
                icon: data.board.icon,
                showDescription: false,
                isTemplate: false,
                templateVersion: 0,
                properties: data.board.properties,
                cardProperties: data.board.cardProperties,
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
            }

            // Combine all blocks: views, cards, and other blocks
            const allBlocks: Block[] = [
                ...data.views as Block[],
                ...data.cards as Block[],
                ...data.blocks,
            ]

            // Create the BoardsAndBlocks structure
            const boardsAndBlocks: BoardsAndBlocks = {
                boards: [board],
                blocks: allBlocks,
            }

            Utils.log(`JsonImporter: Importing board "${board.title}" with ${allBlocks.length} blocks`)

            // Use mutator to create the board and blocks
            const result = await mutator.createBoardsAndBlocks(
                boardsAndBlocks,
                'import board from JSON',
            )

            if (result && result.boards && result.boards.length > 0) {
                Utils.log(`JsonImporter: Successfully imported board with ID ${result.boards[0].id}`)
                return {
                    success: true,
                    boardId: result.boards[0].id,
                    boardsCreated: result.boards.length,
                    blocksCreated: result.blocks?.length || 0,
                }
            }

            return {
                success: false,
                error: 'Failed to create board: no board returned from server',
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            Utils.logError(`JsonImporter: Error importing board data: ${errorMessage}`)
            return {
                success: false,
                error: `Failed to import board: ${errorMessage}`,
            }
        }
    }

    /**
     * Imports board data from a JSON string (useful for programmatic imports)
     * @param jsonString The JSON string to import
     * @returns ImportResult with success status and details
     */
    static async importFromString(jsonString: string): Promise<ImportResult> {
        try {
            const data = JSON.parse(jsonString)

            const validationResult = JsonImporter.validateSchema(data)
            if (!validationResult.valid) {
                return {
                    success: false,
                    error: validationResult.error,
                }
            }

            return await JsonImporter.importBoardData(data as BoardJsonExport)
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            return {
                success: false,
                error: `Failed to parse JSON: ${errorMessage}`,
            }
        }
    }
}

export {JsonImporter, ImportResult, BoardJsonExport}
