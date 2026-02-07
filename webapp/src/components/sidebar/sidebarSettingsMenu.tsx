// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.
import React, {useState} from 'react'
import {FormattedMessage, useIntl} from 'react-intl'

import {Archiver} from '../../archiver'
import {JsonImporter} from '../../importers/jsonImporter'
import {JsonExporter} from '../../exporters/jsonExporter'
import {XmlImporter} from '../../importers/xmlImporter'
import {XmlExporter} from '../../exporters/xmlExporter'
import {getCurrentBoard} from '../../store/boards'
import {getCurrentBoardViews} from '../../store/views'
import {getCards} from '../../store/cards'
import {getContents} from '../../store/contents'
import {Block} from '../../blocks/block'
import {
    darkTheme,
    darkThemeName,
    defaultTheme,
    defaultThemeName,
    lightTheme,
    lightThemeName,
    setTheme, systemThemeName,
    Theme,
} from '../../theme'
import Menu from '../../widgets/menu'
import MenuWrapper from '../../widgets/menuWrapper'
import {useAppDispatch, useAppSelector} from '../../store/hooks'
import {storeLanguage} from '../../store/language'
import {getCurrentTeam, Team} from '../../store/teams'
import {UserSettings} from '../../userSettings'

import './sidebarSettingsMenu.scss'
import CheckIcon from '../../widgets/icons/check'
import {Constants} from '../../constants'

import TelemetryClient, {TelemetryCategory, TelemetryActions} from '../../telemetry/telemetryClient'

type Props = {
    activeTheme: string
}

