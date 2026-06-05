// src/types/models.ts

export interface PersonalInfo {
    name: string
    email: string
    linkedin: string
    github: string
    phone: string
}

export interface Education {
    degree: string
    institution: string
    field_of_study?: string
    start_year?: number
    end_year?: number
    location?: string
    achievements?: string
}

export interface Certifications {
    name: string
    issuing_organization?: string
    issue_date?: string
    expiration_date?: string
    credential_id?: string
    credential_url?: string
}

export interface Resume {
    personal_info: PersonalInfo
    skills?: string
    education?: Education[]
    certificates?: Certifications[]
    professional_summary?: string
    work_history?: string
    personal_projects?: string
    session_id?: string
    final_resume?: string
}

export interface StartRequest {
    user_input: string
    email: string
}

export interface ResumeRequest {
    thread_id: string
    user_data: Record<string, unknown>
}

export interface EducationInfoRequest {
    email: string;
    education: Education[];
}

export interface CertificationsRequest {
    email: string;
    certifications: Certifications[];
}

export interface StartRequest {
    user_input: string
    email: string
}

export interface ResumeRequest {
    thread_id: string
    user_data: Record<string, unknown>
}

export interface AgentResponse {
    thread_id: string
    stage: string
    data: Record<string, unknown> | null
    complete: boolean
}

export interface WorkExperience {
    company_name: string;
    job_title: string;
    start_date: string;
    end_date: string;
    employment_type: string;
    projects: string[];
}