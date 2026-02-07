// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import {Board, IPropertyTemplate, IPropertyOption} from '../blocks/board'
import {Card} from '../blocks/card'
import {Utils} from '../utils'
import {IAppWindow} from '../types'
import {
    BpmnDefinitions,
    BpmnProcess,
    BpmnTask,
    BpmnLane,
    BpmnSequenceFlow,
    BpmnMappingConfig,
    BpmnStartEvent,
    BpmnEndEvent,
    BpmnDiagram,
    BpmnShape,
    BpmnEdge,
    BPMN_NAMESPACES,
} from '../types/bpmn'

declare let window: IAppWindow

/**
 * BpmnExporter provides functionality to export board data as BPMN 2.0 XML files.
 * This enables process modeling and integration with BPMN-compatible tools.
 *
 * Mapping logic:
 * - Board → bpmn:process
 * - Status property options → bpmn:lane (swimlanes)
 * - Cards → bpmn:userTask (grouped by status)
 * - Card dependencies → bpmn:sequenceFlow
 * - Fallback: Sequential connections within and between status columns
 */
class BpmnExporter {
    // Layout constants for BPMN diagram elements
    private static readonly LANE_HEIGHT = 200
    private static readonly LANE_WIDTH = 1200
    private static readonly TASK_WIDTH = 100
    private static readonly TASK_HEIGHT = 80
    private static readonly TASK_SPACING_X = 150
    private static readonly TASK_SPACING_Y = 30
    private static readonly EVENT_SIZE = 36
    private static readonly START_X = 100
    private static readonly START_Y = 50

    /**
     * Exports a board and its cards as a BPMN 2.0 XML file.
     * The file is automatically downloaded to the user's device.
     *
     * @param board - The board to export
     * @param cards - All cards in the board
     * @param config - BPMN mapping configuration (status property, start/end states, dependencies)
     */
    static exportBoardBpmn(board: Board, cards: Card[], config: BpmnMappingConfig): void {
        const definitions = BpmnExporter.mapBoardToBpmn(board, cards, config)
        const xml = BpmnExporter.generateBpmnXml(definitions)
        BpmnExporter.downloadBpmn(xml, board.title || 'process')
    }

    /**
     * Maps board data to BPMN definitions object.
     *
     * @param board - The board to map
     * @param cards - All cards in the board
     * @param config - BPMN mapping configuration
     * @returns Complete BPMN definitions object
     */
    private static mapBoardToBpmn(board: Board, cards: Card[], config: BpmnMappingConfig): BpmnDefinitions {
        const processId = `Process_${board.id}`

        // Find the status property
        const statusProperty = board.cardProperties.find((prop) => prop.id === config.statusPropertyId)
        if (!statusProperty) {
            throw new Error(`Status property with ID ${config.statusPropertyId} not found`)
        }

        // Group cards by status
        const groupedCards = BpmnExporter.groupCardsByStatus(cards, config.statusPropertyId)

        // Create lanes from status options
        const lanes = BpmnExporter.createLanes(statusProperty, groupedCards)

        // Create tasks from cards
        const tasks = BpmnExporter.createTasks(cards, config.statusPropertyId, lanes)

        // Create start and end events
        const startEvent: BpmnStartEvent = {
            id: 'StartEvent_1',
            name: 'Start',
            outgoing: [],
        }

        const endEvent: BpmnEndEvent = {
            id: 'EndEvent_1',
            name: 'End',
            incoming: [],
        }

        // Create sequence flows
        const sequenceFlows = BpmnExporter.createSequenceFlows(
            cards,
            groupedCards,
            config,
            startEvent,
            endEvent,
            tasks,
        )

        // Build process
        const process: BpmnProcess = {
            id: processId,
            name: board.title,
            isExecutable: false,
            laneSet: lanes.length > 0 ? {
                id: 'LaneSet_1',
                lanes,
            } : undefined,
            startEvents: [startEvent],
            endEvents: [endEvent],
            tasks,
            sequenceFlows,
        }

        // Calculate diagram layout
        const diagram = BpmnExporter.calculateDiagramLayout(process)

        return {
            id: 'Definitions_1',
            targetNamespace: 'http://bacon-ai.cloud/bpmn',
            process,
            diagram,
        }
    }

