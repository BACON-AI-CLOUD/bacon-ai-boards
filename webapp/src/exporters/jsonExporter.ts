// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {Board, IPropertyTemplate} from '../blocks/board'
import {BoardView} from '../blocks/boardView'
import {Card} from '../blocks/card'
import {Block} from '../blocks/block'
import {Utils} from '../utils'
import {IAppWindow} from '../types'

declare let window: IAppWindow

/**
 * Interface for the JSON export format used by BACON-AI-BOARDS
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
    views: Array<{
        id: string
        title: string
        viewType: string
        groupById?: string
        sortOptions: Array<{ propertyId: string, reversed: boolean }>
        visiblePropertyIds: string[]
        filter?: unknown
    }>
    cards: Array<{
        id: string
        title: string
        icon?: string
        properties: Record<string, string | string[]>
        contentOrder: Array<string | string[]>
    }>
    blocks: Array<{
        id: string
        parentId: string
        type: string
        title: string
        fields: Record<string, unknown>
    }>
}

/**
 * JsonExporter provides functionality to export board data as JSON files.
 * This enables data portability and backup capabilities for BACON-AI-BOARDS.
 */
class JsonExporter {
    /**
     * Exports a board and all its related data (views, cards, blocks) as a JSON file.
     * The file is automatically downloaded to the user's device.
     *
     * @param board - The board to export
     * @param views - All views associated with the board
     * @param cards - All cards in the board
     * @param blocks - All content blocks (text, images, etc.) within the cards
     */
    static exportBoardJson(board: Board, views: BoardView[], cards: Card[], blocks: Block[]): void {
        const exportData = JsonExporter.generateBoardData(board, views, cards, blocks)
        JsonExporter.downloadJson(exportData, board.title || 'board')
    }

    /**
     * Generates the complete export data structure following the BoardJsonExport schema.
     *
     * @param board - The board to export
     * @param views - All views associated with the board
     * @param cards - All cards in the board
     * @param blocks - All content blocks within the cards
     * @returns The complete export object ready for serialization
     */
    private static generateBoardData(
        board: Board,
        views: BoardView[],
        cards: Card[],
        blocks: Block[],
    ): BoardJsonExport {
        return {
            version: '1.0',
            format: 'bacon-ai-boards-json',
            exportDate: Date.now(),
            board: {
                id: board.id,
                title: board.title,
                description: board.description,
                icon: board.icon,
                type: board.type,
                cardProperties: board.cardProperties,
                properties: board.properties,
            },
            views: views.map((view) => ({
                id: view.id,
                title: view.title,
                viewType: view.fields.viewType,
                groupById: view.fields.groupById,
                sortOptions: view.fields.sortOptions,
                visiblePropertyIds: view.fields.visiblePropertyIds,
                filter: view.fields.filter,
            })),
            cards: cards.map((card) => ({
                id: card.id,
                title: card.title,
                icon: card.fields.icon,
                properties: card.fields.properties,
                contentOrder: card.fields.contentOrder,
            })),
            blocks: blocks.map((block) => ({
                id: block.id,
                parentId: block.parentId,
                type: block.type,
                title: block.title,
                fields: block.fields,
            })),
        }
    }

    /**
     * Creates and triggers a download of the JSON data as a file.
     * Uses the same download pattern as archiver.ts for consistency.
     *
     * @param data - The data object to serialize and download
     * @param boardTitle - The board title used for generating the filename
     */
    private static downloadJson(data: BoardJsonExport, boardTitle: string): void {
        const jsonString = JSON.stringify(data, null, 2)
        const blob = new Blob([jsonString], {type: 'application/json'})

        const link = document.createElement('a')
        link.style.display = 'none'

        const filename = `${Utils.sanitizeFilename(boardTitle)}.json`
        link.href = URL.createObjectURL(blob)
        link.download = filename

        // FireFox support
        document.body.appendChild(link)

        link.click()

        // Support for Linux webview links
        if (window.openInNewBrowser) {
            window.openInNewBrowser(link.href)
        }

        // Clean up: remove link and revoke object URL to prevent memory leak
        setTimeout(() => {
            document.body.removeChild(link)
            URL.revokeObjectURL(link.href)
        }, 100)
    }
}

export {JsonExporter, BoardJsonExport}
