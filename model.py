from pydantic import BaseModel, Field
from typing import Optional,List


class PersonalInfo(BaseModel):
    name: str = Field(alias="name")
    email: str = Field(alias="email")
    linkedin: str = Field(alias="linkedin")
    github: str = Field(alias="github")
    phone: str = Field(alias="phone")

class Education(BaseModel):
    degree: str = Field(description="Degree name like B.Tech, B.Sc, MBA")
    institution: str = Field(description="College or university name")
    field_of_study: Optional[str] = Field(default=None,description="Specialization or major subject")
    start_year: Optional[int] = Field(default=None,description="Education start year")
    end_year: Optional[int] = Field(default=None,description="Education completion year")
    location: Optional[str] = Field(default=None,description="Institution location")
    achievements: Optional[str] = Field(default=None,description="Scholarships, ranks, honors, etc.")

class Certifications(BaseModel):
    name: str = Field(description="Certification name")    
    issuing_organization: Optional[str] = Field(default=None,description="Organization issuing the certification")
    issue_date: Optional[str] = Field(default=None,description="Certification issue date")
    expiration_date: Optional[str] = Field(default=None,description="Certification expiration date")
    credential_id: Optional[str] = Field(default=None,description="Credential or certificate ID")
    credential_url: Optional[str] = Field(default=None,description="Verification URL for the certification")

class Resume(BaseModel):
    personalInfo: PersonalInfo = Field(default=None, alias="personal_info")
    skills: Optional[str] = Field(default=None, alias="skills")
    education:Optional[List[Education]] = Field(default=None, alias="education")
    certificates: Optional[List[Certifications]] = Field(default=None, alias="certificates")
    summary: Optional[str] = Field(default=None, alias="professional_summary")
    workHistory: Optional[str] = Field(default=None, alias="work_history")
    personalProjects: Optional[str] = Field(default=None, alias="personal_projects")
    sessionId: Optional[str] = Field(default=None, alias="session_id")