    /**
     * Groups cards by their status property value.
     *
     * @param cards - All cards to group
     * @param statusPropertyId - The property ID representing status
     * @returns Map of status option ID to cards in that status
     */
    private static groupCardsByStatus(cards: Card[], statusPropertyId: string): Map<string, Card[]> {
        const grouped = new Map<string, Card[]>()

        cards.forEach((card) => {
            const statusValue = card.fields.properties[statusPropertyId]
            const statusId = Array.isArray(statusValue) ? statusValue[0] : statusValue

            if (!statusId) {
                return
            }

            if (!grouped.has(statusId)) {
                grouped.set(statusId, [])
            }
            grouped.get(statusId)!.push(card)
        })

        return grouped
    }

    /**
     * Creates BPMN lanes from status property options.
     *
     * @param statusProperty - The status property template
     * @param groupedCards - Cards grouped by status
     * @returns Array of BPMN lanes
     */
    private static createLanes(
        statusProperty: IPropertyTemplate,
        groupedCards: Map<string, Card[]>,
    ): BpmnLane[] {
        return statusProperty.options.map((option: IPropertyOption) => {
            const cardsInLane = groupedCards.get(option.id) || []
            const flowNodeRefs = cardsInLane.map((card) => `task_${card.id}`)

            return {
                id: `Lane_${option.id}`,
                name: option.value,
                flowNodeRefs,
                optionId: option.id,
            }
        })
    }

    /**
     * Creates BPMN user tasks from cards.
     *
     * @param cards - All cards to convert
     * @param statusPropertyId - The property ID representing status
     * @param lanes - BPMN lanes for lane reference
     * @returns Array of BPMN tasks
     */
    private static createTasks(
        cards: Card[],
        statusPropertyId: string,
        lanes: BpmnLane[],
    ): BpmnTask[] {
        return cards.map((card) => {
            const statusValue = card.fields.properties[statusPropertyId]
            const statusId = Array.isArray(statusValue) ? statusValue[0] : statusValue

            const lane = lanes.find((l) => l.optionId === statusId)

            return {
                id: `task_${card.id}`,
                name: card.title || 'Untitled',
                type: 'userTask',
                laneRef: lane ? lane.id : undefined,
                incoming: [],
                outgoing: [],
                cardId: card.id,
            }
        })
    }

