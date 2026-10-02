"""Company verification endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas import CompanyVerifyRequest
from app.services.company_verifier import verify_company

router = APIRouter(prefix="/api/company", tags=["company"])


@router.post("/verify")
def company_verify(body: CompanyVerifyRequest, db: DbSession, user: CurrentUser):
    return verify_company(db, body.company_name, email=body.email, website=body.website)
