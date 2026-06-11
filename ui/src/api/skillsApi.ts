import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface StartSkillsPayload {
  skills_raw: string;
}

export interface ResumeSkillsPayload {
  thread_id: string;
  user_data: {
    answers?: Record<string, string>;
    is_approved?: boolean;
    refinement_feedback?: string;
  };
}

export interface AgentResponse {
  thread_id: string;
  current_stage: 'interview' | 'review' | 'completed';
  refinement_questions?: string[];
  drafts?: string[];
  refinement_counts?: number;
}

export const skillsApi = {
  /**
   * Triggers the initial node of the LangGraph state machine
   */
  startWorkflow: async (payload: StartSkillsPayload): Promise<AgentResponse> => {
    const response = await axios.post(`${API_BASE_URL}/skills/start`, payload);
    return response.data;
  },

  /**
   * Resumes the paused LangGraph workflow with human feedback or answers
   */
  resumeWorkflow: async (payload: ResumeSkillsPayload): Promise<AgentResponse> => {
    const response = await axios.post(`${API_BASE_URL}/skills/resume`, payload);
    return response.data;
  },
};