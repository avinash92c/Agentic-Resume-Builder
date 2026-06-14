import axios from 'axios';
import { BASEURL } from './BaseAPI';
import type { AgentResponse } from '../types/agent';

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

export const skillsApi = {
  /**
   * Triggers the initial node of the LangGraph state machine
   */
  startWorkflow: async (payload: StartSkillsPayload): Promise<AgentResponse> => {
    const response = await axios.post(`${BASEURL}/skills/start`, payload);
    return response.data;
  },

  /**
   * Resumes the paused LangGraph workflow with human feedback or answers
   */
  resumeWorkflow: async (payload: ResumeSkillsPayload): Promise<AgentResponse> => {
    const response = await axios.post(`${BASEURL}/skills/resume`, payload);
    return response.data;
  },
};