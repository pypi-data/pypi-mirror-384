from enum import StrEnum
from uuid import UUID

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, JSON, UniqueConstraint, Enum
from sqlmodel import Field

from ..general.models import BaseModel


class SalaryFrequency(StrEnum):
    MONTH = "month"
    YEAR = "year"
    WEEK = "week"
    HOUR = "hour"


class RemoteType(StrEnum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class QuestionCategory(StrEnum):
    SCREENING = "screening"
    DEMOGRAPHIC = "demographic"


class SourceType(StrEnum):
    ATS = "ats"
    CUSTOM_FILE = "custom-file"


class VacanciesModel(BaseModel):
    pass


class VacanciesOrganizationModel(VacanciesModel):
    organization: UUID = Field(index=True)


class Feed(VacanciesOrganizationModel, table=True):
    name: str = Field(index=True)
    status: str = Field(index=True)
    file_url: Optional[str] = Field()
    ats_link_id: Optional[UUID] = Field()
    entrypoint: Optional[str] = Field()
    last_sync_date: Optional[datetime] = Field()
    source_type: SourceType =  Field(sa_column=Column(Enum(SourceType)))
    synced_vacancy_count: int = Field(default=0)
    mapping: list = Field(sa_column=Column(JSON))
    custom_fields: list = Field(sa_column=Column(JSON))


class Vacancy(VacanciesOrganizationModel, table=True):
    feed_id: UUID = Field(foreign_key="feed.id")
    reference_number: str = Field(index=True)
    requisition_id: str = Field(index=True)
    title: str = Field(index=True)
    description: str = Field()
    status: str = Field()
    job_site_url: str = Field()
    company_name: str = Field(index=True)
    parent_company_name: Optional[str] = Field()
    remote_type: Optional[RemoteType] = Field(sa_column=Column(Enum(RemoteType)))
    publish_date: Optional[datetime] = Field()
    expiration_date: Optional[datetime] = Field()
    last_updated_date: Optional[datetime] = Field()
    category: List[str] = Field(sa_column=Column(JSON))
    experience: List[str] = Field(sa_column=Column(JSON))
    education: List[str] = Field(sa_column=Column(JSON))
    hours_fte: Optional[float] = Field()
    hours_min: Optional[int] = Field()
    hours_max: Optional[int] = Field()
    location_address: Optional[str] = Field()
    location_zipcode: Optional[str] = Field()
    location_city: Optional[str] = Field()
    location_state: Optional[str] = Field()
    location_country: Optional[str] = Field()
    location_lat: Optional[float] = Field()
    location_lng: Optional[float] = Field()
    salary_min: Optional[float] = Field()
    salary_max: Optional[float] = Field()
    salary_currency: Optional[str] = Field()
    salary_frequency: Optional[SalaryFrequency] = Field(sa_column=Column(Enum(SalaryFrequency)))
    recruiter_first_name: Optional[str] = Field()
    recruiter_last_name: Optional[str] = Field()
    recruiter_phone_number: Optional[str] = Field()
    recruiter_email: Optional[str] = Field()
    recruiter_role: Optional[str] = Field()
    checksum: str = Field(index=True)
    questionnaire_id: Optional[UUID] = Field(index=True)

    __table_args__ = (
        UniqueConstraint("feed_id", "reference_number", name="uq_feed_reference"),
    )


class Questionnaire(VacanciesOrganizationModel, table=True):
    name: str = Field(index=True)
    question_count: int = Field(default=0)


class Question(VacanciesOrganizationModel, table=True):
    questionnaire_id: UUID = Field(index=True)
    question_category: QuestionCategory = Field(sa_column=Column(Enum(QuestionCategory)))
    key: str = Field(index=True)
    label: Optional[str] = Field()
    text: Optional[str] = Field()
    type: str = Field()
    required: bool = Field()
    options: Optional[list] = Field(sa_column=Column(JSON))


class Modification(VacanciesOrganizationModel, table=True):
    name: str = Field(index=True)
    type: str = Field(index=True)
    selection_configuration: dict = Field(sa_column=Column(JSON))
    modification_configuration: dict = Field(sa_column=Column(JSON))

