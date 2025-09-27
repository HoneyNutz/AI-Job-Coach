from pydantic import BaseModel, HttpUrl, field_validator, Field
from typing import List, Optional, Any

# Custom HttpUrl type to gracefully handle invalid URLs
LenientHttpUrl = Optional[HttpUrl]

class LenientUrlModel(BaseModel):
    url: LenientHttpUrl = None

    @field_validator('url', mode='before')
    def validate_url(cls, v: Any) -> Optional[str]:
        if isinstance(v, str) and v.strip():
            try:
                HttpUrl(v)
                return v
            except Exception:
                return None
        return None

# Updated Job Description Model based on jsonresume.org/job-description-schema
class JobDescription(LenientUrlModel):
    name: Optional[str] = None  # Job title, e.g., "Web Developer"
    description: Optional[str] = None  # Company description
    skills: Optional[str] = None
    image: Optional[str] = None
    jobLocation: Optional[str] = None
    hiringOrganization: Optional[str] = None # Company name
    employmentType: Optional[str] = None
    datePosted: Optional[str] = None
    jobBenefits: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    educationRequirements: List[str] = Field(default_factory=list)
    experienceRequirements: List[str] = Field(default_factory=list)

# JSON Resume Schema Models (Corrected)
class Location(BaseModel):
    address: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    countryCode: Optional[str] = None
    region: Optional[str] = None

class Profile(LenientUrlModel):
    network: Optional[str] = None
    username: Optional[str] = None

class Basics(LenientUrlModel):
    name: Optional[str] = None
    label: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    location: Location = Field(default_factory=Location)
    profiles: List[Profile] = Field(default_factory=list)

class Work(LenientUrlModel):
    name: Optional[str] = None
    position: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

class Volunteer(LenientUrlModel):
    organization: Optional[str] = None
    position: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

class Education(LenientUrlModel):
    institution: Optional[str] = None
    area: Optional[str] = None
    studyType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    score: Optional[str] = None
    courses: List[str] = Field(default_factory=list)

class Award(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    awarder: Optional[str] = None
    summary: Optional[str] = None

class Certificate(LenientUrlModel):
    name: Optional[str] = None
    date: Optional[str] = None
    issuer: Optional[str] = None

class Publication(LenientUrlModel):
    name: Optional[str] = None
    publisher: Optional[str] = None
    releaseDate: Optional[str] = None
    summary: Optional[str] = None

class Skill(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

class Language(BaseModel):
    language: Optional[str] = None
    fluency: Optional[str] = None

class Interest(BaseModel):
    name: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

class Reference(BaseModel):
    name: Optional[str] = None
    reference: Optional[str] = None

class Project(LenientUrlModel):
    name: Optional[str] = None
    description: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    entity: Optional[str] = None
    type: Optional[str] = None

class Resume(BaseModel):
    basics: Basics = Field(default_factory=Basics)
    work: List[Work] = Field(default_factory=list)
    volunteer: List[Volunteer] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    certificates: List[Certificate] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    interests: List[Interest] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
