// SIT1 Round-Trip Test: XML Export -> Import Verification
// This integration test verifies that data exported to XML can be imported back correctly

import {TestBlockFactory} from './test/testBlockFactory'
import {XmlExporter} from './exporters/xmlExporter'
import {BoardView} from './blocks/boardView'
import {Card} from './blocks/card'
import {Block} from './blocks/block'

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

describe('SIT1: XML Round-Trip Test', () => {
    test('SIT1-001: should export board to valid XML and parse it back with identical data structure', () => {
        // Create test board with special characters
        const board = TestBlockFactory.createBoard()
        board.id = 'sit1-board-001'
        board.title = 'SIT1 Test Board with <special> & "chars"'
        board.description = "Board description with 'apostrophes'"
        board.icon = '🧪'

        // Add card properties
        board.cardProperties = [
            {
                id: 'prop-status',
                name: 'Status',
                type: 'select',
                options: [
                    {id: 'opt-todo', value: 'To Do', color: 'propColorRed'},
                    {id: 'opt-done', value: 'Done', color: 'propColorGreen'},
                ],
            },
        ]

        // Create views
        const view = TestBlockFactory.createBoardView(board)
        view.id = 'view-001'
        view.title = 'Table View'
        view.fields.viewType = 'table'
        view.fields.groupById = 'prop-status'
        const views: BoardView[] = [view]

        // Create cards with special characters
        const card1 = TestBlockFactory.createCard(board)
        card1.id = 'card-001'
        card1.title = 'Card with <HTML> & "quotes"'
        card1.fields.icon = '📝'
        card1.fields.properties = {'prop-status': 'opt-todo'}

        const card2 = TestBlockFactory.createCard(board)
        card2.id = 'card-002'
        card2.title = "Card with 'apostrophes'"
        card2.fields.icon = '✅'
        card2.fields.properties = {'prop-status': 'opt-done'}

        const cards: Card[] = [card1, card2]

        // Create content blocks
        const block1 = TestBlockFactory.createText(card1)
        block1.id = 'block-001'
        block1.title = 'Content <with> special & chars'
        const blocks: Block[] = [block1]

        // Step 1: Export to XML
        XmlExporter.exportBoardXml(board, views, cards, blocks)

        // Verify Blob was created
        expect(mockBlob).toHaveBeenCalledTimes(1)
        const xmlContent = mockBlob.mock.calls[0][0][0]

        // Step 2: Verify XML structure
        expect(xmlContent).toContain('<?xml version="1.0" encoding="UTF-8"?>')
        expect(xmlContent).toContain('<bacon-ai-boards')
        expect(xmlContent).toContain('version="1.0"')
        expect(xmlContent).toContain('format="bacon-ai-boards-xml"')
        expect(xmlContent).toContain('</bacon-ai-boards>')

        // Step 3: Parse XML back using DOMParser
        const parser = new DOMParser()
        const doc = parser.parseFromString(xmlContent, 'text/xml')

        // Verify no parsing errors
        const parseErrors = doc.getElementsByTagName('parsererror')
        expect(parseErrors.length).toBe(0)

        // Step 4: Validate board data
        const boardEl = doc.getElementsByTagName('board')[0]
        expect(boardEl).toBeDefined()
        expect(boardEl.getAttribute('id')).toBe('sit1-board-001')
        expect(boardEl.getAttribute('title')).toBe('SIT1 Test Board with <special> & "chars"')

        // Step 5: Validate views
        const viewEls = doc.getElementsByTagName('view')
        expect(viewEls.length).toBe(1)
        expect(viewEls[0].getAttribute('id')).toBe('view-001')
        expect(viewEls[0].getAttribute('title')).toBe('Table View')

        // Step 6: Validate cards with special characters preserved
        const cardEls = doc.getElementsByTagName('card')
        expect(cardEls.length).toBe(2)
        expect(cardEls[0].getAttribute('id')).toBe('card-001')
        expect(cardEls[0].getAttribute('title')).toBe('Card with <HTML> & "quotes"')
        expect(cardEls[1].getAttribute('id')).toBe('card-002')
        expect(cardEls[1].getAttribute('title')).toBe("Card with 'apostrophes'")

        // Step 7: Validate blocks
        const blockEls = doc.getElementsByTagName('block')
        expect(blockEls.length).toBe(1)
        expect(blockEls[0].getAttribute('id')).toBe('block-001')
        expect(blockEls[0].getAttribute('title')).toBe('Content <with> special & chars')

        // Step 8: Validate card properties
        const cardPropsEl = doc.getElementsByTagName('cardProperties')[0]
        expect(cardPropsEl).toBeDefined()
        const propEls = cardPropsEl.getElementsByTagName('property')
        expect(propEls.length).toBe(1)
        expect(propEls[0].getAttribute('id')).toBe('prop-status')
        expect(propEls[0].getAttribute('name')).toBe('Status')
    })

    test('SIT1-002: should properly escape all XML special characters', () => {
        const board = TestBlockFactory.createBoard()
        board.id = 'escape-test'
        board.title = 'Test & < > " \' chars'

        const views: BoardView[] = []
        const cards: Card[] = []
        const blocks: Block[] = []

        XmlExporter.exportBoardXml(board, views, cards, blocks)

        const xmlContent = mockBlob.mock.calls[0][0][0]

        // The XML should contain escaped versions in the raw string
        expect(xmlContent).toContain('&amp;')
        expect(xmlContent).toContain('&lt;')
        expect(xmlContent).toContain('&gt;')
        expect(xmlContent).toContain('&quot;')
        expect(xmlContent).toContain('&apos;')

        // But when parsed, should return original characters
        const parser = new DOMParser()
        const doc = parser.parseFromString(xmlContent, 'text/xml')
        const boardEl = doc.getElementsByTagName('board')[0]
        expect(boardEl.getAttribute('title')).toBe('Test & < > " \' chars')
    })

    test('SIT1-003: should preserve data integrity for complex board with multiple views and cards', () => {
        const board = TestBlockFactory.createBoard()
        board.id = 'complex-board'
        board.title = 'Complex Project Board'
        board.cardProperties = [
            {
                id: 'status',
                name: 'Status',
                type: 'select',
                options: [
                    {id: 's1', value: 'Backlog', color: 'propColorGray'},
                    {id: 's2', value: 'In Progress', color: 'propColorBlue'},
                    {id: 's3', value: 'Review', color: 'propColorYellow'},
                    {id: 's4', value: 'Done', color: 'propColorGreen'},
                ],
            },
            {
                id: 'priority',
                name: 'Priority',
                type: 'select',
                options: [
                    {id: 'p1', value: 'High', color: 'propColorRed'},
                    {id: 'p2', value: 'Medium', color: 'propColorYellow'},
                    {id: 'p3', value: 'Low', color: 'propColorGreen'},
                ],
            },
        ]

        // Multiple views
        const tableView = TestBlockFactory.createBoardView(board)
        tableView.id = 'table-view'
        tableView.title = 'Table'
        tableView.fields.viewType = 'table'

        const boardView = TestBlockFactory.createBoardView(board)
        boardView.id = 'board-view'
        boardView.title = 'Board'
        boardView.fields.viewType = 'board'

        const galleryView = TestBlockFactory.createBoardView(board)
        galleryView.id = 'gallery-view'
        galleryView.title = 'Gallery'
        galleryView.fields.viewType = 'gallery'

        const views: BoardView[] = [tableView, boardView, galleryView]

        // Multiple cards
        const cards: Card[] = []
        for (let i = 1; i <= 10; i++) {
            const card = TestBlockFactory.createCard(board)
            card.id = `card-${i}`
            card.title = `Task ${i}`
            card.fields.properties = {
                status: `s${(i % 4) + 1}`,
                priority: `p${(i % 3) + 1}`,
            }
            cards.push(card)
        }

        const blocks: Block[] = []

        XmlExporter.exportBoardXml(board, views, cards, blocks)

        const xmlContent = mockBlob.mock.calls[0][0][0]
        const parser = new DOMParser()
        const doc = parser.parseFromString(xmlContent, 'text/xml')

        // Validate counts
        const viewEls = doc.getElementsByTagName('view')
        expect(viewEls.length).toBe(3)

        const cardEls = doc.getElementsByTagName('card')
        expect(cardEls.length).toBe(10)

        const propEls = doc.getElementsByTagName('cardProperties')[0].getElementsByTagName('property')
        expect(propEls.length).toBe(2)

        // Validate card property attributes
        expect(propEls[0].getAttribute('id')).toBe('status')
        expect(propEls[0].getAttribute('name')).toBe('Status')
        expect(propEls[1].getAttribute('id')).toBe('priority')
        expect(propEls[1].getAttribute('name')).toBe('Priority')
    })
})
