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
            {/* BACON-AI Logo - Stylized B with Kanban grid */}
            {/* Outer rounded square background */}
            <rect
                x='4'
                y='4'
                width='56'
                height='56'
                rx='8'
                ry='8'
                fill='currentColor'
                opacity='0.15'
            />
            {/* Letter B - left stem */}
            <rect
                x='16'
                y='12'
                width='8'
                height='40'
                rx='2'
                fill='currentColor'
            />
            {/* Letter B - top bump */}
            <path
                d='M24 12 h12 c6 0 10 4 10 9 c0 5 -4 9 -10 9 h-12 v-18 z'
                fill='currentColor'
            />
            {/* Letter B - bottom bump (larger) */}
            <path
                d='M24 30 h14 c7 0 12 5 12 11 c0 6 -5 11 -12 11 h-14 v-22 z'
                fill='currentColor'
            />
            {/* Kanban column lines inside B */}
            <rect
                x='28'
                y='16'
                width='2'
                height='10'
                rx='1'
                fill='currentColor'
                opacity='0.3'
            />
            <rect
                x='34'
                y='16'
                width='2'
                height='10'
                rx='1'
                fill='currentColor'
                opacity='0.3'
            />
            <rect
                x='28'
                y='34'
                width='2'
                height='14'
                rx='1'
                fill='currentColor'
                opacity='0.3'
            />
            <rect
                x='34'
                y='34'
                width='2'
                height='14'
                rx='1'
                fill='currentColor'
                opacity='0.3'
            />
            <rect
                x='40'
                y='36'
                width='2'
                height='10'
                rx='1'
                fill='currentColor'
                opacity='0.3'
            />
            {/* AI spark accent */}
            <circle
                cx='52'
                cy='12'
                r='4'
                fill='currentColor'
                opacity='0.8'
            />
            <path
                d='M52 6 v-2 M52 16 v2 M46 12 h-2 M56 12 h2 M48 8 l-1.5 -1.5 M56 8 l1.5 -1.5 M48 16 l-1.5 1.5 M56 16 l1.5 1.5'
                stroke='currentColor'
                strokeWidth='1.5'
                strokeLinecap='round'
                opacity='0.6'
            />
        </svg>
    )
}
