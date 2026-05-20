import axios, { type AxiosResponse } from 'axios';
import { BASEURL } from './BaseAPI';
import type { Pages } from '../types/pages';
import type { PersonalInfo,Education,EducationInfoRequest, Certifications, CertificationsRequest } from '../types/models';

const CoreAPI = {
    pages: (): Promise<AxiosResponse<Pages>> => {
        return axios.get<Pages>(`${BASEURL}/pages`);
    },
    getPersonalInfo: (email: string): Promise<AxiosResponse<PersonalInfo>> => {
        return axios.get<PersonalInfo>(`${BASEURL}/personal-info`, {
            params: { email: email }
        })
    },
    savePersonalInfo: (personalInfo:PersonalInfo):Promise<AxiosResponse<string>> => {
        // let headers = {}
        return axios.post<string>(`${BASEURL}/personal-info`,personalInfo)
    },
    getEducationInfo: (email: string): Promise<AxiosResponse<Education[]>> => {
        return axios.get<Education[]>(`${BASEURL}/education-info`, {
            params: { email: email }
        })
    },
    saveEducationInfo: (education:Education[], email:string):Promise<AxiosResponse<string>> => { 
        let educationReq:EducationInfoRequest = {
            email: email,
            education: education
        }
        return axios.post<string>(`${BASEURL}/education-info`,educationReq)
    },
    getCertificationInfo: (email:string):Promise<AxiosResponse<Certifications[]>> => {
        return axios.get<Certifications[]>(`${BASEURL}/certification-info`, {
            params: { email: email }
        })
    },
    saveCertificationInfo: (certifications:Certifications[], email:string):Promise<AxiosResponse<string>> => {
        let certificationsReq:CertificationsRequest = {
            email: email,
            certifications: certifications
        }
        return axios.post<string>(`${BASEURL}/certification-info`,certificationsReq)
    },
}

export default CoreAPI;