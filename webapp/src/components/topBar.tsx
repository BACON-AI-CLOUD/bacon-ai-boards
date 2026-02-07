// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.

import React from 'react'

import './topBar.scss'
import {FormattedMessage} from 'react-intl'

import HelpIcon from '../widgets/icons/help'

const TopBar = (): JSX.Element => {
    const feedbackUrl = 'mailto:hello@bacon-ai.cloud?subject=BACON-AI%20Feedback'
    return (
        <div
            className='TopBar'
        >
            <a
                className='link'
                href={feedbackUrl}
                target='_blank'
                rel='noreferrer'
            >
                <FormattedMessage
                    id='TopBar.give-feedback'
                    defaultMessage='Give feedback'
                />
            </a>
            <a
                href='https://bacon-ai.cloud/docs/boards?utm_source=webapp'
                target='_blank'
                rel='noreferrer'
            >
                <HelpIcon/>
            </a>
        </div>
    )
}

export default React.memo(TopBar)
