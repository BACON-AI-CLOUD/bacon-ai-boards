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
 * XmlExporter provides functionality to export board data as XML files.
 * This enables data portability and backup capabilities for BACON-AI-BOARDS.
 */
class XmlExporter {
    /**
     * Exports a board and all its related data (views, cards, blocks) as an XML file.
     * The file is automatically downloaded to the user's device.
     *
     * @param board - The board to export
     * @param views - All views associated with the board
     * @param cards - All cards in the board
     * @param blocks - All content blocks (text, images, etc.) within the cards
     */
    static exportBoardXml(board: Board, views: BoardView[], cards: Card[], blocks: Block[]): void {
        const xmlString = XmlExporter.generateBoardXml(board, views, cards, blocks)
        XmlExporter.downloadXml(xmlString, board.title || 'board')
    }

    /**
     * Generates the complete XML string following the BACON-AI-BOARDS XML schema.
     *
     * @param board - The board to export
     * @param views - All views associated with the board
     * @param cards - All cards in the board
     * @param blocks - All content blocks within the cards
     * @returns The complete XML string
     */
    private static generateBoardXml(
        board: Board,
        views: BoardView[],
        cards: Card[],
        blocks: Block[],
    ): string {
        const exportDate = Date.now()
        const lines: string[] = []

        lines.push('<?xml version="1.0" encoding="UTF-8"?>')
        lines.push(`<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${exportDate}">`)

        // Board element
        lines.push(`  <board id="${XmlExporter.escapeXml(board.id)}" title="${XmlExporter.escapeXml(board.title)}" description="${XmlExporter.escapeXml(board.description)}" type="${XmlExporter.escapeXml(board.type)}">`)

        if (board.icon) {
            lines.push(`    <icon>${XmlExporter.escapeXml(board.icon)}</icon>`)
        }

        // Card properties
        lines.push('    <cardProperties>')
        board.cardProperties.forEach((prop: IPropertyTemplate) => {
            lines.push(`      <property id="${XmlExporter.escapeXml(prop.id)}" name="${XmlExporter.escapeXml(prop.name)}" type="${XmlExporter.escapeXml(prop.type)}" />`)
        })
        lines.push('    </cardProperties>')

        // Board properties
        lines.push('    <properties>')
        Object.entries(board.properties).forEach(([key, value]) => {
            const valueStr = Array.isArray(value) ? value.join(',') : value
            lines.push(`      <property key="${XmlExporter.escapeXml(key)}">${XmlExporter.escapeXml(valueStr)}</property>`)
        })
        lines.push('    </properties>')

        lines.push('  </board>')

        // Views
        lines.push('  <views>')
        views.forEach((view) => {
            const groupByIdAttr = view.fields.groupById ? ` groupById="${XmlExporter.escapeXml(view.fields.groupById)}"` : ''
            lines.push(`    <view id="${XmlExporter.escapeXml(view.id)}" title="${XmlExporter.escapeXml(view.title)}" viewType="${XmlExporter.escapeXml(view.fields.viewType)}"${groupByIdAttr}>`)

            // Sort options
            lines.push('      <sortOptions>')
            view.fields.sortOptions.forEach((sort) => {
                lines.push(`        <sort propertyId="${XmlExporter.escapeXml(sort.propertyId)}" reversed="${sort.reversed}" />`)
            })
            lines.push('      </sortOptions>')

            // Visible property IDs
            lines.push('      <visiblePropertyIds>')
            view.fields.visiblePropertyIds.forEach((propId) => {
                lines.push(`        <propertyId>${XmlExporter.escapeXml(propId)}</propertyId>`)
            })
            lines.push('      </visiblePropertyIds>')

            lines.push('    </view>')
        })
        lines.push('  </views>')

        // Cards
        lines.push('  <cards>')
        cards.forEach((card) => {
            lines.push(`    <card id="${XmlExporter.escapeXml(card.id)}" title="${XmlExporter.escapeXml(card.title)}">`)

            if (card.fields.icon) {
                lines.push(`      <icon>${XmlExporter.escapeXml(card.fields.icon)}</icon>`)
            }

            // Card properties
            lines.push('      <properties>')
            Object.entries(card.fields.properties).forEach(([key, value]) => {
                const valueStr = Array.isArray(value) ? value.join(',') : value
                lines.push(`        <property key="${XmlExporter.escapeXml(key)}">${XmlExporter.escapeXml(valueStr)}</property>`)
            })
            lines.push('      </properties>')

            // Content order
            lines.push('      <contentOrder>')
            card.fields.contentOrder.forEach((contentId) => {
                if (Array.isArray(contentId)) {
                    lines.push(`        <contentId>${XmlExporter.escapeXml(contentId.join(','))}</contentId>`)
                } else {
                    lines.push(`        <contentId>${XmlExporter.escapeXml(contentId)}</contentId>`)
                }
            })
            lines.push('      </contentOrder>')

            lines.push('    </card>')
        })
        lines.push('  </cards>')

        // Blocks
        lines.push('  <blocks>')
        blocks.forEach((block) => {
            lines.push(`    <block id="${XmlExporter.escapeXml(block.id)}" parentId="${XmlExporter.escapeXml(block.parentId)}" type="${XmlExporter.escapeXml(block.type)}" title="${XmlExporter.escapeXml(block.title)}">`)
            lines.push(`      <fields>${XmlExporter.escapeXml(JSON.stringify(block.fields))}</fields>`)
            lines.push('    </block>')
        })
        lines.push('  </blocks>')

        lines.push('</bacon-ai-boards>')

        return lines.join('\n')
    }

    /**
     * Creates and triggers a download of the XML data as a file.
     * Uses the same download pattern as archiver.ts and jsonExporter.ts for consistency.
     *
     * @param xmlString - The XML string to download
     * @param boardTitle - The board title used for generating the filename
     */
    private static downloadXml(xmlString: string, boardTitle: string): void {
        const blob = new Blob([xmlString], {type: 'application/xml'})

        const link = document.createElement('a')
        link.style.display = 'none'

        const filename = `${Utils.sanitizeFilename(boardTitle)}.xml`
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

    /**
     * Escapes XML special characters to prevent XML injection and ensure valid XML output.
     *
     * @param text - The text to escape
     * @returns The escaped text safe for XML content and attributes
     */
    private static escapeXml(text: string): string {
        if (text === null || text === undefined) {
            return ''
        }
        return String(text).
            replace(/&/g, '&amp;').
            replace(/</g, '&lt;').
            replace(/>/g, '&gt;').
            replace(/"/g, '&quot;').
            replace(/'/g, '&apos;')
    }
}

export {XmlExporter}
