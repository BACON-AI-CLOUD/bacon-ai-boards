// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {Board} from '../blocks/board'
import {Card} from '../blocks/card'
import {BpmnMappingConfig} from '../types/bpmn'

import {BpmnExporter} from './bpmnExporter'

describe('BpmnExporter', () => {
    let mockBoard: Board
    let mockCards: Card[]
    let mockConfig: BpmnMappingConfig

    beforeEach(() => {
        // Create mock board with status property
        mockBoard = {
            id: 'board1',
            teamId: 'team1',
            createdBy: 'user1',
            modifiedBy: 'user1',
            type: 'P',
            minimumRole: '',
            title: 'Test Process Board',
            description: 'A test board for BPMN export',
            icon: '',
            showDescription: false,
            isTemplate: false,
            templateVersion: 0,
            properties: {},
            cardProperties: [
                {
                    id: 'status-prop-1',
                    name: 'Status',
                    type: 'select',
                    options: [
                        {id: 'status1', value: 'To Do', color: 'blue'},
                        {id: 'status2', value: 'In Progress', color: 'yellow'},
                        {id: 'status3', value: 'Done', color: 'green'},
                    ],
                },
            ],
            createAt: Date.now(),
            updateAt: Date.now(),
            deleteAt: 0,
        } as Board

        // Create mock cards
        mockCards = [
            {
                id: 'card1',
                parentId: 'board1',
                type: 'card',
                title: 'Task 1',
                fields: {
                    properties: {
                        'status-prop-1': 'status1',
                    },
                    contentOrder: [],
                },
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
                schema: 1,
                rootId: 'board1',
                modifiedBy: 'user1',
                createdBy: 'user1',
            } as Card,
            {
                id: 'card2',
                parentId: 'board1',
                type: 'card',
                title: 'Task 2',
                fields: {
                    properties: {
                        'status-prop-1': 'status2',
                    },
                    contentOrder: [],
                },
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
                schema: 1,
                rootId: 'board1',
                modifiedBy: 'user1',
                createdBy: 'user1',
            } as Card,
            {
                id: 'card3',
                parentId: 'board1',
                type: 'card',
                title: 'Task 3',
                fields: {
                    properties: {
                        'status-prop-1': 'status3',
                    },
                    contentOrder: [],
                },
                createAt: Date.now(),
                updateAt: Date.now(),
                deleteAt: 0,
                schema: 1,
                rootId: 'board1',
                modifiedBy: 'user1',
                createdBy: 'user1',
            } as Card,
        ]

        // Create mock config
        mockConfig = {
            statusPropertyId: 'status-prop-1',
            startStates: ['status1'],
            endStates: ['status3'],
        }
    })

    test('should export board with basic configuration', () => {
        // Mock URL.createObjectURL and revokeObjectURL
        global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
        global.URL.revokeObjectURL = jest.fn()

        // Create a real anchor element
        const mockLink = document.createElement('a')
        const clickSpy = jest.spyOn(mockLink, 'click').mockImplementation()

        const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockLink)

        // Export
        BpmnExporter.exportBoardBpmn(mockBoard, mockCards, mockConfig)

        // Verify link was created and clicked
        expect(createElementSpy).toHaveBeenCalledWith('a')
        expect(clickSpy).toHaveBeenCalled()
        expect(mockLink.download).toContain('.bpmn')

        // Cleanup
        createElementSpy.mockRestore()
        clickSpy.mockRestore()
    })

    test('should throw error if status property not found', () => {
        const invalidConfig: BpmnMappingConfig = {
            statusPropertyId: 'invalid-prop',
            startStates: [],
            endStates: [],
        }

        expect(() => {
            BpmnExporter.exportBoardBpmn(mockBoard, mockCards, invalidConfig)
        }).toThrow('Status property with ID invalid-prop not found')
    })

    test('should handle boards with no cards', () => {
        // Mock URL.createObjectURL and revokeObjectURL
        global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
        global.URL.revokeObjectURL = jest.fn()

        // Create a real anchor element
        const mockLink = document.createElement('a')
        const clickSpy = jest.spyOn(mockLink, 'click').mockImplementation()

        const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockLink)

        // Export with empty cards array
        BpmnExporter.exportBoardBpmn(mockBoard, [], mockConfig)

        // Should still create a download
        expect(clickSpy).toHaveBeenCalled()

        // Cleanup
        createElementSpy.mockRestore()
        clickSpy.mockRestore()
    })
})
