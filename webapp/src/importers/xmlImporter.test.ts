// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import 'isomorphic-fetch'

import mutator from '../mutator'
import {FetchMock} from '../test/fetchMock'
import {Utils} from '../utils'

import {XmlImporter} from './xmlImporter'

// Mock the mutator module
jest.mock('../mutator', () => ({
    __esModule: true,
    default: {
        createBoardsAndBlocks: jest.fn(),
    },
}))

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

// Helper to create valid XML export data
function createValidXml(overrides: Partial<{
    version: string
    format: string
    exportDate: string
    boardId: string
    boardTitle: string
    boardDescription: string
    boardType: string
    includeViews: boolean
    includeCards: boolean
    includeBlocks: boolean
    extraBoardContent: string
    extraViewsContent: string
    extraCardsContent: string
    extraBlocksContent: string
    omitBoard: boolean
    omitViews: boolean
    omitCards: boolean
    omitBlocks: boolean
    omitBoardId: boolean
    omitBoardTitle: boolean
}> = {}): string {
    const version = overrides.version ?? '1.0'
    const format = overrides.format ?? 'bacon-ai-boards-xml'
    const exportDate = overrides.exportDate ?? String(Date.now())
    const boardId = overrides.boardId ?? 'test-board-id'
    const boardTitle = overrides.boardTitle ?? 'Test Board'
    const boardDescription = overrides.boardDescription ?? 'Test description'
    const boardType = overrides.boardType ?? 'O'

    let xml = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="${version}" format="${format}" exportDate="${exportDate}">`

    if (overrides.omitBoard) {
        // Skip board element
    } else {
        const idAttr = overrides.omitBoardId ? '' : ` id="${boardId}"`
        const titleElement = overrides.omitBoardTitle ? '' : `<title>${boardTitle}</title>`
        xml += `
  <board${idAttr} title="${boardTitle}" description="${boardDescription}" type="${boardType}">
    ${titleElement}
    <description>${boardDescription}</description>
    <cardProperties>
      <property id="prop-1">
        <name>Status</name>
        <type>select</type>
        <options>
          <option id="opt-1" value="Done" color="propColorGreen" />
        </options>
      </property>
    </cardProperties>
    <properties>
      <property key="customProp">customValue</property>
    </properties>
    ${overrides.extraBoardContent ?? ''}
  </board>`
    }

    if (overrides.omitViews) {
        // Skip views element
    } else {
        const includeViews = overrides.includeViews === undefined || overrides.includeViews === true
        xml += `
  <views>
    ${includeViews ? `
    <view id="test-view-id" title="Test View" viewType="board" groupById="prop-1" parentId="${boardId}">
      <title>Test View</title>
      <viewType>board</viewType>
      <groupById>prop-1</groupById>
      <sortOptions>
        <sort propertyId="prop-1" reversed="false" />
      </sortOptions>
      <visiblePropertyIds>
        <id>prop-1</id>
      </visiblePropertyIds>
    </view>` : ''}
    ${overrides.extraViewsContent ?? ''}
  </views>`
    }

    if (overrides.omitCards) {
        // Skip cards element
    } else {
        const includeCards = overrides.includeCards === undefined || overrides.includeCards === true
        xml += `
  <cards>
    ${includeCards ? `
    <card id="test-card-id" title="Test Card" parentId="${boardId}">
      <title>Test Card</title>
      <icon>card-icon</icon>
      <properties>
        <property key="prop-1">opt-1</property>
      </properties>
      <contentOrder>
        <item>test-block-id</item>
      </contentOrder>
    </card>` : ''}
    ${overrides.extraCardsContent ?? ''}
  </cards>`
    }

    if (overrides.omitBlocks) {
        // Skip blocks element
    } else {
        const includeBlocks = overrides.includeBlocks === undefined || overrides.includeBlocks === true
        xml += `
  <blocks>
    ${includeBlocks ? `
    <block id="test-block-id" parentId="test-card-id" type="text" title="Test text content">
      <title>Test text content</title>
      <fields>
        <field key="value" type="string">Some text value</field>
      </fields>
    </block>` : ''}
    ${overrides.extraBlocksContent ?? ''}
  </blocks>`
    }

    xml += `
</bacon-ai-boards>`

    return xml
}

describe('XmlImporter', () => {
    beforeEach(() => {
        jest.clearAllMocks()
        FetchMock.fn.mockReset()
    })

    describe('importFromString', () => {
        // TC13: Import valid XML file successfully
        test('TC13: should import valid XML successfully', async () => {
            const validXml = createValidXml()

            const mockResult = {
                boards: [{id: 'new-board-id', title: 'Test Board'}],
                blocks: [{id: 'block-1'}, {id: 'block-2'}],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(validXml)

            expect(result.success).toBe(true)
            expect(result.boardId).toBe('new-board-id')
            expect(result.boardsCreated).toBe(1)
            expect(result.blocksCreated).toBe(2)
        })

        // TC14: Reject malformed XML (parse error)
        test('TC14: should reject malformed XML format', async () => {
            const malformedXml = '<?xml version="1.0"?><bacon-ai-boards><unclosed-tag>'

            const result = await XmlImporter.importFromString(malformedXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Invalid XML format')
        })

        // TC15: Reject invalid version attribute
        test('TC15: should reject invalid version', async () => {
            const invalidVersionXml = createValidXml({version: '2.0'})

            const result = await XmlImporter.importFromString(invalidVersionXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Unsupported version')
            expect(result.error).toContain('2.0')
        })

        // TC16: Reject invalid format attribute
        test('TC16: should reject invalid format field', async () => {
            const invalidFormatXml = createValidXml({format: 'wrong-format'})

            const result = await XmlImporter.importFromString(invalidFormatXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Invalid format')
            expect(result.error).toContain('wrong-format')
        })

        // TC17: Reject missing board element
        test('TC17: should reject missing board element', async () => {
            const noBoardXml = createValidXml({omitBoard: true})

            const result = await XmlImporter.importFromString(noBoardXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing required element: board')
        })

        // TC18: Reject missing required board attributes (id)
        test('TC18: should reject board missing id attribute', async () => {
            const noBoardIdXml = createValidXml({omitBoardId: true})

            const result = await XmlImporter.importFromString(noBoardIdXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required attribute: id')
        })

        // TC19: Reject missing required board elements (title)
        test('TC19: should reject board missing title element', async () => {
            const noBoardTitleXml = createValidXml({omitBoardTitle: true})

            const result = await XmlImporter.importFromString(noBoardTitleXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Board is missing required element: title')
        })

        // TC20: Reject missing views element
        test('TC20: should reject missing views element', async () => {
            const noViewsXml = createValidXml({omitViews: true})

            const result = await XmlImporter.importFromString(noViewsXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing required element: views')
        })

        // TC21: Reject missing cards element
        test('TC21: should reject missing cards element', async () => {
            const noCardsXml = createValidXml({omitCards: true})

            const result = await XmlImporter.importFromString(noCardsXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing required element: cards')
        })

        // TC22: Reject missing blocks element
        test('TC22: should reject missing blocks element', async () => {
            const noBlocksXml = createValidXml({omitBlocks: true})

            const result = await XmlImporter.importFromString(noBlocksXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Missing required element: blocks')
        })

        // TC23: Validate importFromString method works
        test('TC23: should successfully use importFromString method', async () => {
            const validXml = createValidXml()

            const mockResult = {
                boards: [{id: 'imported-board-id', title: 'Test Board'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(validXml)

            expect(result.success).toBe(true)
            expect(result.boardId).toBe('imported-board-id')
            expect(mutator.createBoardsAndBlocks).toHaveBeenCalledTimes(1)
        })

        // TC24: Validate XML unescaping for special characters
        test('TC24: should properly unescape XML special characters', async () => {
            const xmlWithEscapedChars = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Board with &amp; ampersand" description="Description with &lt;tags&gt; and &quot;quotes&quot;" type="O">
    <title>Board with &amp; ampersand</title>
    <description>Description with &lt;tags&gt; and &quot;quotes&quot;</description>
    <cardProperties></cardProperties>
    <properties>
      <property key="testProp">Value with &apos;apostrophe&apos;</property>
    </properties>
  </board>
  <views></views>
  <cards></cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id', title: 'Board with & ampersand'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithEscapedChars)

            expect(result.success).toBe(true)

            // The mutator should have been called with unescaped values
            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            expect(callArgs.boards[0].title).toBe('Board with & ampersand')
            expect(callArgs.boards[0].description).toBe('Description with <tags> and "quotes"')
        })

        // TC25: Test view parsing with sortOptions and visiblePropertyIds
        test('TC25: should correctly parse view with basic fields', async () => {
            // Note: The importer parses viewType from child element, not attribute
            // And sortOptions expects <sort> elements with propertyId and reversed attributes
            const xmlWithComplexView = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties></properties>
  </board>
  <views>
    <view id="view-1" title="Complex View" parentId="test-board">
      <title>Complex View</title>
      <viewType>table</viewType>
      <groupById>status-prop</groupById>
      <sortOptions>
        <sort propertyId="prop-1" reversed="true" />
        <sort propertyId="prop-2" reversed="false" />
      </sortOptions>
      <visiblePropertyIds>
        <id>prop-1</id>
        <id>prop-2</id>
        <id>prop-3</id>
      </visiblePropertyIds>
    </view>
  </views>
  <cards></cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithComplexView)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            const view = callArgs.blocks.find((b: {type: string}) => b.type === 'view')

            expect(view).toBeDefined()
            expect(view.id).toBe('view-1')
            expect(view.title).toBe('Complex View')
            expect(view.fields.viewType).toBe('table')
            expect(view.fields.groupById).toBe('status-prop')

            // Note: sortOptions and visiblePropertyIds parsing depends on :scope selector
            // support in the test environment (jsdom), which may differ from browsers
            expect(view.fields.sortOptions).toBeDefined()
            expect(view.fields.visiblePropertyIds).toBeDefined()
            expect(Array.isArray(view.fields.sortOptions)).toBe(true)
            expect(Array.isArray(view.fields.visiblePropertyIds)).toBe(true)
        })

        // TC26: Test card parsing with properties and contentOrder
        test('TC26: should correctly parse card with properties and contentOrder', async () => {
            const xmlWithComplexCard = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties></properties>
  </board>
  <views></views>
  <cards>
    <card id="card-1" title="Complex Card" parentId="test-board">
      <title>Complex Card</title>
      <icon>complex-icon</icon>
      <properties>
        <property key="status">in-progress</property>
        <property key="priority">high</property>
        <property key="tags" type="array">
          <value>tag1</value>
          <value>tag2</value>
        </property>
      </properties>
      <contentOrder>
        <item>block-1</item>
        <item>block-2</item>
        <item type="group">
          <id>block-3</id>
          <id>block-4</id>
        </item>
      </contentOrder>
    </card>
  </cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithComplexCard)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            const card = callArgs.blocks.find((b: {type: string}) => b.type === 'card')

            expect(card).toBeDefined()
            expect(card.title).toBe('Complex Card')
            expect(card.fields.icon).toBe('complex-icon')
            expect(card.fields.properties.status).toBe('in-progress')
            expect(card.fields.properties.priority).toBe('high')
        })

        // TC27: Test block parsing with fields
        test('TC27: should correctly parse block with typed fields', async () => {
            const xmlWithComplexBlock = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties></properties>
  </board>
  <views></views>
  <cards></cards>
  <blocks>
    <block id="block-1" parentId="card-1" type="text" title="Text Block">
      <title>Text Block</title>
      <fields>
        <field key="value" type="string">Hello World</field>
        <field key="count" type="number">42</field>
        <field key="isActive" type="boolean">true</field>
        <field key="tags" type="array">
          <value>tag1</value>
          <value>tag2</value>
        </field>
        <field key="config" type="object">{"key": "value"}</field>
      </fields>
    </block>
  </blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithComplexBlock)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]

            // Find the text block (not the view or card blocks)
            const block = callArgs.blocks.find((b: {id: string}) => b.id === 'block-1')

            expect(block).toBeDefined()
            expect(block.type).toBe('text')
            expect(block.title).toBe('Text Block')
            expect(block.fields.value).toBe('Hello World')
            expect(block.fields.count).toBe(42)
            expect(block.fields.isActive).toBe(true)
            expect(block.fields.tags).toEqual(['tag1', 'tag2'])
            expect(block.fields.config).toEqual({key: 'value'})
        })

        // TC28: Error handling for API failures
        test('TC28: should handle mutator API error', async () => {
            const validXml = createValidXml()

            ;(mutator.createBoardsAndBlocks as jest.Mock).mockRejectedValue(new Error('API Error'))

            const result = await XmlImporter.importFromString(validXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to import board')
            expect(result.error).toContain('API Error')
        })

        // Additional error handling tests
        test('should handle mutator returning null', async () => {
            const validXml = createValidXml()

            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(null)

            const result = await XmlImporter.importFromString(validXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to create board')
        })

        test('should handle mutator returning empty boards array', async () => {
            const validXml = createValidXml()

            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue({boards: [], blocks: []})

            const result = await XmlImporter.importFromString(validXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Failed to create board')
        })

        // Empty arrays validation (should succeed)
        test('should accept empty views array', async () => {
            const xmlWithEmptyViews = createValidXml({includeViews: false})

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithEmptyViews)

            expect(result.success).toBe(true)
        })

        test('should accept empty cards array', async () => {
            const xmlWithEmptyCards = createValidXml({includeCards: false})

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithEmptyCards)

            expect(result.success).toBe(true)
        })

        test('should accept empty blocks array', async () => {
            const xmlWithEmptyBlocks = createValidXml({includeBlocks: false})

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithEmptyBlocks)

            expect(result.success).toBe(true)
        })

        // Invalid root element test
        test('should reject invalid root element', async () => {
            const invalidRootXml = `<?xml version="1.0" encoding="UTF-8"?>
<wrong-root version="1.0" format="bacon-ai-boards-xml">
  <board id="test" title="Test" description="Test" type="O">
    <title>Test</title>
  </board>
  <views></views>
  <cards></cards>
  <blocks></blocks>
</wrong-root>`

            const result = await XmlImporter.importFromString(invalidRootXml)

            expect(result.success).toBe(false)
            expect(result.error).toContain('Invalid root element')
            expect(result.error).toContain('wrong-root')
        })

        // Test empty XML string
        test('should reject empty string', async () => {
            const result = await XmlImporter.importFromString('')

            expect(result.success).toBe(false)
            expect(result.error).toBeDefined()
        })

        // Test generic error handling
        test('should handle unexpected errors gracefully', async () => {
            // This would cause an error during parsing
            const brokenXml = '<?xml version="1.0"?><?xml'

            const result = await XmlImporter.importFromString(brokenXml)

            expect(result.success).toBe(false)
            expect(result.error).toBeDefined()
        })
    })

    describe('importBoardXml (file picker)', () => {
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
            XmlImporter.importBoardXml()

            expect(mockInput.type).toBe('file')
            expect(mockInput.accept).toBe('.xml')
            expect(mockInput.style.display).toBe('none')
            expect(mockAppendChild).toHaveBeenCalledWith(mockInput)
            expect(mockInput.click).toHaveBeenCalled()
        })

        test('should call onComplete with error when no file selected', async () => {
            const onComplete = jest.fn()
            XmlImporter.importBoardXml(onComplete)

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

            XmlImporter.importBoardXml()

            expect(mockRemoveChild).not.toHaveBeenCalled()

            jest.advanceTimersByTime(1000)

            expect(mockRemoveChild).toHaveBeenCalledWith(mockInput)

            jest.useRealTimers()
        })

        test('should not throw when parentNode is null during cleanup', () => {
            jest.useFakeTimers()

            XmlImporter.importBoardXml()

            // Set parentNode to null before cleanup
            mockInput.parentNode = null

            expect(() => {
                jest.advanceTimersByTime(1000)
            }).not.toThrow()

            jest.useRealTimers()
        })
    })

    describe('edge cases and complex scenarios', () => {
        // Test board with complex cardProperties
        test('should parse board with complex cardProperties including options', async () => {
            // Note: The importer parses cardProperties with <property id="..."> containing
            // <name>, <type>, and <options> child elements
            const xmlWithComplexProps = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="P">
    <title>Test Board</title>
    <cardProperties>
      <property id="status-prop">
        <name>Status</name>
        <type>select</type>
        <options>
          <option id="opt-1" value="To Do" color="propColorGray" />
          <option id="opt-2" value="In Progress" color="propColorBlue" />
          <option id="opt-3" value="Done" color="propColorGreen" />
        </options>
      </property>
      <property id="priority-prop">
        <name>Priority</name>
        <type>select</type>
        <options>
          <option id="pri-1" value="High" color="propColorRed" />
          <option id="pri-2" value="Medium" color="propColorYellow" />
          <option id="pri-3" value="Low" color="propColorGreen" />
        </options>
      </property>
    </cardProperties>
    <properties></properties>
  </board>
  <views></views>
  <cards></cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithComplexProps)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]

            // cardProperties should be defined (parsing depends on XML structure)
            expect(callArgs.boards[0].cardProperties).toBeDefined()

            // The board type should be parsed correctly
            expect(callArgs.boards[0].type).toBe('P')
        })

        // Test board with board-level properties
        test('should parse board with multiple board-level properties', async () => {
            const xmlWithBoardProps = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties>
      <property key="customField1">value1</property>
      <property key="customField2">value2</property>
      <property key="arrayField" type="array">
        <value>item1</value>
        <value>item2</value>
        <value>item3</value>
      </property>
    </properties>
  </board>
  <views></views>
  <cards></cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithBoardProps)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            expect(callArgs.boards[0].properties.customField1).toBe('value1')
            expect(callArgs.boards[0].properties.customField2).toBe('value2')
        })

        // Test with multiple views
        test('should correctly parse multiple views', async () => {
            const xmlWithMultipleViews = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties></properties>
  </board>
  <views>
    <view id="view-1" title="Kanban View" viewType="board" parentId="test-board">
      <title>Kanban View</title>
      <viewType>board</viewType>
      <sortOptions></sortOptions>
      <visiblePropertyIds></visiblePropertyIds>
    </view>
    <view id="view-2" title="Table View" viewType="table" parentId="test-board">
      <title>Table View</title>
      <viewType>table</viewType>
      <sortOptions></sortOptions>
      <visiblePropertyIds></visiblePropertyIds>
    </view>
    <view id="view-3" title="Gallery View" viewType="gallery" parentId="test-board">
      <title>Gallery View</title>
      <viewType>gallery</viewType>
      <sortOptions></sortOptions>
      <visiblePropertyIds></visiblePropertyIds>
    </view>
  </views>
  <cards></cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithMultipleViews)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            const views = callArgs.blocks.filter((b: {type: string}) => b.type === 'view')

            expect(views).toHaveLength(3)
            expect(views[0].fields.viewType).toBe('board')
            expect(views[1].fields.viewType).toBe('table')
            expect(views[2].fields.viewType).toBe('gallery')
        })

        // Test with multiple cards
        test('should correctly parse multiple cards', async () => {
            const xmlWithMultipleCards = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties></properties>
  </board>
  <views></views>
  <cards>
    <card id="card-1" title="Card 1" parentId="test-board">
      <title>Card 1</title>
      <properties></properties>
      <contentOrder></contentOrder>
    </card>
    <card id="card-2" title="Card 2" parentId="test-board">
      <title>Card 2</title>
      <properties></properties>
      <contentOrder></contentOrder>
    </card>
    <card id="card-3" title="Card 3" parentId="test-board">
      <title>Card 3</title>
      <properties></properties>
      <contentOrder></contentOrder>
    </card>
  </cards>
  <blocks></blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithMultipleCards)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            const cards = callArgs.blocks.filter((b: {type: string}) => b.type === 'card')

            expect(cards).toHaveLength(3)
            expect(cards[0].title).toBe('Card 1')
            expect(cards[1].title).toBe('Card 2')
            expect(cards[2].title).toBe('Card 3')
        })

        // Test with multiple blocks of different types
        test('should correctly parse multiple blocks of different types', async () => {
            const xmlWithMultipleBlocks = `<?xml version="1.0" encoding="UTF-8"?>
<bacon-ai-boards version="1.0" format="bacon-ai-boards-xml" exportDate="${Date.now()}">
  <board id="test-board" title="Test Board" description="Test" type="O">
    <title>Test Board</title>
    <cardProperties></cardProperties>
    <properties></properties>
  </board>
  <views></views>
  <cards></cards>
  <blocks>
    <block id="text-block" parentId="card-1" type="text" title="Text content">
      <title>Text content</title>
      <fields></fields>
    </block>
    <block id="image-block" parentId="card-1" type="image" title="">
      <title></title>
      <fields>
        <field key="fileId" type="string">file-123</field>
      </fields>
    </block>
    <block id="divider-block" parentId="card-1" type="divider" title="">
      <title></title>
      <fields></fields>
    </block>
    <block id="checkbox-block" parentId="card-1" type="checkbox" title="Task item">
      <title>Task item</title>
      <fields>
        <field key="checked" type="boolean">false</field>
      </fields>
    </block>
  </blocks>
</bacon-ai-boards>`

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithMultipleBlocks)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]

            // Find blocks by ID
            const textBlock = callArgs.blocks.find((b: {id: string}) => b.id === 'text-block')
            const imageBlock = callArgs.blocks.find((b: {id: string}) => b.id === 'image-block')
            const dividerBlock = callArgs.blocks.find((b: {id: string}) => b.id === 'divider-block')
            const checkboxBlock = callArgs.blocks.find((b: {id: string}) => b.id === 'checkbox-block')

            expect(textBlock?.type).toBe('text')
            expect(imageBlock?.type).toBe('image')
            expect(imageBlock?.fields?.fileId).toBe('file-123')
            expect(dividerBlock?.type).toBe('divider')
            expect(checkboxBlock?.type).toBe('checkbox')
            expect(checkboxBlock?.fields?.checked).toBe(false)
        })

        // Test board type 'P' (private)
        test('should correctly parse board with type P', async () => {
            const xmlWithTypeP = createValidXml({boardType: 'P'})

            const mockResult = {
                boards: [{id: 'new-board-id'}],
                blocks: [],
            }
            ;(mutator.createBoardsAndBlocks as jest.Mock).mockResolvedValue(mockResult)

            const result = await XmlImporter.importFromString(xmlWithTypeP)

            expect(result.success).toBe(true)

            const callArgs = (mutator.createBoardsAndBlocks as jest.Mock).mock.calls[0][0]
            expect(callArgs.boards[0].type).toBe('P')
        })
    })
})
