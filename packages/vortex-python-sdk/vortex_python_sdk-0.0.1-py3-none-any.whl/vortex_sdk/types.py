from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    user_id: str
    identifiers: Dict[str, str]
    groups: Optional[List[str]] = None
    role: Optional[str] = None


class JwtPayload(BaseModel):
    user_id: str
    identifiers: Dict[str, str]
    groups: Optional[List[str]] = None
    role: Optional[str] = None


class InvitationTarget(BaseModel):
    type: Literal["email", "username", "phoneNumber"]
    value: str


class Invitation(BaseModel):
    id: str
    target: InvitationTarget
    group_type: Optional[str] = None
    group_id: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, bool]]] = None


class CreateInvitationRequest(BaseModel):
    target: InvitationTarget
    group_type: Optional[str] = None
    group_id: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, bool]]] = None


class AcceptInvitationsRequest(BaseModel):
    invitation_ids: List[str]
    target: InvitationTarget


class ApiResponse(BaseModel):
    data: Optional[Dict] = None
    error: Optional[str] = None
    status_code: int = 200


class VortexApiError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)