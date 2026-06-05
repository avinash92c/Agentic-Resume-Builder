export type AgentType = 'psg' | 'wh' | 'pp' | 'fd' | 'skills';

export type MessageRole =
    | 'user'
    | 'assistant'
    | 'draft'
    | 'system';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content?: string;

    qaPairs?: {
        question: string;
        answer: string;
    }[];
}

// export interface StartRequest {
//     email: string;
//     user_input: string;
// }

export interface ResumeRequest {
    thread_id: string;
    user_data: Record<string, any>;
}

export interface AgentResponse {
    thread_id: string;
    stage?: string;
    complete?: boolean;

    data?: {
        draft?: string;
        questions?: string[];
        message?: string;
        refinement_question?: string;
        approval_question?: string;
    };
}

export interface StartRequest<T = unknown> {
    email: string;
    user_input: T;
}