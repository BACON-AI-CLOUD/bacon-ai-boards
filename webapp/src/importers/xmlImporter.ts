// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {Board, BoardsAndBlocks, IPropertyOption, IPropertyTemplate, MemberRole} from '../blocks/board'
import {BoardView} from '../blocks/boardView'
import {Card} from '../blocks/card'
import {Block} from '../blocks/block'
import {FilterGroup, createFilterGroup} from '../blocks/filterGroup'
import {Utils} from '../utils'
import mutator from '../mutator'

/**
 * Result interface for XML import operations
 */
interface ImportResult {
    success: boolean
    boardId?: string
    error?: string
    boardsCreated?: number
    blocksCreated?: number
}

/**
 * XML Importer for BACON-AI-BOARDS
 * Imports board data from XML files following the bacon-ai-boards-xml schema
 */
class XmlImporter {
    /**
     * Opens a file picker dialog and imports board data from a selected XML file
     * @param onComplete Callback function called when import completes
     */
    static importBoardXml(onComplete?: (result: ImportResult) => void): void {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.xml'
        input.onchange = async () => {
            const file = input.files && input.files[0]
            if (file) {
                const result = await XmlImporter.processXmlFile(file)
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
     * Processes an XML file and imports the board data
     * @param file The XML file to process
     * @returns ImportResult with success status and details
     */
    private static async processXmlFile(file: File): Promise<ImportResult> {
        try {
            const doc = await XmlImporter.parseXmlFile(file)

            const validationResult = XmlImporter.validateSchema(doc)
            if (!validationResult.valid) {
                return {
                    success: false,
                    error: validationResult.error,
                }
            }

            const boardsAndBlocks = XmlImporter.xmlToBoard(doc)
            return await XmlImporter.importBoardData(boardsAndBlocks)
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            Utils.logError(`XmlImporter: Error processing file: ${errorMessage}`)
            return {
                success: false,
                error: `Failed to process file: ${errorMessage}`,
            }
        }
    }

    /**
     * Parses an XML file and returns the parsed Document
     * @param file The file to parse
     * @returns Parsed XML Document
     */
    private static async parseXmlFile(file: File): Promise<Document> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = (event) => {
                try {
                    const content = event.target?.result as string
                    const parser = new DOMParser()
                    const doc = parser.parseFromString(content, 'application/xml')

                    // Check for parse errors
                    const parseError = doc.querySelector('parsererror')
                    if (parseError) {
                        reject(new Error('Invalid XML format'))
                        return
                    }

                    resolve(doc)
                } catch (error) {
                    reject(new Error('Failed to parse XML'))
                }
            }
            reader.onerror = () => {
                reject(new Error('Failed to read file'))
            }
            reader.readAsText(file)
        })
    }

    /**
     * Validates that the XML document matches the expected bacon-ai-boards-xml schema
     * @param doc The parsed XML document to validate
     * @returns Validation result with valid flag and optional error message
     */
    private static validateSchema(doc: Document): {valid: boolean, error?: string} {
        const root = doc.documentElement

        // Validate root element
        if (root.tagName !== 'bacon-ai-boards') {
            return {valid: false, error: `Invalid root element: ${root.tagName}. Expected bacon-ai-boards`}
        }

        // Validate version
        const version = root.getAttribute('version')
        if (version !== '1.0') {
            return {valid: false, error: `Unsupported version: ${version}. Expected version 1.0`}
        }

        // Validate format
        const format = root.getAttribute('format')
        if (format !== 'bacon-ai-boards-xml') {
            return {valid: false, error: `Invalid format: ${format}. Expected bacon-ai-boards-xml`}
        }

        // Validate required elements exist
        const board = root.querySelector('board')
        if (!board) {
            return {valid: false, error: 'Missing required element: board'}
        }

        const views = root.querySelector('views')
        if (!views) {
            return {valid: false, error: 'Missing required element: views'}
        }

        const cards = root.querySelector('cards')
        if (!cards) {
            return {valid: false, error: 'Missing required element: cards'}
        }

        const blocks = root.querySelector('blocks')
        if (!blocks) {
            return {valid: false, error: 'Missing required element: blocks'}
        }

        // Validate board has required attributes
        const boardId = board.getAttribute('id')
        if (!boardId) {
            return {valid: false, error: 'Board is missing required attribute: id'}
        }

        const boardTitle = board.querySelector('title')
        if (!boardTitle) {
            return {valid: false, error: 'Board is missing required element: title'}
        }

        return {valid: true}
    }

