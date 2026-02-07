// Copyright (c) 2015-present Mattermost, Inc. All Rights Reserved.
// See LICENSE.txt for license information.
// Modified for BACON-AI

import React from 'react'

import './focalboard_logo.scss'

export default function FocalboardLogoIcon(): JSX.Element {
    return (
        <svg
            className='FocalboardLogoIcon Icon'
            version='1.1'
            x='0px'
            y='0px'
            viewBox='0 0 64 64'
        >
            {/* BACON-AI Logo - A! in circle representing AI */}

            {/* Outer circle - main container */}
            <circle
                cx='32'
                cy='32'
                r='29'
                fill='none'
                stroke='currentColor'
                strokeWidth='3'
                opacity='0.9'
            />

            {/* Inner subtle fill */}
            <circle
                cx='32'
                cy='32'
                r='26'
                fill='currentColor'
                opacity='0.08'
            />

            {/* Letter A - clean triangular design */}
            <path
                d='M15 50 L28 14 L32 14 L32 50 L27 50 L27 40 L20 40 L17 50 Z'
                fill='currentColor'
            />
            {/* A crossbar cutout */}
            <path
                d='M22 35 L27 35 L27 26 Z'
                fill='currentColor'
                opacity='0.15'
            />

            {/* Exclamation mark - the "I" in AI */}
            {/* Main stem with rounded ends */}
            <rect
                x='38'
                y='14'
                width='8'
                height='24'
                rx='4'
                fill='currentColor'
            />

            {/* Exclamation dot */}
            <circle
                cx='42'
                cy='46'
                r='5'
                fill='currentColor'
            />

            {/* Subtle orbital ring accent */}
            <ellipse
                cx='32'
                cy='32'
                rx='22'
                ry='8'
                fill='none'
                stroke='currentColor'
                strokeWidth='1'
                opacity='0.2'
                transform='rotate(-20 32 32)'
            />
        </svg>
    )
}
