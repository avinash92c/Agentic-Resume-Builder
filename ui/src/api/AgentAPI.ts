import axios, { type AxiosResponse } from 'axios';
import { BASEURL } from './BaseAPI';

import type {
    StartRequest,
    ResumeRequest,
    AgentResponse,
    AgentType,
} from '../types/agent';

const AgentAPI = {
    start: (
        agent: AgentType,
        request: StartRequest
    ): Promise<AxiosResponse<AgentResponse>> => {
        return axios.post(`${BASEURL}/${agent}/start`, request);
    },

    resume: (
        agent: AgentType,
        request: ResumeRequest
    ): Promise<AxiosResponse<AgentResponse>> => {
        return axios.post(`${BASEURL}/${agent}/resume`, request);
    },
};

export default AgentAPI;