    /**
     * Converts an XML Document to BoardsAndBlocks structure
     * @param doc The validated XML document
     * @returns BoardsAndBlocks structure ready for import
     */
    private static xmlToBoard(doc: Document): BoardsAndBlocks {
        const root = doc.documentElement
        const boardElement = root.querySelector('board')!

        // Parse board
        const board = XmlImporter.parseBoard(boardElement)

        // Parse views
        const viewsElement = root.querySelector('views')!
        const views = XmlImporter.parseViews(viewsElement, board.id)

        // Parse cards
        const cardsElement = root.querySelector('cards')!
        const cards = XmlImporter.parseCards(cardsElement, board.id)

        // Parse other blocks
        const blocksElement = root.querySelector('blocks')!
        const blocks = XmlImporter.parseBlocks(blocksElement, board.id)

        // Combine all blocks
        const allBlocks: Block[] = [
            ...views as Block[],
            ...cards as Block[],
            ...blocks,
        ]

        return {
            boards: [board],
            blocks: allBlocks,
        }
    }

    /**
     * Parses the board element from XML
     * @param boardElement The board XML element
     * @returns Board object
     */
    private static parseBoard(boardElement: Element): Board {
        const id = boardElement.getAttribute('id') || ''
        const title = XmlImporter.getElementText(boardElement, 'title')
        const description = XmlImporter.getElementText(boardElement, 'description')
        const icon = XmlImporter.getElementText(boardElement, 'icon') || undefined
        const type = (XmlImporter.getElementText(boardElement, 'type') || 'P') as 'O' | 'P'

        // Parse card properties
        const cardPropertiesElement = boardElement.querySelector('cardProperties')
        let cardProperties: IPropertyTemplate[] = []
        if (cardPropertiesElement) {
            cardProperties = XmlImporter.parseCardProperties(cardPropertiesElement)
        }

        // Parse properties
        const propertiesElement = boardElement.querySelector('properties')
        let properties: Record<string, string | string[]> = {}
        if (propertiesElement) {
            properties = XmlImporter.parseRecordProperties(propertiesElement)
        }

        return {
            id,
            teamId: '', // Will be set by the server based on context
            createdBy: '',
            modifiedBy: '',
            type,
            minimumRole: MemberRole.None,
            title,
            description,
            icon,
            showDescription: false,
            isTemplate: false,
            templateVersion: 0,
            properties,
            cardProperties,
            createAt: Date.now(),
            updateAt: Date.now(),
            deleteAt: 0,
        }
    }

    /**
     * Parses card properties from XML
     * @param element The cardProperties XML element
     * @returns Array of IPropertyTemplate
     */
    private static parseCardProperties(element: Element): IPropertyTemplate[] {
        const properties: IPropertyTemplate[] = []
        const propertyElements = element.querySelectorAll(':scope > property')

        propertyElements.forEach((propElement) => {
            const id = propElement.getAttribute('id') || ''
            const name = XmlImporter.getElementText(propElement, 'name')
            const propType = XmlImporter.getElementText(propElement, 'type') || 'text'

            // Parse options
            const optionsElement = propElement.querySelector('options')
            const options: IPropertyOption[] = []
            if (optionsElement) {
                const optionElements = optionsElement.querySelectorAll(':scope > option')
                optionElements.forEach((optElement) => {
                    options.push({
                        id: optElement.getAttribute('id') || '',
                        value: XmlImporter.unescapeXml(optElement.getAttribute('value') || ''),
                        color: optElement.getAttribute('color') || '',
                    })
                })
            }

            properties.push({
                id,
                name,
                type: propType as IPropertyTemplate['type'],
                options,
            })
        })

        return properties
    }

    /**
     * Parses record properties (key-value pairs) from XML
     * @param element The properties XML element
     * @returns Record of property key-value pairs
     */
    private static parseRecordProperties(element: Element): Record<string, string | string[]> {
        const properties: Record<string, string | string[]> = {}
        const propElements = element.querySelectorAll(':scope > property')

        propElements.forEach((propElement) => {
            const key = propElement.getAttribute('key') || ''
            const isArray = propElement.getAttribute('type') === 'array'

            if (isArray) {
                const values: string[] = []
                const valueElements = propElement.querySelectorAll(':scope > value')
                valueElements.forEach((valueElement) => {
                    values.push(XmlImporter.unescapeXml(valueElement.textContent || ''))
                })
                properties[key] = values
            } else {
                properties[key] = XmlImporter.unescapeXml(propElement.textContent || '')
            }
        })

        return properties
    }

