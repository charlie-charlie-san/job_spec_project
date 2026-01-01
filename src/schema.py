"""JobSpec Pydantic model for job specification data."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Rate(BaseModel):
    """報酬レンジを表すモデル."""

    min: float | None = None
    max: float | None = None
    unit: Literal["hourly", "daily", "monthly", "yearly"] | None = None


class JobSpec(BaseModel):
    """求人情報を表すメインモデル."""

    title: str | None = None
    company: str | None = None
    role: str | None = None
    summary: str | None = None
    must_requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    stack_keywords: list[str] = Field(default_factory=list)
    location: str | None = None
    remote_type: Literal["full_remote", "hybrid", "on_site"] | None = None
    rate: Rate | None = None
    start_date: str | None = None
    duration: str | None = None
    interview_count: int | None = None
    working_hours: str | None = None
    contract_type: str | None = None
    notes: str | None = None
    risks_or_unknowns: list[str] = Field(default_factory=list)

