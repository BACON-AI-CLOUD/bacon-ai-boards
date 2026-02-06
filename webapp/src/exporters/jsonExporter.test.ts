// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {JsonExporter, BoardJsonExport} from './jsonExporter'
import {TestBlockFactory} from '../test/testBlockFactory'
import {Board} from '../blocks/board'
import {BoardView} from '../blocks/boardView'
import {Card} from '../blocks/card'
import {Block} from '../blocks/block'
import {Utils} from '../utils'

// Mock document and URL APIs for download functionality
const mockLink = {
    href: '',
    download: '',
    style: {display: ''},
    click: jest.fn(),
}

const mockBlob = jest.fn()
const mockCreateObjectURL = jest.fn(() => 'blob:mock-url')
const mockRevokeObjectURL = jest.fn()
const mockCreateElement = jest.fn(() => mockLink)
const mockAppendChild = jest.fn()
const mockRemoveChild = jest.fn()

// Store original implementations
const originalBlob = global.Blob
const originalCreateObjectURL = URL.createObjectURL
const originalRevokeObjectURL = URL.revokeObjectURL

beforeAll(() => {
    // Mock Blob constructor
    global.Blob = mockBlob as unknown as typeof Blob
    mockBlob.mockImplementation((content: string[], options: BlobPropertyBag) => ({
        content,
        type: options?.type,
    }))

    // Mock URL methods
    URL.createObjectURL = mockCreateObjectURL
    URL.revokeObjectURL = mockRevokeObjectURL

    // Mock document methods
    document.createElement = mockCreateElement as unknown as typeof document.createElement
    document.body.appendChild = mockAppendChild
    document.body.removeChild = mockRemoveChild
})

afterAll(() => {
    // Restore original implementations
    global.Blob = originalBlob
    URL.createObjectURL = originalCreateObjectURL
    URL.revokeObjectURL = originalRevokeObjectURL
})

beforeEach(() => {
    jest.clearAllMocks()
    mockLink.href = ''
    mockLink.download = ''
    mockLink.style.display = ''
})