    /**
     * Parses views from XML
     * @param viewsElement The views XML element
     * @param boardId The board ID to associate with views
     * @returns Array of BoardView objects
     */
    private static parseViews(viewsElement: Element, boardId: string): BoardView[] {
        const views: BoardView[] = []
        const viewElements = viewsElement.querySelectorAll(':scope > view')

        viewElements.forEach((viewElement) => {
            const id = viewElement.getAttribute('id') || ''
            const title = XmlImporter.getElementText(viewElement, 'title')
            const viewType = XmlImporter.getElementText(viewElement, 'viewType') || 'board'
            const groupById = XmlImporter.getElementText(viewElement, 'groupById') || undefined
            const parentId = viewElement.getAttribute('parentId') || boardId

            // Parse sortOptions
            const sortOptions: Array<{propertyId: string, reversed: boolean}> = []
            const sortOptionsElement = viewElement.querySelector('sortOptions')
            if (sortOptionsElement) {
                const sortElements = sortOptionsElement.querySelectorAll(':scope > sort')
                sortElements.forEach((sortElement) => {
                    sortOptions.push({
                        propertyId: sortElement.getAttribute('propertyId') || '',
                        reversed: sortElement.getAttribute('reversed') === 'true',
                    })
                })
            }

            // Parse visiblePropertyIds
            const visiblePropertyIds: string[] = []
            const visiblePropsElement = viewElement.querySelector('visiblePropertyIds')
            if (visiblePropsElement) {
                const idElements = visiblePropsElement.querySelectorAll(':scope > id')
                idElements.forEach((idElement) => {
                    visiblePropertyIds.push(idElement.textContent || '')
                })
            }

            // Parse filter if present
            const filterElement = viewElement.querySelector('filter')
            const filter = filterElement ? XmlImporter.parseFilter(filterElement) : createFilterGroup()

            views.push({
                id,
                boardId,
                parentId,
                createdBy: '',
                modifiedBy: '',
                schema: 1,
                type: 'view',
                title,
                fields: {
                    viewType: viewType as 'board' | 'table' | 'gallery' | 'calendar',
                    groupById,
                    sortOptions,
                    visiblePropertyIds,
                    visibleOptionIds: [],
                    hiddenOptionIds: [],
                    collapsedOptionIds: [],
                    filter,
                    cardOrder: [],
                    columnWidths: {},
                    columnCalculations: {},
                    kanbanCalculations: {},
                    defaultTemplateId: '',
                },
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
            })
        })

        return views
    }

    /**
     * Parses a filter element from XML
     * @param filterElement The filter XML element
     * @returns FilterGroup object
     */
    private static parseFilter(filterElement: Element): FilterGroup {
        const operation = (filterElement.getAttribute('operation') || 'and') as 'and' | 'or'

        // For simplicity, we use createFilterGroup to return a properly typed empty filter
        // A complete implementation would recursively parse filter conditions
        return createFilterGroup({operation, filters: []})
    }

    /**
     * Parses cards from XML
     * @param cardsElement The cards XML element
     * @param boardId The board ID to associate with cards
     * @returns Array of Card objects
     */
    private static parseCards(cardsElement: Element, boardId: string): Card[] {
        const cards: Card[] = []
        const cardElements = cardsElement.querySelectorAll(':scope > card')

        cardElements.forEach((cardElement) => {
            const id = cardElement.getAttribute('id') || ''
            const title = XmlImporter.getElementText(cardElement, 'title')
            const icon = XmlImporter.getElementText(cardElement, 'icon') || undefined
            const parentId = cardElement.getAttribute('parentId') || boardId

            // Parse properties
            const propertiesElement = cardElement.querySelector('properties')
            let properties: Record<string, string | string[]> = {}
            if (propertiesElement) {
                properties = XmlImporter.parseRecordProperties(propertiesElement)
            }

            // Parse contentOrder
            const contentOrder: Array<string | string[]> = []
            const contentOrderElement = cardElement.querySelector('contentOrder')
            if (contentOrderElement) {
                const orderElements = contentOrderElement.querySelectorAll(':scope > item')
                orderElements.forEach((orderElement) => {
                    const isGroup = orderElement.getAttribute('type') === 'group'
                    if (isGroup) {
                        const groupIds: string[] = []
                        const idElements = orderElement.querySelectorAll(':scope > id')
                        idElements.forEach((idElement) => {
                            groupIds.push(idElement.textContent || '')
                        })
                        contentOrder.push(groupIds)
                    } else {
                        contentOrder.push(orderElement.textContent || '')
                    }
                })
            }

            cards.push({
                id,
                boardId,
                parentId,
                createdBy: '',
                modifiedBy: '',
                schema: 1,
                type: 'card',
                title,
                fields: {
                    icon,
                    properties,
                    contentOrder,
                    isTemplate: false,
                },
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
            })
        })

        return cards
    }