    /**
     * Creates sequence flows based on card order and dependencies.
     *
     * @param cards - All cards
     * @param groupedCards - Cards grouped by status
     * @param config - BPMN mapping configuration
     * @param startEvent - Start event to connect from
     * @param endEvent - End event to connect to
     * @param tasks - All tasks to connect
     * @returns Array of BPMN sequence flows
     */
    private static createSequenceFlows(
        cards: Card[],
        groupedCards: Map<string, Card[]>,
        config: BpmnMappingConfig,
        startEvent: BpmnStartEvent,
        endEvent: BpmnEndEvent,
        tasks: BpmnTask[],
    ): BpmnSequenceFlow[] {
        const flows: BpmnSequenceFlow[] = []
        let flowCounter = 1

        // Track which tasks have incoming/outgoing connections
        const taskConnections = new Map<string, {incoming: string[], outgoing: string[]}>()
        tasks.forEach((task) => {
            taskConnections.set(task.id, {incoming: [], outgoing: []})
        })

        // If dependency property is provided, create flows based on dependencies
        if (config.dependencyPropertyId) {
            const depPropId = config.dependencyPropertyId
            cards.forEach((card) => {
                const dependencies = card.fields.properties[depPropId]
                const taskId = `task_${card.id}`

                if (dependencies) {
                    const depIds = Array.isArray(dependencies) ? dependencies : [dependencies]

                    depIds.forEach((depId) => {
                        const sourceTask = tasks.find((t) => t.cardId === depId)
                        if (sourceTask) {
                            const flowId = `Flow_${flowCounter++}`
                            flows.push({
                                id: flowId,
                                sourceRef: sourceTask.id,
                                targetRef: taskId,
                            })

                            taskConnections.get(sourceTask.id)!.outgoing.push(flowId)
                            taskConnections.get(taskId)!.incoming.push(flowId)
                        }
                    })
                }
            })
        }

        // Fallback: Create sequential flows within each status column
        groupedCards.forEach((cardsInStatus) => {
            for (let i = 0; i < cardsInStatus.length - 1; i++) {
                const currentTaskId = `task_${cardsInStatus[i].id}`
                const nextTaskId = `task_${cardsInStatus[i + 1].id}`

                // Only create flow if not already connected
                const currentConnections = taskConnections.get(currentTaskId)!
                const nextConnections = taskConnections.get(nextTaskId)!

                if (currentConnections.outgoing.length > 0 && nextConnections.incoming.length > 0) {
                    // Already connected, skip
                } else {
                    const flowId = `Flow_${flowCounter++}`
                    flows.push({
                        id: flowId,
                        sourceRef: currentTaskId,
                        targetRef: nextTaskId,
                    })

                    currentConnections.outgoing.push(flowId)
                    nextConnections.incoming.push(flowId)
                }
            }
        })

        // Connect start event to tasks in start states
        const firstTasks: BpmnTask[] = []
        config.startStates.forEach((stateId) => {
            const cardsInState = groupedCards.get(stateId)
            if (cardsInState && cardsInState.length > 0) {
                const taskId = `task_${cardsInState[0].id}`
                const task = tasks.find((t) => t.id === taskId)
                if (task) {
                    firstTasks.push(task)
                }
            }
        })

        // If no start states or no tasks in start states, connect to first task
        if (firstTasks.length === 0 && tasks.length > 0) {
            firstTasks.push(tasks[0])
        }

        firstTasks.forEach((task) => {
            const flowId = `Flow_${flowCounter++}`
            flows.push({
                id: flowId,
                sourceRef: startEvent.id,
                targetRef: task.id,
            })
            startEvent.outgoing.push(flowId)
            taskConnections.get(task.id)!.incoming.push(flowId)
        })

        // Connect tasks in end states to end event
        const lastTasks: BpmnTask[] = []
        config.endStates.forEach((stateId) => {
            const cardsInState = groupedCards.get(stateId)
            if (cardsInState && cardsInState.length > 0) {
                const taskId = `task_${cardsInState[cardsInState.length - 1].id}`
                const task = tasks.find((t) => t.id === taskId)
                if (task) {
                    lastTasks.push(task)
                }
            }
        })

        // If no end states or no tasks in end states, connect from last task
        if (lastTasks.length === 0 && tasks.length > 0) {
            lastTasks.push(tasks[tasks.length - 1])
        }

        lastTasks.forEach((task) => {
            const flowId = `Flow_${flowCounter++}`
            flows.push({
                id: flowId,
                sourceRef: task.id,
                targetRef: endEvent.id,
            })
            taskConnections.get(task.id)!.outgoing.push(flowId)
            endEvent.incoming.push(flowId)
        })

        // Update task incoming/outgoing arrays
        tasks.forEach((task) => {
            const connections = taskConnections.get(task.id)!
            task.incoming = connections.incoming
            task.outgoing = connections.outgoing
        })

        return flows
    }

