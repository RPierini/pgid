from __future__ import annotations

from typing import Any

from app.models import CourseLockRequest, DemoUser, GradeSubmission
from app.repositories import app_repo


async def fetch_grades(user: DemoUser) -> dict[str, Any]:
    return await app_repo.fetch_grades(user)


async def submit_grade(user: DemoUser, submission: GradeSubmission) -> dict[str, Any]:
    return await app_repo.submit_grade(user, submission)


async def freeze_course(user: DemoUser, payload: CourseLockRequest) -> dict[str, Any]:
    return await app_repo.freeze_course(user, payload)