describe('JsonExporter', () => {
    describe('exportBoardJson', () => {
        // TC1: Export empty board (board with no cards)
        test('TC1: should export empty board with no cards', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-1'
            board.title = 'Empty Board'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            // Verify Blob was created with JSON content
            expect(mockBlob).toHaveBeenCalledTimes(1)
            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.version).toBe('1.0')
            expect(exportData.format).toBe('bacon-ai-boards-json')
            expect(exportData.board.id).toBe('board-1')
            expect(exportData.board.title).toBe('Empty Board')
            expect(exportData.views).toHaveLength(0)
            expect(exportData.cards).toHaveLength(0)
            expect(exportData.blocks).toHaveLength(0)

            // Verify download was triggered
            expect(mockLink.click).toHaveBeenCalledTimes(1)
        })

        // TC2: Export board with cards
        test('TC2: should export board with cards', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-2'
            board.title = 'Board With Cards'

            const card1 = TestBlockFactory.createCard(board)
            card1.id = 'card-1'
            card1.title = 'Card 1'

            const card2 = TestBlockFactory.createCard(board)
            card2.id = 'card-2'
            card2.title = 'Card 2'

            const views: BoardView[] = []
            const cards: Card[] = [card1, card2]
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.cards).toHaveLength(2)
            expect(exportData.cards[0].id).toBe('card-1')
            expect(exportData.cards[0].title).toBe('Card 1')
            expect(exportData.cards[1].id).toBe('card-2')
            expect(exportData.cards[1].title).toBe('Card 2')
        })

        // TC3: Export board with multiple views
        test('TC3: should export board with multiple views', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-3'
            board.title = 'Board With Views'

            const view1 = TestBlockFactory.createBoardView(board)
            view1.id = 'view-1'
            view1.title = 'Kanban View'
            view1.fields.viewType = 'board'

            const view2 = TestBlockFactory.createTableView(board)
            view2.id = 'view-2'
            view2.title = 'Table View'
            view2.fields.viewType = 'table'

            const views: BoardView[] = [view1, view2]
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.views).toHaveLength(2)
            expect(exportData.views[0].id).toBe('view-1')
            expect(exportData.views[0].title).toBe('Kanban View')
            expect(exportData.views[0].viewType).toBe('board')
            expect(exportData.views[1].id).toBe('view-2')
            expect(exportData.views[1].title).toBe('Table View')
            expect(exportData.views[1].viewType).toBe('table')
        })

        // TC4: Export board with all property types
        test('TC4: should export board with all property types', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-4'
            board.title = 'Board With Properties'
            board.cardProperties = [
                {
                    id: 'prop-select',
                    name: 'Select Property',
                    type: 'select',
                    options: [
                        {id: 'opt-1', value: 'Option 1', color: 'propColorRed'},
                        {id: 'opt-2', value: 'Option 2', color: 'propColorBlue'},
                    ],
                },
                {
                    id: 'prop-text',
                    name: 'Text Property',
                    type: 'text',
                    options: [],
                },
                {
                    id: 'prop-number',
                    name: 'Number Property',
                    type: 'number',
                    options: [],
                },
                {
                    id: 'prop-date',
                    name: 'Date Property',
                    type: 'date',
                    options: [],
                },
                {
                    id: 'prop-checkbox',
                    name: 'Checkbox Property',
                    type: 'checkbox',
                    options: [],
                },
            ]

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.board.cardProperties).toHaveLength(5)
            expect(exportData.board.cardProperties[0].type).toBe('select')
            expect(exportData.board.cardProperties[0].options).toHaveLength(2)
            expect(exportData.board.cardProperties[1].type).toBe('text')
            expect(exportData.board.cardProperties[2].type).toBe('number')
            expect(exportData.board.cardProperties[3].type).toBe('date')
            expect(exportData.board.cardProperties[4].type).toBe('checkbox')
        })

        // TC5: Verify JSON schema correctness (version, format fields)
        test('TC5: should include correct version and format fields', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-5'
            board.title = 'Schema Test Board'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.version).toBe('1.0')
            expect(exportData.format).toBe('bacon-ai-boards-json')
            expect(typeof exportData.exportDate).toBe('number')
            expect(exportData.exportDate).toBeGreaterThan(0)
        })

        // TC6: Verify board data is correctly mapped
        test('TC6: should correctly map board data', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-6'
            board.title = 'Mapped Board'
            board.description = 'Board description text'
            board.icon = 'board-icon'
            board.type = 'O'
            board.properties = {customProp: 'customValue'}

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.board.id).toBe('board-6')
            expect(exportData.board.title).toBe('Mapped Board')
            expect(exportData.board.description).toBe('Board description text')
            expect(exportData.board.icon).toBe('board-icon')
            expect(exportData.board.type).toBe('O')
            expect(exportData.board.properties).toEqual({customProp: 'customValue'})
        })

        // TC7: Verify view data is correctly mapped
        test('TC7: should correctly map view data', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-7'

            const view = TestBlockFactory.createBoardView(board)
            view.id = 'view-7'
            view.title = 'Test View'
            view.fields.viewType = 'board'
            view.fields.groupById = 'property1'
            view.fields.sortOptions = [
                {propertyId: 'prop1', reversed: false},
                {propertyId: 'prop2', reversed: true},
            ]
            view.fields.visiblePropertyIds = ['prop1', 'prop2', 'prop3']

            const views: BoardView[] = [view]
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.views[0].id).toBe('view-7')
            expect(exportData.views[0].title).toBe('Test View')
            expect(exportData.views[0].viewType).toBe('board')
            expect(exportData.views[0].groupById).toBe('property1')
            expect(exportData.views[0].sortOptions).toHaveLength(2)
            expect(exportData.views[0].visiblePropertyIds).toEqual(['prop1', 'prop2', 'prop3'])
        })

        // TC8: Verify card data is correctly mapped
        test('TC8: should correctly map card data', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-8'

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-8'
            card.title = 'Test Card'
            card.fields.icon = 'card-icon'
            card.fields.properties = {
                prop1: 'value1',
                prop2: ['value2a', 'value2b'],
            }
            card.fields.contentOrder = ['block1', 'block2']

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.cards[0].id).toBe('card-8')
            expect(exportData.cards[0].title).toBe('Test Card')
            expect(exportData.cards[0].icon).toBe('card-icon')
            expect(exportData.cards[0].properties).toEqual({
                prop1: 'value1',
                prop2: ['value2a', 'value2b'],
            })
            expect(exportData.cards[0].contentOrder).toEqual(['block1', 'block2'])
        })

        // TC9: Verify block data is correctly mapped
        test('TC9: should correctly map block data', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-9'

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-9'

            const textBlock = TestBlockFactory.createText(card)
            textBlock.id = 'text-block-1'
            textBlock.parentId = 'card-9'
            textBlock.title = 'Text content'

            const imageBlock = TestBlockFactory.createImage(card)
            imageBlock.id = 'image-block-1'
            imageBlock.parentId = 'card-9'

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = [textBlock, imageBlock]

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            expect(exportData.blocks).toHaveLength(2)
            expect(exportData.blocks[0].id).toBe('text-block-1')
            expect(exportData.blocks[0].parentId).toBe('card-9')
            expect(exportData.blocks[0].type).toBe('text')
            expect(exportData.blocks[0].title).toBe('Text content')
            expect(exportData.blocks[1].id).toBe('image-block-1')
            expect(exportData.blocks[1].type).toBe('image')
        })

        // Additional test: Verify download filename uses sanitized board title
        test('should generate download filename from board title', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-10'
            board.title = 'My Board Title'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            // Verify the download attribute was set correctly
            expect(mockLink.download).toBe(`${Utils.sanitizeFilename('My Board Title')}.json`)
        })

        // Additional test: Verify default title when board title is empty
        test('should use default filename when board title is empty', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-11'
            board.title = ''

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            expect(mockLink.download).toBe('board.json')
        })

        // Additional test: Verify Blob is created with correct MIME type
        test('should create Blob with application/json MIME type', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-12'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            expect(mockBlob).toHaveBeenCalledWith(
                expect.any(Array),
                {type: 'application/json'},
            )
        })

        // Additional test: Verify link element is properly styled and cleaned up
        test('should properly setup and cleanup download link', () => {
            jest.useFakeTimers()

            const board = TestBlockFactory.createBoard()
            board.id = 'board-13'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            JsonExporter.exportBoardJson(board, views, cards, blocks)

            // Verify link was created and configured
            expect(mockCreateElement).toHaveBeenCalledWith('a')
            expect(mockLink.style.display).toBe('none')
            expect(mockAppendChild).toHaveBeenCalledWith(mockLink)
            expect(mockLink.click).toHaveBeenCalled()
            expect(mockCreateObjectURL).toHaveBeenCalled()

            // Fast-forward cleanup timer
            jest.advanceTimersByTime(100)
            expect(mockRemoveChild).toHaveBeenCalledWith(mockLink)
            expect(mockRevokeObjectURL).toHaveBeenCalled()

            jest.useRealTimers()
        })

        // Additional test: Complete export with all data types
        test('should export complete board with views, cards, and blocks', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'complete-board'
            board.title = 'Complete Board'
            board.description = 'Full export test'
            board.icon = 'full-icon'

            const view = TestBlockFactory.createBoardView(board)
            view.id = 'complete-view'
            view.title = 'Complete View'

            const card = TestBlockFactory.createCard(board)
            card.id = 'complete-card'
            card.title = 'Complete Card'

            const textBlock = TestBlockFactory.createText(card)
            textBlock.id = 'complete-text'
            textBlock.title = 'Complete Text'

            const dividerBlock = TestBlockFactory.createDivider(card)
            dividerBlock.id = 'complete-divider'

            JsonExporter.exportBoardJson(board, [view], [card], [textBlock, dividerBlock])

            const blobContent = mockBlob.mock.calls[0][0][0]
            const exportData = JSON.parse(blobContent) as BoardJsonExport

            // Verify all data is present
            expect(exportData.board.id).toBe('complete-board')
            expect(exportData.views).toHaveLength(1)
            expect(exportData.cards).toHaveLength(1)
            expect(exportData.blocks).toHaveLength(2)

            // Verify JSON is pretty-printed (2 space indentation)
            expect(blobContent).toContain('\n')
            expect(blobContent).toContain('  ')
        })
    })
})
