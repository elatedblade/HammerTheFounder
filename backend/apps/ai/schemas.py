from pydantic import BaseModel, ConfigDict, Field


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProfileExtract(Proposal):
    full_name: str = Field(max_length=200)
    skills: list[str] = Field(max_length=100)
    summary: str = Field(max_length=4000)
    warnings: list[str] = Field(max_length=30)


class JobMatch(Proposal):
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(max_length=30)
    gaps: list[str] = Field(max_length=30)


class OutreachDraft(Proposal):
    subject: str = Field(max_length=255)
    body: str = Field(max_length=10000)
    warnings: list[str] = Field(max_length=30)


class QA(Proposal):
    passed: bool
    issues: list[str] = Field(max_length=50)
    recommendations: list[str] = Field(max_length=50)


OUTPUT_SCHEMAS = {"profile_extract": ProfileExtract, "job_match": JobMatch, "outreach_draft": OutreachDraft, "qa": QA}
