// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {JsonImporter, ImportResult} from './jsonImporter'
import {FetchMock} from '../test/fetchMock'
import {Utils} from '../utils'
import 'isomorphic-fetch'

// Mock the mutator module
jest.mock('../mutator', () => ({
    __esModule: true,
    default: {
        createBoardsAndBlocks: jest.fn(),
    },
}))

// Import mocked mutator
import mutator from '../mutator'

global.fetch = FetchMock.fn

// Spy on Utils.log and Utils.logError
let logSpy: jest.SpyInstance
let logErrorSpy: jest.SpyInstance

beforeAll(() => {
    logSpy = jest.spyOn(Utils, 'log').mockImplementation(() => {})
    logErrorSpy = jest.spyOn(Utils, 'logError').mockImplementation(() => {})
})

afterAll(() => {
    logSpy.mockRestore()
    logErrorSpy.mockRestore()
})

// Helper to create valid export data without using TestBlockFactory
function createValidExportData(overrides: Partial<Record<string, unknown>> = {}): Record<string, unknown> {
    return {
        version: '1.0',
        format: 'bacon-ai-boards-json',
        exportDate: Date.now(),
        board: {
            id: 'test-board-id',
            title: 'Test Board',
            description: 'Test description',
            icon: 'test-icon',
            type: 'O',
            cardProperties: [
                {
                    id: 'prop-1',
                    name: 'Status',
                    type: 'select',
                    options: [{id: 'opt-1', value: 'Done', color: 'propColorGreen'}],
                },
            ],
            properties: {},
        },
        views: [
            {
                id: 'test-view-id',
                boardId: 'test-board-id',
                title: 'Test View',
                type: 'view',
                fields: {
                    viewType: 'board',
                    groupById: 'prop-1',
                    sortOptions: [],
                    visiblePropertyIds: ['prop-1'],
                },
            },
        ],
        cards: [
            {
                id: 'test-card-id',
                boardId: 'test-board-id',
                title: 'Test Card',
                type: 'card',
                fields: {
                    icon: 'card-icon',
                    properties: {
                        'prop-1': 'opt-1',
                    },
                    contentOrder: ['test-block-id'],
                },
            },
        ],
        blocks: [
            {
                id: 'test-block-id',
                boardId: 'test-board-id',
                parentId: 'test-card-id',
                type: 'text',
                title: 'Test text content',
                fields: {},
            },
        ],
        ...overrides,
    }
}

// Remove unused createMockFile - file processing is tested via importBoardJson tests