const SidebarSettingsMenu = (props: Props) => {
    const intl = useIntl()
    const dispatch = useAppDispatch()
    const currentTeam = useAppSelector<Team|null>(getCurrentTeam)
    const currentBoard = useAppSelector(getCurrentBoard)
    const views = useAppSelector(getCurrentBoardViews)
    const allCards = useAppSelector(getCards)
    const contents = useAppSelector(getContents)

    // we need this as the sidebar doesn't always need to re-render
    // on theme change. This can cause props and the actual
    // active theme can go out of sync
    const [themeName, setThemeName] = useState(props.activeTheme)

    const updateTheme = (theme: Theme | null, name: string) => {
        setTheme(theme)
        setThemeName(name)
    }

    const [randomIcons, setRandomIcons] = useState(UserSettings.prefillRandomIcons)
    const toggleRandomIcons = () => {
        UserSettings.prefillRandomIcons = !UserSettings.prefillRandomIcons
        setRandomIcons(!randomIcons)
    }

    const themes = [
        {
            id: defaultThemeName,
            displayName: 'Default theme',
            theme: defaultTheme,
        },
        {
            id: darkThemeName,
            displayName: 'Dark theme',
            theme: darkTheme,
        },
        {
            id: lightThemeName,
            displayName: 'Light theme',
            theme: lightTheme,
        },
        {
            id: systemThemeName,
            displayName: 'System theme',
            theme: null,
        },
    ]

    return (
        <div className='SidebarSettingsMenu'>
            <MenuWrapper>
                <div className='menu-entry'>
                    <FormattedMessage
                        id='Sidebar.settings'
                        defaultMessage='Settings'
                    />
                </div>
                <Menu position='top'>
                    <Menu.SubMenu
                        id='import'
                        name={intl.formatMessage({id: 'Sidebar.import', defaultMessage: 'Import'})}
                        position='top'
                    >
                        <Menu.Text
                            id='import_archive'
                            name={intl.formatMessage({id: 'Sidebar.import-archive', defaultMessage: 'Import archive'})}
                            onClick={async () => {
                                TelemetryClient.trackEvent(TelemetryCategory, TelemetryActions.ImportArchive)
                                Archiver.importFullArchive()
                            }}
                        />
                        <Menu.Text
                            id='import_json'
                            name={intl.formatMessage({id: 'Sidebar.import-json', defaultMessage: 'Import JSON'})}
                            onClick={async () => {
                                TelemetryClient.trackEvent(TelemetryCategory, TelemetryActions.ImportJson)
                                JsonImporter.importBoardJson((result) => {
                                    if (result.success) {
                                        // Reload to show the imported board
                                        window.location.reload()
                                    }
                                })
                            }}
                        />
                        <Menu.Text
                            id='import_xml'
                            name={intl.formatMessage({id: 'Sidebar.import-xml', defaultMessage: 'Import XML'})}
                            onClick={async () => {
                                TelemetryClient.trackEvent(TelemetryCategory, TelemetryActions.ImportXml)
                                XmlImporter.importBoardXml((result) => {
                                    if (result.success) {
                                        window.location.reload()
                                    }
                                })
                            }}
                        />
                        {
                            Constants.imports.map((i) => (
                                <Menu.Text
                                    key={`${i.id}-import`}
                                    id={`${i.id}-import`}
                                    name={i.displayName}
                                    onClick={() => {
                                        TelemetryClient.trackEvent(TelemetryCategory, i.telemetryName)
                                        window.open(i.href)
                                    }}
                                />
                            ))
                        }
                    </Menu.SubMenu>
                    <Menu.SubMenu
                        id='export'
                        name={intl.formatMessage({id: 'Sidebar.export', defaultMessage: 'Export'})}
                        position='top'
                    >
                        <Menu.Text
                            id='export_archive'
                            name={intl.formatMessage({id: 'Sidebar.export-archive', defaultMessage: 'Export archive'})}
                            onClick={async () => {
                                if (currentTeam) {
                                    TelemetryClient.trackEvent(TelemetryCategory, TelemetryActions.ExportArchive)
                                    Archiver.exportFullArchive(currentTeam.id)
                                }
                            }}
                        />
                        {currentBoard &&
                            <Menu.Text
                                id='export_json'
                                name={intl.formatMessage({id: 'Sidebar.export-json', defaultMessage: 'Export JSON'})}
                                onClick={async () => {
                                    TelemetryClient.trackEvent(TelemetryCategory, TelemetryActions.ExportJson)
                                    const cards = Object.values(allCards).filter((card) => card.boardId === currentBoard.id)
                                    JsonExporter.exportBoardJson(currentBoard, views, cards, contents as Block[])
                                }}
                            />
                        }
                        {currentBoard &&
                            <Menu.Text
                                id='export_xml'
                                name={intl.formatMessage({id: 'Sidebar.export-xml', defaultMessage: 'Export XML'})}
                                onClick={async () => {
                                    TelemetryClient.trackEvent(TelemetryCategory, TelemetryActions.ExportXml)
                                    const cards = Object.values(allCards).filter((card) => card.boardId === currentBoard.id)
                                    XmlExporter.exportBoardXml(currentBoard, views, cards, contents as Block[])
                                }}
                            />
                        }
                    </Menu.SubMenu>
                    <Menu.SubMenu
                        id='lang'
                        name={intl.formatMessage({id: 'Sidebar.set-language', defaultMessage: 'Set language'})}
                        position='top'
                    >
                        {
                            Constants.languages.map((language) => (
                                <Menu.Text
                                    key={language.code}
                                    id={`${language.name}-lang`}
                                    name={language.displayName}
                                    onClick={async () => dispatch(storeLanguage(language.code))}
                                    rightIcon={intl.locale.toLowerCase() === language.code ? <CheckIcon/> : null}
                                />
                            ))
                        }
                    </Menu.SubMenu>
                    <Menu.SubMenu
                        id='theme'
                        name={intl.formatMessage({id: 'Sidebar.set-theme', defaultMessage: 'Set theme'})}
                        position='top'
                    >
                        {
                            themes.map((theme) =>
                                (
                                    <Menu.Text
                                        key={theme.id}
                                        id={theme.id}
                                        name={intl.formatMessage({id: `Sidebar.${theme.id}`, defaultMessage: theme.displayName})}
                                        onClick={async () => updateTheme(theme.theme, theme.id)}
                                        rightIcon={themeName === theme.id ? <CheckIcon/> : null}
                                    />
                                ),
                            )
                        }
                    </Menu.SubMenu>
                    <Menu.Switch
                        id='random-icons'
                        name={intl.formatMessage({id: 'Sidebar.random-icons', defaultMessage: 'Random icons'})}
                        isOn={randomIcons}
                        onClick={async () => toggleRandomIcons()}
                        suppressItemClicked={true}
                    />
                </Menu>
            </MenuWrapper>
        </div>
    )
}

export default React.memo(SidebarSettingsMenu)
