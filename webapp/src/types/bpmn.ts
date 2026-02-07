// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.
// BPMN 2.0 Type Definitions for BACON-AI

/**
 * BPMN 2.0 Definitions - Root element of a BPMN document
 */
export interface BpmnDefinitions {
    id: string
    targetNamespace: string
    process: BpmnProcess
    diagram?: BpmnDiagram
}

/**
 * BPMN Process - Contains all flow elements
 */
export interface BpmnProcess {
    id: string
    name: string
    isExecutable?: boolean
    laneSet?: BpmnLaneSet
    startEvents: BpmnStartEvent[]
    endEvents: BpmnEndEvent[]
    tasks: BpmnTask[]
    sequenceFlows: BpmnSequenceFlow[]
}

/**
 * BPMN Lane Set - Container for swimlanes
 */
export interface BpmnLaneSet {
    id: string
    lanes: BpmnLane[]
}

/**
 * BPMN Lane - Swimlane representing a status/phase
 */
export interface BpmnLane {
    id: string
    name: string
    flowNodeRefs: string[]
    optionId?: string // Reference to board status property option
}

/**
 * BPMN Task - User task representing a card
 */
export interface BpmnTask {
    id: string
    name: string
    type: 'userTask' | 'task' | 'serviceTask' | 'scriptTask'
    laneRef?: string
    incoming: string[]
    outgoing: string[]
    cardId?: string // Reference back to original card
}

/**
 * BPMN Start Event
 */
export interface BpmnStartEvent {
    id: string
    name?: string
    outgoing: string[]
}

/**
 * BPMN End Event
 */
export interface BpmnEndEvent {
    id: string
    name?: string
    incoming: string[]
}

/**
 * BPMN Sequence Flow - Connection between flow elements
 */
export interface BpmnSequenceFlow {
    id: string
    name?: string
    sourceRef: string
    targetRef: string
}

/**
 * BPMN Diagram - Visual representation
 */
export interface BpmnDiagram {
    id: string
    plane: BpmnPlane
}

/**
 * BPMN Plane - Contains all diagram shapes
 */
export interface BpmnPlane {
    id: string
    bpmnElement: string
    shapes: BpmnShape[]
    edges: BpmnEdge[]
}

/**
 * BPMN Shape - Visual representation of a flow element
 */
export interface BpmnShape {
    id: string
    bpmnElement: string
    bounds: BpmnBounds
    isHorizontal?: boolean
}

/**
 * BPMN Edge - Visual representation of a sequence flow
 */
export interface BpmnEdge {
    id: string
    bpmnElement: string
    waypoints: BpmnPoint[]
}

/**
 * BPMN Bounds - Rectangle dimensions
 */
export interface BpmnBounds {
    x: number
    y: number
    width: number
    height: number
}

/**
 * BPMN Point - 2D coordinate
 */
export interface BpmnPoint {
    x: number
    y: number
}

/**
 * Configuration for BPMN export mapping
 */
export interface BpmnMappingConfig {
    statusPropertyId: string // Which property represents status columns
    startStates: string[] // Option IDs for "start" states
    endStates: string[] // Option IDs for "end" states
    dependencyPropertyId?: string // Optional dependency property for sequence flows
}

/**
 * BPMN XML namespaces
 */
export const BPMN_NAMESPACES = {
    bpmn: 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    bpmndi: 'http://www.omg.org/spec/BPMN/20100524/DI',
    dc: 'http://www.omg.org/spec/DD/20100524/DC',
    di: 'http://www.omg.org/spec/DD/20100524/DI',
    xsi: 'http://www.w3.org/2001/XMLSchema-instance',
} as const