describe('JsonImporter', () => {
    beforeEach(() => {
        jest.clearAllMocks()
        FetchMock.fn.mockReset()
    })

    describe('importFromString', () => {
        // TC10: Import valid JSON file (via importFromString)
        test('TC10: should import valid JSON successfully', async () => {
            const validData = createValidExportData()
            const jsonString = JSON.stringify(validData)

            const mockResult = {
                boards: [{id: 'new-board-id', title: 'Test Board'}],
                blocks: [{id: 'block-1'}, {id: 'block-2'}],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(true)
            expect(result.boardId).toBe('new-board-id')
            expect(result.boardsCreated).toBe(1)
            expect(result.blocksCreated).toBe(2)
        })

        // TC11: Reject invalid JSON format (parse error)
        test('TC11: should reject invalid JSON format', async () => {
            const invalidJson = '{not valid json'

            const result = await JsonImporter.importFromString(invalidJson)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to parse JSON')
        })

        // TC12: Reject invalid version
        test('TC12: should reject invalid version', async () => {
            const invalidVersionData = createValidExportData({version: '2.0'})
            const jsonString = JSON.stringify(invalidVersionData)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Unsupported version')
            expect(result.error).toContain('2.0')
        })

        // TC13: Reject invalid format field
        test('TC13: should reject invalid format field', async () => {
            const invalidFormatData = createValidExportData({format: 'wrong-format'})
            const jsonString = JSON.stringify(invalidFormatData)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Invalid format')
            expect(result.error).toContain('wrong-format')
        })

        // TC14: Reject missing board data
        test('TC14: should reject missing board data', async () => {
            const noBoardData = createValidExportData()
            delete noBoardData.board
            const jsonString = JSON.stringify(noBoardData)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid board data')
        })

        // TC15: Reject missing required board fields (id, title)
        test('TC15a: should reject board missing id field', async () => {
            const noIdBoard = createValidExportData()
            const board = noIdBoard.board as Record<string, unknown>
            delete board.id
            const jsonString = JSON.stringify(noIdBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: id')
        })

        test('TC15b: should reject board missing title field', async () => {
            const noTitleBoard = createValidExportData()
            const board = noTitleBoard.board as Record<string, unknown>
            delete board.title
            const jsonString = JSON.stringify(noTitleBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: title')
        })

        test('TC15c: should reject board missing description field', async () => {
            const noDescBoard = createValidExportData()
            const board = noDescBoard.board as Record<string, unknown>
            delete board.description
            const jsonString = JSON.stringify(noDescBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: description')
        })

        test('TC15d: should reject board missing type field', async () => {
            const noTypeBoard = createValidExportData()
            const board = noTypeBoard.board as Record<string, unknown>
            delete board.type
            const jsonString = JSON.stringify(noTypeBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: type')
        })

        test('TC15e: should reject board missing cardProperties field', async () => {
            const noCardPropsBoard = createValidExportData()
            const board = noCardPropsBoard.board as Record<string, unknown>
            delete board.cardProperties
            const jsonString = JSON.stringify(noCardPropsBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: cardProperties')
        })

        test('TC15f: should reject board missing properties field', async () => {
            const noPropsBoard = createValidExportData()
            const board = noPropsBoard.board as Record<string, unknown>
            delete board.properties
            const jsonString = JSON.stringify(noPropsBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: properties')
        })

        // TC16: Reject missing views array
        test('TC16: should reject missing views array', async () => {
            const noViewsData = createValidExportData()
            delete noViewsData.views
            const jsonString = JSON.stringify(noViewsData)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid views array')
        })

        // TC17: Reject missing cards array
        test('TC17: should reject missing cards array', async () => {
            const noCardsData = createValidExportData()
            delete noCardsData.cards
            const jsonString = JSON.stringify(noCardsData)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid cards array')
        })

        // TC18: Reject missing blocks array
        test('TC18: should reject missing blocks array', async () => {
            const noBlocksData = createValidExportData()
            delete noBlocksData.blocks
            const jsonString = JSON.stringify(noBlocksData)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid blocks array')
        })

        // TC19: Validate importFromString method works
        test('TC19: should successfully use importFromString method', async () => {
            const validData = createValidExportData()
            const jsonString = JSON.stringify(validData)

            const mockResult = {
                boards: [{id: 'imported-board-id', title: 'Test Board'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(true)
            expect(result.boardId).toBe('imported-board-id')
            expect(mutator.createBoardsAndBlocks).toHaveBeenCalledTimes(1)
        })

        // Additional validation tests
        test('should reject null data', async () => {
            const result = await JsonImporter.importFromString('null')

            expect(result.success).toBe(false)
            expect(result.error).toContain('Invalid data')
        })

        test('should reject non-object data', async () => {
            const result = await JsonImporter.importFromString('"string"')

            expect(result.success).toBe(false)
            expect(result.error).toContain('Invalid data')
        })

        test('should reject array data', async () => {
            const result = await JsonImporter.importFromString('[]')

            expect(result.success).toBe(false)
            // Arrays are objects in JS, but don't have the required fields
            expect(result.success).toBe(false)
        })

        test('should reject missing exportDate', async () => {
            const noExportDate = createValidExportData()
            delete noExportDate.exportDate
            const jsonString = JSON.stringify(noExportDate)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid exportDate')
        })

        test('should reject non-numeric exportDate', async () => {
            const invalidExportDate = createValidExportData({exportDate: 'not-a-number'})
            const jsonString = JSON.stringify(invalidExportDate)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid exportDate')
        })

        test('should reject board as non-object', async () => {
            const invalidBoard = createValidExportData({board: 'not-an-object'})
            const jsonString = JSON.stringify(invalidBoard)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid board data')
        })

        test('should reject cardProperties as non-array', async () => {
            const data = createValidExportData()
            const board = data.board as Record<string, unknown>
            board.cardProperties = 'not-an-array'
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('cardProperties (must be an array)')
        })

        test('should reject properties as non-object', async () => {
            const data = createValidExportData()
            const board = data.board as Record<string, unknown>
            board.properties = 'not-an-object'
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required field: properties')
        })

        test('should reject views as non-array', async () => {
            const invalidViews = createValidExportData({views: 'not-an-array'})
            const jsonString = JSON.stringify(invalidViews)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid views array')
        })

        test('should reject cards as non-array', async () => {
            const invalidCards = createValidExportData({cards: 'not-an-array'})
            const jsonString = JSON.stringify(invalidCards)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid cards array')
        })

        test('should reject blocks as non-array', async () => {
            const invalidBlocks = createValidExportData({blocks: 'not-an-array'})
            const jsonString = JSON.stringify(invalidBlocks)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing or invalid blocks array')
        })

        // View validation tests
        test('should reject view missing id field', async () => {
            const data = createValidExportData()
            data.views = [{boardId: 'board-id', title: 'View'}] as unknown[]
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('View at index 0 is missing required fields')
        })

        test('should reject view missing boardId field', async () => {
            const data = createValidExportData()
            data.views = [{id: 'view-id', title: 'View'}] as unknown[]
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('View at index 0 is missing required fields')
        })

        // Card validation tests
        test('should reject card missing id field', async () => {
            const data = createValidExportData()
            data.cards = [{boardId: 'board-id', title: 'Card'}] as unknown[]
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Card at index 0 is missing required fields')
        })

        test('should reject card missing boardId field', async () => {
            const data = createValidExportData()
            data.cards = [{id: 'card-id', title: 'Card'}] as unknown[]
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Card at index 0 is missing required fields')
        })

        // Block validation tests
        test('should reject block missing id field', async () => {
            const data = createValidExportData()
            data.blocks = [{boardId: 'board-id', parentId: 'card-id', type: 'text'}] as unknown[]
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Block at index 0 is missing required fields')
        })

        test('should reject block missing boardId field', async () => {
            const data = createValidExportData()
            data.blocks = [{id: 'block-id', parentId: 'card-id', type: 'text'}] as unknown[]
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Block at index 0 is missing required fields')
        })

        // Error handling tests
        test('should handle mutator API error', async () => {
            const validData = createValidExportData()
            const jsonString = JSON.stringify(validData)

            ;(mutator.createBoardsAndBlocks as jest.Mock).mockRejectedValue(new Error('API Error'))

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to import board')
            expect(result.error).toContain('API Error')
        })

        test('should handle mutator returning null', async () => {
            const validData = createValidExportData()
            const jsonString = JSON.stringify(validData)

            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(null)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to create board')
        })

        test('should handle mutator returning empty boards array', async () => {
            const validData = createValidExportData()
            const jsonString = JSON.stringify(validData)

            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue({boards: [], blocks: []})

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to create board')
        })

        // Empty arrays validation (should succeed)
        test('should accept empty views array', async () => {
            const data = createValidExportData({views: []})
            const jsonString = JSON.stringify(data)

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(true)
        })

        test('should accept empty cards array', async () => {
            const data = createValidExportData({cards: []})
            const jsonString = JSON.stringify(data)

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(true)
        })

        test('should accept empty blocks array', async () => {
            const data = createValidExportData({blocks: []})
            const jsonString = JSON.stringify(data)

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(true)
        })

        // Multiple items validation
        test('should validate all views in array', async () => {
            const data = createValidExportData()
            const validView = (data.views as unknown[])[0]
            data.views = [validView, {id: 'view-2'}] // Second view missing boardId
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('View at index 1 is missing required fields')
        })

        test('should validate all cards in array', async () => {
            const data = createValidExportData()
            const validCard = (data.cards as unknown[])[0]
            data.cards = [validCard, {boardId: 'board-id'}] // Second card missing id
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Card at index 1 is missing required fields')
        })

        test('should validate all blocks in array', async () => {
            const data = createValidExportData()
            const validBlock = (data.blocks as unknown[])[0]
            data.blocks = [validBlock, {id: 'block-2'}] // Second block missing boardId
            const jsonString = JSON.stringify(data)

            const result = await JsonImporter.importFromString(jsonString)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Block at index 1 is missing required fields')
        })
    })

    describe('importBoardJson (file picker)', () => {
        // Mock document.createElement for input element
        let mockInput: {
            type: string
            accept: string
            style: {display: string}
            onchange: (() => void) | null
            files: FileList | null
            click: jest.Mock
            parentNode: {removeChild: jest.Mock} | null
        }

        const mockAppendChild = jest.fn()
        const mockRemoveChild = jest.fn()

        beforeEach(() => {
            mockInput = {
                type: '',
                accept: '',
                style: {display: ''},
                onchange: null,
                files: null,
                click: jest.fn(),
                parentNode: {removeChild: mockRemoveChild},
            }

            jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
                if (tag === 'input') {
                    return mockInput as unknown as HTMLInputElement
                }
                return document.createElement.bind(document)(tag)
            })

            jest.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild)
        })

        afterEach(() => {
            jest.restoreAllMocks()
        })

        test('should create file input with correct attributes', () => {
            JsonImporter.importBoardJson()

            expect(mockInput.type).toBe('file')
            expect(mockInput.accept).toBe('.json')
            expect(mockInput.style.display).toBe('none')
            expect(mockAppendChild).toHaveBeenCalledWith(mockInput)
            expect(mockInput.click).toHaveBeenCalled()
        })

        test('should call onComplete with error when no file selected', async () => {
            const onComplete = jest.fn()
            JsonImporter.importBoardJson(onComplete)

            // Simulate no file selected
            mockInput.files = null
            mockInput.onchange?.()

            // Wait for async operations
            await new Promise((resolve) => setTimeout(resolve, 0))

            expect(onComplete).toHaveBeenCalledWith({
                success: false,
                error: 'No file selected',
            })
        })

        test('should cleanup input element after timeout', () => {
            jest.useFakeTimers()

            JsonImporter.importBoardJson()

            expect(mockRemoveChild).not.toHaveBeenCalled()

            jest.advanceTimersByTime(1000)

            expect(mockRemoveChild).toHaveBeenCalledWith(mockInput)

            jest.useRealTimers()
        })

        test('should not throw when parentNode is null during cleanup', () => {
            jest.useFakeTimers()

            JsonImporter.importBoardJson()

            // Set parentNode to null before cleanup
            mockInput.parentNode = null

            expect(() => {
                jest.advanceTimersByTime(1000)
            }).not.toThrow()

            jest.useRealTimers()
        })
    })
})