    /**
     * Calculates layout positions for diagram elements.
     *
     * @param process - The BPMN process
     * @returns BPMN diagram with calculated positions
     */
    private static calculateDiagramLayout(process: BpmnProcess): BpmnDiagram {
        const shapes: BpmnShape[] = []
        const edges: BpmnEdge[] = []

        let currentY = BpmnExporter.START_Y

        // Add start event shape
        shapes.push({
            id: `${process.startEvents[0].id}_di`,
            bpmnElement: process.startEvents[0].id,
            bounds: {
                x: BpmnExporter.START_X,
                y: currentY,
                width: BpmnExporter.EVENT_SIZE,
                height: BpmnExporter.EVENT_SIZE,
            },
        })

        currentY += BpmnExporter.EVENT_SIZE + 50

        // Add lane shapes and task shapes
        if (process.laneSet) {
            process.laneSet.lanes.forEach((lane) => {
                const laneY = currentY

                // Lane shape
                shapes.push({
                    id: `${lane.id}_di`,
                    bpmnElement: lane.id,
                    bounds: {
                        x: 50,
                        y: laneY,
                        width: BpmnExporter.LANE_WIDTH,
                        height: BpmnExporter.LANE_HEIGHT,
                    },
                    isHorizontal: true,
                })

                // Task shapes within lane
                let taskX = BpmnExporter.START_X + BpmnExporter.TASK_SPACING_X
                const taskY = laneY + BpmnExporter.TASK_SPACING_Y

                lane.flowNodeRefs.forEach((taskRef) => {
                    shapes.push({
                        id: `${taskRef}_di`,
                        bpmnElement: taskRef,
                        bounds: {
                            x: taskX,
                            y: taskY,
                            width: BpmnExporter.TASK_WIDTH,
                            height: BpmnExporter.TASK_HEIGHT,
                        },
                    })

                    taskX += BpmnExporter.TASK_WIDTH + BpmnExporter.TASK_SPACING_X
                })

                currentY += BpmnExporter.LANE_HEIGHT
            })
        } else {
            // No lanes - just lay out tasks horizontally
            let taskX = BpmnExporter.START_X + BpmnExporter.TASK_SPACING_X
            process.tasks.forEach((task) => {
                shapes.push({
                    id: `${task.id}_di`,
                    bpmnElement: task.id,
                    bounds: {
                        x: taskX,
                        y: currentY,
                        width: BpmnExporter.TASK_WIDTH,
                        height: BpmnExporter.TASK_HEIGHT,
                    },
                })

                taskX += BpmnExporter.TASK_WIDTH + BpmnExporter.TASK_SPACING_X
            })

            currentY += BpmnExporter.TASK_HEIGHT + 50
        }

        // Add end event shape
        shapes.push({
            id: `${process.endEvents[0].id}_di`,
            bpmnElement: process.endEvents[0].id,
            bounds: {
                x: BpmnExporter.START_X,
                y: currentY,
                width: BpmnExporter.EVENT_SIZE,
                height: BpmnExporter.EVENT_SIZE,
            },
        })

        // Add edges for sequence flows (simplified straight lines)
        process.sequenceFlows.forEach((flow) => {
            const sourceShape = shapes.find((s) => s.bpmnElement === flow.sourceRef)
            const targetShape = shapes.find((s) => s.bpmnElement === flow.targetRef)

            if (!sourceShape || !targetShape) {
                // Skip if shapes not found
            } else {
                edges.push({
                    id: `${flow.id}_di`,
                    bpmnElement: flow.id,
                    waypoints: [
                        {
                            x: sourceShape.bounds.x + (sourceShape.bounds.width / 2),
                            y: sourceShape.bounds.y + (sourceShape.bounds.height / 2),
                        },
                        {
                            x: targetShape.bounds.x + (targetShape.bounds.width / 2),
                            y: targetShape.bounds.y + (targetShape.bounds.height / 2),
                        },
                    ],
                })
            }
        })

        return {
            id: 'BPMNDiagram_1',
            plane: {
                id: 'BPMNPlane_1',
                bpmnElement: process.id,
                shapes,
                edges,
            },
        }
    }

