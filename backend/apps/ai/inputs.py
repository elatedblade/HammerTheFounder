"""Canonical capability inputs: user-provided facts never replace candidate data.

Input JSON: profile_extract={resume_id}; job_match={job_id};
outreach_draft={contact_id}; qa={content}. UUIDs are serialized as strings.
"""
from uuid import UUID
from django.utils import timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError
from apps.integrations.ai.omniroute import GatewayError

AGENT_VERSION = "htf-assistance-v2"
PROMPT_VERSION = "canonical-facts-v1"


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileInput(Input):
    resume_id: UUID


class MatchInput(Input):
    job_id: UUID


class DraftInput(Input):
    contact_id: UUID


class QAInput(Input):
    content: str = Field(min_length=1, max_length=16000, strict=True)


INPUT_SCHEMAS = {"profile_extract": ProfileInput, "job_match": MatchInput, "outreach_draft": DraftInput, "qa": QAInput}


def validate_input(capability, value):
    try:
        return INPUT_SCHEMAS[capability].model_validate(value).model_dump(mode="json")
    except (PydanticValidationError, KeyError) as exc:
        # Never include validation errors containing submitted private values.
        raise ValidationError({"input": "Use only the required capability keys: profile_extract {resume_id}, job_match {job_id}, outreach_draft {contact_id}, qa {content}. No raw profile or resume overrides are permitted."}) from exc


def canonical_input(campaign, capability, input_data):
    """Read facts afresh at execution; persist only references, not their copies."""
    from apps.candidates.models import CandidateProfile
    profile = CandidateProfile.objects.select_related("user").get(pk=campaign.candidate_id)
    if not profile.user.is_active or profile.user.role != "CLIENT":
        raise GatewayError("candidate_not_active")
    facts = {name: getattr(profile, name) for name in (
        "full_name", "headline", "location", "experience_summary", "target_roles",
        "preferred_locations", "remote_preference", "target_industries", "work_authorization",
        "sponsorship_requirement", "notice_period", "preferences_json",
    )}
    facts.update({name: str(getattr(profile, name)) if getattr(profile, name) is not None else None for name in ("expected_ctc_min", "expected_ctc_max")})
    payload = {"candidate": facts, "campaign": {"plan": campaign.plan}}
    refs = {"candidate": {"id": profile.pk, "profile_version": profile.profile_version}, "campaign": {"id": str(campaign.pk), "version": campaign.version}, "loaded_at": timezone.now().isoformat()}

    def company_facts(company):
        refs["company"] = {"id": str(company.pk), "updated_at": company.updated_at.isoformat()}
        return {name: getattr(company, name) for name in ("name", "website", "industry", "location")}

    if capability == "profile_extract":
        from apps.resumes.models import Resume
        resume = Resume.objects.filter(pk=input_data["resume_id"], candidate=profile, upload_status="UPLOADED", parse_status="PARSED").first()
        if resume is None or not resume.extracted_text:
            raise GatewayError("resume_not_available")
        payload.update({"resume_text": resume.extracted_text[:32000], "source_truncated": len(resume.extracted_text) > 32000})
        refs["resume"] = {"id": str(resume.pk), "version": resume.version, "parsed_at": resume.parsed_at.isoformat() if resume.parsed_at else None}
    elif capability == "job_match":
        from apps.jobs.models import Job
        job = Job.objects.select_related("company").filter(pk=input_data["job_id"]).first()
        if job is None:
            raise GatewayError("job_not_available")
        payload["job"] = {name: getattr(job, name) for name in ("title", "description", "location", "employment_type", "status", "canonical_url")}
        payload["company"] = company_facts(job.company)
        refs["job"] = {"id": str(job.pk), "updated_at": job.updated_at.isoformat()}
    elif capability == "outreach_draft":
        from apps.contacts.models import Contact
        from apps.outreach.models import Suppression
        contact = Contact.objects.select_related("company").filter(pk=input_data["contact_id"]).first()
        if contact is None:
            raise GatewayError("contact_not_available")
        suppressed = bool(contact.email and Suppression.objects.filter(email__iexact=contact.email).exists())
        if suppressed:
            raise GatewayError("contact_suppressed")
        payload["contact"] = {name: getattr(contact, name) for name in ("name", "title", "email", "profile_url")}
        payload["company"] = company_facts(contact.company)
        payload["suppression"] = {"suppressed": False, "email_available": bool(contact.email)}
        refs["contact"] = {"id": str(contact.pk), "updated_at": contact.updated_at.isoformat()}
        refs["suppression_checked_at"] = timezone.now().isoformat()
    elif capability == "qa":
        payload["content_for_review"] = input_data["content"]
    else:
        raise GatewayError("invalid_capability")
    return payload, refs
