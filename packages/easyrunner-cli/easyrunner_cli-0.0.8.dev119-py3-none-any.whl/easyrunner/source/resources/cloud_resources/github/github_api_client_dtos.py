from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ....types.dto_base import DTOBase


@dataclass
class GitHubDeployKey(DTOBase):
    """Data model for GitHub deploy key information."""

    id: int
    key: str
    url: str
    title: str
    verified: bool
    created_at: datetime
    read_only: bool
    added_by: Optional[str] = None
    last_used: Optional[datetime] = None


@dataclass
class CreateDeployKeyRequest(DTOBase):
    """Data model for creating a deploy key request."""

    title: str
    key: str
    read_only: bool = True


@dataclass
class DeleteDeployKeyResponse:
    """Response for deleting a deploy key."""
    
    success: bool
    status_code: int
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if the operation was successful."""
        return self.success and 200 <= self.status_code < 300


@dataclass
class ListDeployKeysResponse:
    """Response for listing deploy keys."""
    
    success: bool
    status_code: int
    deploy_keys: Optional[List[GitHubDeployKey]] = None
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if the operation was successful."""
        return self.success and 200 <= self.status_code < 300


@dataclass
class AddDeployKeyResponse(DTOBase):
    """Response DTO for adding a deploy key to a GitHub repository.
    
    The GitHub API returns 201 Created on successful creation with the deploy key object.
    """
    
    success: bool
    status_code: int
    deploy_key: Optional[GitHubDeployKey] = None
    error_message: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if the addition was successful (status code 201)."""
        return self.success and self.status_code == 201
