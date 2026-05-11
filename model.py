from pydantic import BaseModel, Field

class PersonalInfo(BaseModel):
    name: str
    email: str
    linkedin: str
    github: str
    phone: str

class Resume(BaseModel):
    personalInfo: PersonalInfo = Field(alias="personal_info")
    skills: str = Field(alias="skills")
    education: str = Field(alias="education")
    certifications: str = Field(alias="certifications")
    summary: str = Field(alias="professional_summary")
    workHistory: str = Field(alias="work_history")
    personalProjects: str = Field(alias="personal_projects")
