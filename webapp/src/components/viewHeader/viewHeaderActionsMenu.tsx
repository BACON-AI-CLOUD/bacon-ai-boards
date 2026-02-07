// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.
import React, {useState} from 'react'
import {useIntl, IntlShape} from 'react-intl'

import {CsvExporter} from '../../csvExporter'
import {JsonExporter} from '../../exporters/jsonExporter'
import {XmlExporter} from '../../exporters/xmlExporter'
import {BpmnExporter} from '../../exporters/bpmnExporter'
import {Archiver} from '../../archiver'
import {BpmnMappingConfig} from '../../types/bpmn'
import BpmnExportDialog from '../dialog/bpmnExportDialog'
import {Block} from '../../blocks/block'
import {Board} from '../../blocks/board'
import {BoardView} from '../../blocks/boardView'
import {Card} from '../../blocks/card'
import IconButton from '../../widgets/buttons/iconButton'
import OptionsIcon from '../../widgets/icons/options'
import Menu from '../../widgets/menu'
import MenuWrapper from '../../widgets/menuWrapper'
import {Utils} from '../../utils'
import {useAppSelector} from '../../store/hooks'
import {getContents} from '../../store/contents'
import {getCurrentBoardViews} from '../../store/views'

import ModalWrapper from '../modalWrapper'
import {sendFlashMessage} from '../flashMessages'

type Props = {
    board: Board
    activeView: BoardView
    cards: Card[]
}

// import {mutator} from '../../mutator'
// import {CardFilter} from '../../cardFilter'
// import {BlockIcons} from '../../blockIcons'
// async function testAddCards(board: Board, activeView: BoardView, startCount: number, count: number) {
//     let optionIndex = 0

//     mutator.performAsUndoGroup(async () => {
//         for (let i = 0; i < count; i++) {
//             const card = new Card()
//             card.parentId = board.id
//             card.boardId = board.boardId
//             card.fields.properties = CardFilter.propertiesThatMeetFilterGroup(activeView.fields.filter, board.cardProperties)
//             card.title = `Test Card ${startCount + i + 1}`
//             card.fields.icon = BlockIcons.shared.randomIcon()

//             const groupByProperty = board.cardProperties.find((o) => o.id === activeView.fields.groupById)
//             if (groupByProperty && groupByProperty.options.length > 0) {
//                 // Cycle through options
//                 const option = groupByProperty.options[optionIndex]
//                 optionIndex = (optionIndex + 1) % groupByProperty.options.length
//                 card.fields.properties[groupByProperty.id] = option.id
//             }
//             mutator.insertBlock(card, 'test add card')
//         }
//     })
// }

// async function testDistributeCards(boardTree: BoardTree) {
//     mutator.performAsUndoGroup(async () => {
//         let optionIndex = 0
//         for (const card of boardTree.cards) {
//             if (boardTree.groupByProperty && boardTree.groupByProperty.options.length > 0) {
//                 // Cycle through options
//                 const option = boardTree.groupByProperty.options[optionIndex]
//                 optionIndex = (optionIndex + 1) % boardTree.groupByProperty.options.length
//                 const newCard = new Card(card)
//                 if (newCard.properties[boardTree.groupByProperty.id] !== option.id) {
//                     newCard.properties[boardTree.groupByProperty.id] = option.id
//                     mutator.updateBlock(newCard, card, 'test distribute cards')
//                 }
//             }
//         }
//     })
// }

// async function testRandomizeIcons(boardTree: BoardTree) {
//     mutator.performAsUndoGroup(async () => {
//         for (const card of boardTree.cards) {
//             mutator.changeIcon(card.id, card.fields.icon, BlockIcons.shared.randomIcon(), 'randomize icon')
//         }
//     })
// }

function onExportCsvTrigger(board: Board, activeView: BoardView, cards: Card[], intl: IntlShape) {
    try {
        CsvExporter.exportTableCsv(board, activeView, cards, intl)
        const exportCompleteMessage = intl.formatMessage({
            id: 'ViewHeader.export-complete',
            defaultMessage: 'Export complete!',
        })
        sendFlashMessage({content: exportCompleteMessage, severity: 'normal'})
    } catch (e) {
        Utils.logError(`ExportCSV ERROR: ${e}`)
        const exportFailedMessage = intl.formatMessage({
            id: 'ViewHeader.export-failed',
            defaultMessage: 'Export failed!',
        })
        sendFlashMessage({content: exportFailedMessage, severity: 'high'})
    }
}

function onExportJsonTrigger(board: Board, views: BoardView[], cards: Card[], blocks: Block[], intl: IntlShape) {
    try {
        JsonExporter.exportBoardJson(board, views, cards, blocks)
        const exportCompleteMessage = intl.formatMessage({
            id: 'ViewHeader.export-complete',
            defaultMessage: 'Export complete!',
        })
        sendFlashMessage({content: exportCompleteMessage, severity: 'normal'})
    } catch (e) {
        Utils.logError(`ExportJSON ERROR: ${e}`)
        const exportFailedMessage = intl.formatMessage({
            id: 'ViewHeader.export-failed',
            defaultMessage: 'Export failed!',
        })
        sendFlashMessage({content: exportFailedMessage, severity: 'high'})
    }
}

