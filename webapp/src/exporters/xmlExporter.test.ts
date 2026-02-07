// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {TestBlockFactory} from '../test/testBlockFactory'
import {BoardView} from '../blocks/boardView'
import {Card} from '../blocks/card'
import {Block} from '../blocks/block'
import {Utils} from '../utils'

import {XmlExporter} from './xmlExporter'

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

describe('XmlExporter', () => {
    describe('exportBoardXml', () => {
        // TC1: Export empty board with no cards
        test('TC1: should export empty board with no cards', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-1'
            board.title = 'Empty Board'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            // Verify Blob was created with XML content
            expect(mockBlob).toHaveBeenCalledTimes(1)
            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Verify XML structure
            expect(xmlContent).toContain('<?xml version="1.0" encoding="UTF-8"?>')
            expect(xmlContent).toContain('<bacon-ai-boards')
            expect(xmlContent).toContain('version="1.0"')
            expect(xmlContent).toContain('format="bacon-ai-boards-xml"')
            expect(xmlContent).toContain('<board id="board-1"')
            expect(xmlContent).toContain('title="Empty Board"')
            expect(xmlContent).toContain('<views>')
            expect(xmlContent).toContain('</views>')
            expect(xmlContent).toContain('<cards>')
            expect(xmlContent).toContain('</cards>')
            expect(xmlContent).toContain('<blocks>')
            expect(xmlContent).toContain('</blocks>')

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

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<card id="card-1" title="Card 1">')
            expect(xmlContent).toContain('<card id="card-2" title="Card 2">')
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

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<view id="view-1" title="Kanban View" viewType="board"')
            expect(xmlContent).toContain('<view id="view-2" title="Table View" viewType="table"')
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

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<cardProperties>')
            expect(xmlContent).toContain('<property id="prop-select" name="Select Property" type="select"')
            expect(xmlContent).toContain('<property id="prop-text" name="Text Property" type="text"')
            expect(xmlContent).toContain('<property id="prop-number" name="Number Property" type="number"')
            expect(xmlContent).toContain('<property id="prop-date" name="Date Property" type="date"')
            expect(xmlContent).toContain('<property id="prop-checkbox" name="Checkbox Property" type="checkbox"')
            expect(xmlContent).toContain('</cardProperties>')
        })

        // TC5: Verify XML declaration and root element
        test('TC5: should include correct XML declaration and root element', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-5'
            board.title = 'Schema Test Board'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Verify XML declaration
            expect(xmlContent.startsWith('<?xml version="1.0" encoding="UTF-8"?>')).toBe(true)

            // Verify root element attributes
            expect(xmlContent).toContain('<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="')
            expect(xmlContent).toContain('</bacon-ai-boards>')
        })

        // TC6: Verify board element attributes and children
        test('TC6: should correctly map board data with all attributes', () => {
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

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<board id="board-6"')
            expect(xmlContent).toContain('title="Mapped Board"')
            expect(xmlContent).toContain('description="Board description text"')
            expect(xmlContent).toContain('type="O"')
            expect(xmlContent).toContain('<icon>board-icon</icon>')
            expect(xmlContent).toContain('<properties>')
            expect(xmlContent).toContain('<property key="customProp">customValue</property>')
            expect(xmlContent).toContain('</properties>')
        })

        // TC7: Verify view elements are correctly mapped
        test('TC7: should correctly map view data with sortOptions and visiblePropertyIds', () => {
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

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<view id="view-7" title="Test View" viewType="board" groupById="property1">')
            expect(xmlContent).toContain('<sortOptions>')
            expect(xmlContent).toContain('<sort propertyId="prop1" reversed="false"')
            expect(xmlContent).toContain('<sort propertyId="prop2" reversed="true"')
            expect(xmlContent).toContain('</sortOptions>')
            expect(xmlContent).toContain('<visiblePropertyIds>')
            expect(xmlContent).toContain('<propertyId>prop1</propertyId>')
            expect(xmlContent).toContain('<propertyId>prop2</propertyId>')
            expect(xmlContent).toContain('<propertyId>prop3</propertyId>')
            expect(xmlContent).toContain('</visiblePropertyIds>')
        })

        // TC8: Verify card elements are correctly mapped
        test('TC8: should correctly map card data with properties and contentOrder', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-8'

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-8'
            card.title = 'Test Card'
            card.fields.icon = 'card-icon'
            card.fields.properties = {
                prop1: 'value1',
                prop2: 'value2',
            }
            card.fields.contentOrder = ['block1', 'block2']

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<card id="card-8" title="Test Card">')
            expect(xmlContent).toContain('<icon>card-icon</icon>')
            expect(xmlContent).toContain('<properties>')
            expect(xmlContent).toContain('<property key="prop1">value1</property>')
            expect(xmlContent).toContain('<property key="prop2">value2</property>')
            expect(xmlContent).toContain('</properties>')
            expect(xmlContent).toContain('<contentOrder>')
            expect(xmlContent).toContain('<contentId>block1</contentId>')
            expect(xmlContent).toContain('<contentId>block2</contentId>')
            expect(xmlContent).toContain('</contentOrder>')
        })

        // TC9: Verify block elements are correctly mapped
        test('TC9: should correctly map block data with fields', () => {
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

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<blocks>')
            expect(xmlContent).toContain('<block id="text-block-1" parentId="card-9" type="text" title="Text content">')
            expect(xmlContent).toContain('<block id="image-block-1" parentId="card-9" type="image"')
            expect(xmlContent).toContain('<fields>')
            expect(xmlContent).toContain('</fields>')
            expect(xmlContent).toContain('</block>')
            expect(xmlContent).toContain('</blocks>')
        })

        // TC10: Verify XML escaping for special characters
        test('TC10: should properly escape XML special characters (& < > " \')', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-10'
            board.title = 'Board with & ampersand'
            board.description = 'Description with <script>alert("xss")</script> tags'

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-10'
            card.title = "Card with 'quotes' and \"double quotes\""

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Verify ampersand is escaped
            expect(xmlContent).toContain('&amp;')

            // Verify less-than and greater-than are escaped
            expect(xmlContent).toContain('&lt;script&gt;')
            expect(xmlContent).toContain('&lt;/script&gt;')

            // Verify quotes are escaped
            expect(xmlContent).toContain('&quot;')
            expect(xmlContent).toContain('&apos;')
        })

        // TC11: Verify filename sanitization
        test('TC11: should sanitize filename for download', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-11'
            board.title = 'My Board/Title:With*Special?Chars'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            // Verify the download attribute was set with sanitized filename
            expect(mockLink.download).toBe(`${Utils.sanitizeFilename('My Board/Title:With*Special?Chars')}.xml`)
        })

        // TC12: Verify MIME type is application/xml
        test('TC12: should create Blob with application/xml MIME type', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-12'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            expect(mockBlob).toHaveBeenCalledWith(
                expect.any(Array),
                {type: 'application/xml'},
            )
        })

        // Additional test: Verify default title when board title is empty
        test('should use default filename when board title is empty', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-13'
            board.title = ''

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            expect(mockLink.download).toBe('board.xml')
        })

        // Additional test: Verify link element is properly styled and cleaned up
        test('should properly setup and cleanup download link', () => {
            jest.useFakeTimers()

            const board = TestBlockFactory.createBoard()
            board.id = 'board-14'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

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

            XmlExporter.exportBoardXml(board, [view], [card], [textBlock, dividerBlock])

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Verify all data is present
            expect(xmlContent).toContain('<board id="complete-board"')
            expect(xmlContent).toContain('<view id="complete-view"')
            expect(xmlContent).toContain('<card id="complete-card"')
            expect(xmlContent).toContain('<block id="complete-text"')
            expect(xmlContent).toContain('<block id="complete-divider"')

            // Verify XML is multiline formatted
            expect(xmlContent).toContain('\n')
        })

        // Additional test: Verify view without groupById
        test('should export view without groupById attribute when not set', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-15'

            const view = TestBlockFactory.createBoardView(board)
            view.id = 'view-15'
            view.title = 'View Without GroupBy'
            view.fields.groupById = undefined

            const views: BoardView[] = [view]
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Should not include groupById attribute when undefined
            expect(xmlContent).toContain('<view id="view-15" title="View Without GroupBy" viewType="board">')
            expect(xmlContent).not.toContain('groupById=""')
        })

        // Additional test: Verify card without icon
        test('should export card without icon element when not set', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-16'

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-16'
            card.title = 'Card Without Icon'
            card.fields.icon = undefined

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Should have card but no icon element inside
            expect(xmlContent).toContain('<card id="card-16" title="Card Without Icon">')

            // The card should not have an <icon> element
            const cardSection = xmlContent.substring(
                xmlContent.indexOf('<card id="card-16"'),
                xmlContent.indexOf('</card>', xmlContent.indexOf('<card id="card-16"')) + '</card>'.length,
            )
            expect(cardSection).not.toContain('<icon>')
        })

        // Additional test: Verify array properties are comma-separated
        test('should handle array property values correctly', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-17'
            board.properties = {
                arrayProp: ['value1', 'value2', 'value3'],
            }

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-17'
            card.fields.properties = {
                multiSelect: ['opt1', 'opt2'],
            }

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Array values should be comma-separated
            expect(xmlContent).toContain('<property key="arrayProp">value1,value2,value3</property>')
            expect(xmlContent).toContain('<property key="multiSelect">opt1,opt2</property>')
        })

        // Additional test: Verify nested contentOrder arrays
        test('should handle nested contentOrder arrays', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-18'

            const card = TestBlockFactory.createCard(board)
            card.id = 'card-18'
            card.fields.contentOrder = ['block1', ['block2', 'block3'], 'block4']

            const views: BoardView[] = []
            const cards: Card[] = [card]
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            expect(xmlContent).toContain('<contentId>block1</contentId>')
            expect(xmlContent).toContain('<contentId>block2,block3</contentId>')
            expect(xmlContent).toContain('<contentId>block4</contentId>')
        })

        // Additional test: Verify board without icon
        test('should export board without icon element when not set', () => {
            const board = TestBlockFactory.createBoard()
            board.id = 'board-19'
            board.title = 'Board Without Icon'
            board.icon = ''

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Should have board but no icon element inside
            expect(xmlContent).toContain('<board id="board-19"')

            // The board should not have an <icon> element when icon is empty
            const boardSection = xmlContent.substring(
                xmlContent.indexOf('<board'),
                xmlContent.indexOf('</board>') + '</board>'.length,
            )
            expect(boardSection).not.toContain('<icon>')
        })

        // Additional test: Verify exportDate is a timestamp
        test('should include valid exportDate timestamp', () => {
            const beforeExport = Date.now()

            const board = TestBlockFactory.createBoard()
            board.id = 'board-20'

            const views: BoardView[] = []
            const cards: Card[] = []
            const blocks: Block[] = []

            XmlExporter.exportBoardXml(board, views, cards, blocks)

            const afterExport = Date.now()

            const xmlContent = mockBlob.mock.calls[0][0][0]

            // Extract exportDate from XML
            const exportDateMatch = xmlContent.match(/exportDate="(\d+)"/)
            expect(exportDateMatch).not.toBeNull()

            const exportDate = parseInt(exportDateMatch![1], 10)
            expect(exportDate).toBeGreaterThanOrEqual(beforeExport)
            expect(exportDate).toBeLessThanOrEqual(afterExport)
        })
    })
})
