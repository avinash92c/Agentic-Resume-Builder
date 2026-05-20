import type { AgentType } from '../types/agent';

export interface AgentConfig {
    title: string;
    subtitle: string;
    initialPlaceholder: string;
}

export const AGENT_CONFIG: Record<AgentType, AgentConfig> = {
    psg: {
        title: 'Professional Summary',
        subtitle: 'Tell me about your professional background',
        initialPlaceholder:
            'Describe your experience, strengths, technologies, achievements, and career journey...',
    },

    wh: {
        title: 'Work Experience',
        subtitle: 'Tell me about your work history',
        initialPlaceholder:
            'Describe your job responsibilities, projects, achievements, and technologies...',
    },

    pp: {
        title: 'Personal Projects',
        subtitle: 'Tell me about your projects',
        initialPlaceholder:
            'Describe your projects, technologies used, architecture, and impact...',
    },

    fd: {
        title: 'Final Review',
        subtitle: 'Review your generated resume',
        initialPlaceholder: '',
    },
};