    /**
     * Parses content blocks from XML
     * @param blocksElement The blocks XML element
     * @param boardId The board ID to associate with blocks
     * @returns Array of Block objects
     */
    private static parseBlocks(blocksElement: Element, boardId: string): Block[] {
        const blocks: Block[] = []
        const blockElements = blocksElement.querySelectorAll(':scope > block')

        blockElements.forEach((blockElement) => {
            const id = blockElement.getAttribute('id') || ''
            const parentId = blockElement.getAttribute('parentId') || ''
            const blockType = blockElement.getAttribute('type') || 'unknown'
            const title = XmlImporter.getElementText(blockElement, 'title')

            // Parse fields
            const fieldsElement = blockElement.querySelector('fields')
            const fields: Record<string, unknown> = {}
            if (fieldsElement) {
                const fieldElements = fieldsElement.querySelectorAll(':scope > field')
                fieldElements.forEach((fieldElement) => {
                    const key = fieldElement.getAttribute('key') || ''
                    const fieldType = fieldElement.getAttribute('type')

                    if (fieldType === 'number') {
                        fields[key] = parseFloat(fieldElement.textContent || '0')
                    } else if (fieldType === 'boolean') {
                        fields[key] = fieldElement.textContent === 'true'
                    } else if (fieldType === 'array') {
                        const values: string[] = []
                        const valueElements = fieldElement.querySelectorAll(':scope > value')
                        valueElements.forEach((valueElement) => {
                            values.push(XmlImporter.unescapeXml(valueElement.textContent || ''))
                        })
                        fields[key] = values
                    } else if (fieldType === 'object') {
                        try {
                            fields[key] = JSON.parse(fieldElement.textContent || '{}')
                        } catch {
                            fields[key] = {}
                        }
                    } else {
                        fields[key] = XmlImporter.unescapeXml(fieldElement.textContent || '')
                    }
                })
            }

            blocks.push({
                id,
                boardId,
                parentId,
                createdBy: '',
                modifiedBy: '',
                schema: 1,
                type: blockType as Block['type'],
                title,
                fields,
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
            })
        })

        return blocks
    }

    /**
     * Helper to get text content of a child element
     * @param parent The parent element
     * @param tagName The child element tag name
     * @returns The text content or empty string
     */
    private static getElementText(parent: Element, tagName: string): string {
        const element = parent.querySelector(`:scope > ${tagName}`)
        return XmlImporter.unescapeXml(element?.textContent || '')
    }

    /**
     * Unescapes XML special characters
     * @param text The text to unescape
     * @returns Unescaped text
     */
    private static unescapeXml(text: string): string {
        return text.
            replace(/&lt;/g, '<').
            replace(/&gt;/g, '>').
            replace(/&quot;/g, '"').
            replace(/&apos;/g, "'").
            replace(/&amp;/g, '&')
    }

    /**
     * Imports the board data using the mutator API
     * @param boardsAndBlocks The BoardsAndBlocks structure to import
     * @returns ImportResult with success status and created board ID
     */
    private static async importBoardData(boardsAndBlocks: BoardsAndBlocks): Promise<ImportResult> {
        try {
            const board = boardsAndBlocks.boards[0]
            Utils.log(`XmlImporter: Importing board "${board.title}" with ${boardsAndBlocks.blocks.length} blocks`)

            // Use mutator to create the board and blocks
            const result = await mutator.createBoardsAndBlocks(
                boardsAndBlocks,
                'import board from XML',
            )

            if (result && result.boards && result.boards.length > 0) {
                Utils.log(`XmlImporter: Successfully imported board with ID ${result.boards[0].id}`)
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
            Utils.logError(`XmlImporter: Error importing board data: ${errorMessage}`)
            return {
                success: false,
                error: `Failed to import board: ${errorMessage}`,
            }
        }
    }

    /**
     * Imports board data from an XML string (useful for programmatic imports)
     * @param xmlString The XML string to import
     * @returns ImportResult with success status and details
     */
    static async importFromString(xmlString: string): Promise<ImportResult> {
        try {
            const parser = new DOMParser()
            const doc = parser.parseFromString(xmlString, 'application/xml')

            // Check for parse errors
            const parseError = doc.querySelector('parsererror')
            if (parseError) {
                return {
                    success: false,
                    error: 'Invalid XML format',
                }
            }

            const validationResult = XmlImporter.validateSchema(doc)
            if (!validationResult.valid) {
                return {
                    success: false,
                    error: validationResult.error,
                }
            }

            const boardsAndBlocks = XmlImporter.xmlToBoard(doc)
            return await XmlImporter.importBoardData(boardsAndBlocks)
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            return {
                success: false,
                error: `Failed to parse XML: ${errorMessage}`,
            }
        }
    }
}

export {XmlImporter, ImportResult}