    /**
     * Generates BPMN 2.0 compliant XML from definitions.
     *
     * @param definitions - BPMN definitions object
     * @returns BPMN 2.0 XML string
     */
    private static generateBpmnXml(definitions: BpmnDefinitions): string {
        const lines: string[] = []

        // XML declaration
        lines.push('<?xml version="1.0" encoding="UTF-8"?>')

        // Definitions element with namespaces
        lines.push(
            `<bpmn:definitions xmlns:bpmn="${BPMN_NAMESPACES.bpmn}" ` +
            `xmlns:bpmndi="${BPMN_NAMESPACES.bpmndi}" ` +
            `xmlns:dc="${BPMN_NAMESPACES.dc}" ` +
            `xmlns:di="${BPMN_NAMESPACES.di}" ` +
            `xmlns:xsi="${BPMN_NAMESPACES.xsi}" ` +
            `id="${definitions.id}" ` +
            `targetNamespace="${definitions.targetNamespace}">`,
        )

        // Process element
        const process = definitions.process
        const executableAttr = process.isExecutable === undefined ? '' : ` isExecutable="${process.isExecutable}"`
        lines.push(`  <bpmn:process id="${process.id}" name="${BpmnExporter.escapeXml(process.name)}"${executableAttr}>`)

        // Lane set
        if (process.laneSet) {
            lines.push(`    <bpmn:laneSet id="${process.laneSet.id}">`)
            process.laneSet.lanes.forEach((lane) => {
                lines.push(`      <bpmn:lane id="${lane.id}" name="${BpmnExporter.escapeXml(lane.name)}">`)
                lane.flowNodeRefs.forEach((ref) => {
                    lines.push(`        <bpmn:flowNodeRef>${ref}</bpmn:flowNodeRef>`)
                })
                lines.push('      </bpmn:lane>')
            })
            lines.push('    </bpmn:laneSet>')
        }

        // Start events
        process.startEvents.forEach((event) => {
            const nameAttr = event.name ? ` name="${BpmnExporter.escapeXml(event.name)}"` : ''
            lines.push(`    <bpmn:startEvent id="${event.id}"${nameAttr}>`)
            event.outgoing.forEach((flowId) => {
                lines.push(`      <bpmn:outgoing>${flowId}</bpmn:outgoing>`)
            })
            lines.push('    </bpmn:startEvent>')
        })

        // Tasks
        process.tasks.forEach((task) => {
            lines.push(`    <bpmn:${task.type} id="${task.id}" name="${BpmnExporter.escapeXml(task.name)}">`)
            task.incoming.forEach((flowId) => {
                lines.push(`      <bpmn:incoming>${flowId}</bpmn:incoming>`)
            })
            task.outgoing.forEach((flowId) => {
                lines.push(`      <bpmn:outgoing>${flowId}</bpmn:outgoing>`)
            })
            lines.push(`    </bpmn:${task.type}>`)
        })

        // End events
        process.endEvents.forEach((event) => {
            const nameAttr = event.name ? ` name="${BpmnExporter.escapeXml(event.name)}"` : ''
            lines.push(`    <bpmn:endEvent id="${event.id}"${nameAttr}>`)
            event.incoming.forEach((flowId) => {
                lines.push(`      <bpmn:incoming>${flowId}</bpmn:incoming>`)
            })
            lines.push('    </bpmn:endEvent>')
        })

        // Sequence flows
        process.sequenceFlows.forEach((flow) => {
            const nameAttr = flow.name ? ` name="${BpmnExporter.escapeXml(flow.name)}"` : ''
            lines.push(
                `    <bpmn:sequenceFlow id="${flow.id}"${nameAttr} ` +
                `sourceRef="${flow.sourceRef}" targetRef="${flow.targetRef}" />`,
            )
        })

        lines.push('  </bpmn:process>')

        // BPMN Diagram
        if (definitions.diagram) {
            const diagram = definitions.diagram
            lines.push(`  <bpmndi:BPMNDiagram id="${diagram.id}">`)
            lines.push(`    <bpmndi:BPMNPlane id="${diagram.plane.id}" bpmnElement="${diagram.plane.bpmnElement}">`)

            // Shapes
            diagram.plane.shapes.forEach((shape) => {
                const horizontalAttr = shape.isHorizontal === undefined ? '' : ` isHorizontal="${shape.isHorizontal}"`
                lines.push(`      <bpmndi:BPMNShape id="${shape.id}" bpmnElement="${shape.bpmnElement}"${horizontalAttr}>`)
                lines.push(
                    `        <dc:Bounds x="${shape.bounds.x}" y="${shape.bounds.y}" ` +
                    `width="${shape.bounds.width}" height="${shape.bounds.height}" />`,
                )
                lines.push('      </bpmndi:BPMNShape>')
            })

            // Edges
            diagram.plane.edges.forEach((edge) => {
                lines.push(`      <bpmndi:BPMNEdge id="${edge.id}" bpmnElement="${edge.bpmnElement}">`)
                edge.waypoints.forEach((point) => {
                    lines.push(`        <di:waypoint x="${point.x}" y="${point.y}" />`)
                })
                lines.push('      </bpmndi:BPMNEdge>')
            })

            lines.push('    </bpmndi:BPMNPlane>')
            lines.push('  </bpmndi:BPMNDiagram>')
        }

        lines.push('</bpmn:definitions>')

        return lines.join('\n')
    }

    /**
     * Downloads the BPMN XML file.
     *
     * @param xml - The BPMN XML string
     * @param boardTitle - The board title for filename
     */
    private static downloadBpmn(xml: string, boardTitle: string): void {
        const blob = new Blob([xml], {type: 'application/xml'})

        const link = document.createElement('a')
        link.style.display = 'none'

        const filename = `${Utils.sanitizeFilename(boardTitle)}.bpmn`
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

export {BpmnExporter}