function onExportXmlTrigger(board: Board, views: BoardView[], cards: Card[], blocks: Block[], intl: IntlShape) {
    try {
        XmlExporter.exportBoardXml(board, views, cards, blocks)
        const exportCompleteMessage = intl.formatMessage({
            id: 'ViewHeader.export-complete',
            defaultMessage: 'Export complete!',
        })
        sendFlashMessage({content: exportCompleteMessage, severity: 'normal'})
    } catch (e) {
        Utils.logError(`ExportXML ERROR: ${e}`)
        const exportFailedMessage = intl.formatMessage({
            id: 'ViewHeader.export-failed',
            defaultMessage: 'Export failed!',
        })
        sendFlashMessage({content: exportFailedMessage, severity: 'high'})
    }
}

const ViewHeaderActionsMenu = (props: Props) => {
    const {board, activeView, cards} = props
    const intl = useIntl()
    const contents = useAppSelector(getContents)
    const views = useAppSelector(getCurrentBoardViews)
    const [showBpmnExportDialog, setShowBpmnExportDialog] = useState(false)

    return (
        <ModalWrapper>
            <MenuWrapper label={intl.formatMessage({id: 'ViewHeader.view-header-menu', defaultMessage: 'View header menu'})}>
                <IconButton icon={<OptionsIcon/>}/>
                <Menu position='left'>
                    <Menu.Text
                        id='exportCsv'
                        name={intl.formatMessage({id: 'ViewHeader.export-csv', defaultMessage: 'Export to CSV'})}
                        onClick={() => onExportCsvTrigger(board, activeView, cards, intl)}
                    />
                    <Menu.Text
                        id='exportJson'
                        name={intl.formatMessage({id: 'ViewHeader.export-json', defaultMessage: 'Export to JSON'})}
                        onClick={() => onExportJsonTrigger(board, views, cards, contents as Block[], intl)}
                    />
                    <Menu.Text
                        id='exportXml'
                        name={intl.formatMessage({id: 'ViewHeader.export-xml', defaultMessage: 'Export to XML'})}
                        onClick={() => onExportXmlTrigger(board, views, cards, contents as Block[], intl)}
                    />
                    <Menu.Text
                        id='exportBpmn'
                        name={intl.formatMessage({id: 'ViewHeader.export-bpmn', defaultMessage: 'Export to BPMN'})}
                        onClick={() => setShowBpmnExportDialog(true)}
                    />
                    <Menu.Text
                        id='exportBoardArchive'
                        name={intl.formatMessage({id: 'ViewHeader.export-board-archive', defaultMessage: 'Export board archive'})}
                        onClick={() => Archiver.exportBoardArchive(board)}
                    />
                    {/*
                    <Menu.Separator/>

                    <Menu.Text
                        id='testAdd100Cards'
                        name={intl.formatMessage({id: 'ViewHeader.test-add-100-cards', defaultMessage: 'TEST: Add 100 cards'})}
                        onClick={() => testAddCards(board, activeView, cards.length, 100)}
                    />
                    <Menu.Text
                        id='testAdd1000Cards'
                        name={intl.formatMessage({id: 'ViewHeader.test-add-1000-cards', defaultMessage: 'TEST: Add 1,000 cards'})}
                        onClick={() => testAddCards(board, activeView, cards.length, 1000)}
                    />
                    <Menu.Text
                        id='testDistributeCards'
                        name={intl.formatMessage({id: 'ViewHeader.test-distribute-cards', defaultMessage: 'TEST: Distribute cards'})}
                        onClick={() => testDistributeCards()}
                    />
                    <Menu.Text
                        id='testRandomizeIcons'
                        name={intl.formatMessage({id: 'ViewHeader.test-randomize-icons', defaultMessage: 'TEST: Randomize icons'})}
                        onClick={() => testRandomizeIcons()}
                    />
                    */}
                </Menu>
            </MenuWrapper>
            {showBpmnExportDialog && (
                <BpmnExportDialog
                    board={board}
                    cards={cards}
                    onClose={() => setShowBpmnExportDialog(false)}
                    onExport={(config: BpmnMappingConfig) => {
                        try {
                            BpmnExporter.exportBoardBpmn(board, cards, config)
                            const exportCompleteMessage = intl.formatMessage({
                                id: 'ViewHeader.export-complete',
                                defaultMessage: 'Export complete!',
                            })
                            sendFlashMessage({content: exportCompleteMessage, severity: 'normal'})
                        } catch (e) {
                            Utils.logError(`ExportBPMN ERROR: ${e}`)
                            const exportFailedMessage = intl.formatMessage({
                                id: 'ViewHeader.export-failed',
                                defaultMessage: 'Export failed!',
                            })
                            sendFlashMessage({content: exportFailedMessage, severity: 'high'})
                        }
                        setShowBpmnExportDialog(false)
                    }}
                />
            )}
        </ModalWrapper>
    )
}

export default React.memo(ViewHeaderActionsMenu)
