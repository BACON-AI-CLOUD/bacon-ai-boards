// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.
import React, {useState, useEffect, useMemo} from 'react'
import {useIntl} from 'react-intl'

import {Board} from '../../blocks/board'
import {Card} from '../../blocks/card'
import {BpmnMappingConfig} from '../../types/bpmn'
import Dialog from '../dialog'
import Button from '../../widgets/buttons/button'

import './bpmnExportDialog.scss'

interface BpmnExportDialogProps {
    board: Board
    cards: Card[]
    onClose: () => void
    onExport: (config: BpmnMappingConfig) => void
}

const BpmnExportDialog = (props: BpmnExportDialogProps): JSX.Element => {
    const {board, cards, onClose, onExport} = props
    const intl = useIntl()

    // Find all select-type properties
    const selectProperties = useMemo(() => {
        return board.cardProperties.filter((prop) => prop.type === 'select')
    }, [board.cardProperties])

    // State for selected configuration
    const [statusPropertyId, setStatusPropertyId] = useState<string>('')
    const [startStates, setStartStates] = useState<Set<string>>(new Set())
    const [endStates, setEndStates] = useState<Set<string>>(new Set())
    const [dependencyPropertyId] = useState<string>('')

    // Initialize with first select property
    useEffect(() => {
        if (selectProperties.length > 0 && !statusPropertyId) {
            const firstProperty = selectProperties[0]
            setStatusPropertyId(firstProperty.id)

            // Auto-select first option as start state
            if (firstProperty.options.length > 0) {
                setStartStates(new Set([firstProperty.options[0].id]))
            }

            // Auto-select last option as end state
            if (firstProperty.options.length > 1) {
                setEndStates(new Set([firstProperty.options[firstProperty.options.length - 1].id]))
            }
        }
    }, [selectProperties, statusPropertyId])

    // Get current status property
    const currentStatusProperty = useMemo(() => {
        return board.cardProperties.find((prop) => prop.id === statusPropertyId)
    }, [board.cardProperties, statusPropertyId])

    // Calculate cards per lane
    const cardsPerLane = useMemo(() => {
        if (!currentStatusProperty) {
            return new Map<string, number>()
        }

        const counts = new Map<string, number>()

        // Initialize all options with 0
        currentStatusProperty.options.forEach((opt) => {
            counts.set(opt.id, 0)
        })

        // Count cards per status
        cards.forEach((card) => {
            const statusValue = card.fields.properties[statusPropertyId]
            if (typeof statusValue === 'string') {
                counts.set(statusValue, (counts.get(statusValue) || 0) + 1)
            }
        })

        return counts
    }, [cards, statusPropertyId, currentStatusProperty])

    // Toggle state selection
    const toggleStartState = (optionId: string) => {
        const newStates = new Set(startStates)
        if (newStates.has(optionId)) {
            newStates.delete(optionId)
        } else {
            newStates.add(optionId)
        }
        setStartStates(newStates)
    }

    const toggleEndState = (optionId: string) => {
        const newStates = new Set(endStates)
        if (newStates.has(optionId)) {
            newStates.delete(optionId)
        } else {
            newStates.add(optionId)
        }
        setEndStates(newStates)
    }

    // Validation
    const isValid = useMemo(() => {
        return statusPropertyId !== '' &&
               startStates.size > 0 &&
               endStates.size > 0
    }, [statusPropertyId, startStates.size, endStates.size])

    // Handle export
    const handleExport = () => {
        if (!isValid) {
            return
        }

        const config: BpmnMappingConfig = {
            statusPropertyId,
            startStates: Array.from(startStates),
            endStates: Array.from(endStates),
            dependencyPropertyId: dependencyPropertyId || undefined,
        }

        onExport(config)
    }

    return (
        <Dialog
            onClose={onClose}
            size='medium'
            title={
                <span>
                    {intl.formatMessage({
                        id: 'BpmnExport.title',
                        defaultMessage: 'Export as BPMN',
                    })}
                </span>
            }
        >
            <div className='BpmnExportDialog'>
                <div className='dialog-body'>
                    {/* Status Property Selector */}
                    <div className='form-group'>
                        <label htmlFor='status-property'>
                            {intl.formatMessage({
                                id: 'BpmnExport.statusProperty',
                                defaultMessage: 'Status Property (Swimlanes)',
                            })}
                        </label>
                        <select
                            id='status-property'
                            value={statusPropertyId}
                            onChange={(e) => {
                                setStatusPropertyId(e.target.value)
                                setStartStates(new Set())
                                setEndStates(new Set())
                            }}
                            className='form-control'
                        >
                            {selectProperties.length === 0 && (
                                <option value=''>
                                    {intl.formatMessage({
                                        id: 'BpmnExport.noSelectProperties',
                                        defaultMessage: 'No select properties available',
                                    })}
                                </option>
                            )}
                            {selectProperties.map((prop) => (
                                <option
                                    key={prop.id}
                                    value={prop.id}
                                >
                                    {prop.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Status Options */}
                    {currentStatusProperty && currentStatusProperty.options.length > 0 && (
                        <div className='form-group'>
                            <label>
                                {intl.formatMessage({
                                    id: 'BpmnExport.configureStates',
                                    defaultMessage: 'Configure States',
                                })}
                            </label>
                            <div className='state-options'>
                                <table className='state-table'>
                                    <thead>
                                        <tr>
                                            <th>
                                                {intl.formatMessage({
                                                    id: 'BpmnExport.statusColumn',
                                                    defaultMessage: 'Status',
                                                })}
                                            </th>
                                            <th>
                                                {intl.formatMessage({
                                                    id: 'BpmnExport.cardsColumn',
                                                    defaultMessage: 'Cards',
                                                })}
                                            </th>
                                            <th>
                                                {intl.formatMessage({
                                                    id: 'BpmnExport.startStateColumn',
                                                    defaultMessage: 'Start State',
                                                })}
                                            </th>
                                            <th>
                                                {intl.formatMessage({
                                                    id: 'BpmnExport.endStateColumn',
                                                    defaultMessage: 'End State',
                                                })}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentStatusProperty.options.map((option) => (
                                            <tr key={option.id}>
                                                <td>
                                                    <div className='status-label'>
                                                        <span
                                                            className='status-color'
                                                            style={{backgroundColor: option.color}}
                                                        />
                                                        <span>{option.value}</span>
                                                    </div>
                                                </td>
                                                <td className='card-count'>
                                                    {cardsPerLane.get(option.id) || 0}
                                                </td>
                                                <td className='checkbox-cell'>
                                                    <input
                                                        type='checkbox'
                                                        checked={startStates.has(option.id)}
                                                        onChange={() => toggleStartState(option.id)}
                                                    />
                                                </td>
                                                <td className='checkbox-cell'>
                                                    <input
                                                        type='checkbox'
                                                        checked={endStates.has(option.id)}
                                                        onChange={() => toggleEndState(option.id)}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Validation Messages */}
                    {statusPropertyId && startStates.size === 0 && (
                        <div className='validation-message warning'>
                            {intl.formatMessage({
                                id: 'BpmnExport.selectStartState',
                                defaultMessage: 'Please select at least one start state',
                            })}
                        </div>
                    )}
                    {statusPropertyId && endStates.size === 0 && (
                        <div className='validation-message warning'>
                            {intl.formatMessage({
                                id: 'BpmnExport.selectEndState',
                                defaultMessage: 'Please select at least one end state',
                            })}
                        </div>
                    )}

                    {/* Summary */}
                    {isValid && (
                        <div className='export-summary'>
                            {intl.formatMessage({
                                id: 'BpmnExport.summary',
                                defaultMessage: 'Ready to export {cardCount} cards across {laneCount} swimlanes',
                            }, {
                                cardCount: cards.length,
                                laneCount: currentStatusProperty?.options.length || 0,
                            })}
                        </div>
                    )}
                </div>

                <div className='dialog-footer'>
                    <Button onClick={onClose}>
                        {intl.formatMessage({
                            id: 'BpmnExport.cancel',
                            defaultMessage: 'Cancel',
                        })}
                    </Button>
                    <Button
                        filled={true}
                        onClick={handleExport}
                        disabled={!isValid}
                    >
                        {intl.formatMessage({
                            id: 'BpmnExport.export',
                            defaultMessage: 'Export BPMN',
                        })}
                    </Button>
                </div>
            </div>
        </Dialog>
    )
}

export default React.memo(BpmnExportDialog)
