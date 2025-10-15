"""Pydantic models for Firestore document schemas.

This module defines the data models that represent the structure of documents
stored in Firestore. These models provide type validation and serialization
for organization, user, dataset, and process related data.
"""

from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class Organization(BaseModel):
    """Organization data model for Firestore documents.

    Represents an organization entity with its associated metadata and configuration.
    Organizations can have multiple users and are used for access control.

    Attributes:
        document_id: Firestore auto-generated document identifier
        name: Organization's display name
        p_iva: VAT identification number
        address: Physical address of the organization
        is_active: Flag indicating if the organization is currently active
        billing_tag: Optional billing identifier
        description: Optional organization description
        allowed_users_emails: List of email addresses of users allowed in the organization
        created_at: Timestamp of when the organization was created
        updated_at: Timestamp of the last update to the organization
    """

    document_id: Optional[str] = None  # Firestore auto-generated ID
    name: str
    p_iva: str
    address: str
    is_active: bool = True
    billing_tag: Optional[str] = None
    description: Optional[str] = None
    allowed_users_emails: Optional[list[EmailStr]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class User(BaseModel):
    """User data model for Firestore documents.

    Represents a user entity with their personal information and organizational
    association.

    Attributes:
        document_id: Firestore auto-generated document identifier
        organization_id: ID of the organization the user belongs to
        email: User's primary email address
        updated_email: Optional new email address pending verification
        username: Unique username for the user
        first_name: User's first name
        last_name: User's last name
        is_active: Flag indicating if the user account is active
        created_at: Timestamp of when the user was created
        updated_at: Timestamp of the last update to the user
    """

    document_id: Optional[str] = None  # Firestore auto-generated ID
    organization_id: str
    email: EmailStr
    updated_email: Optional[EmailStr] = None
    username: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    onboarding_completed: bool = Field(
        description="Flag indicating if the user has completed the UI onboarding, default is False",
        default=False,
    )


class DatasetFormat(str, Enum):
    """Enum for dataset format"""

    COCO = "coco"
    YOLO = "yolo"


class Dataset(BaseModel):
    """Model for dataset information"""

    id: Optional[str] = None  # Firestore auto-generated ID
    name: str
    description: Optional[str] = None
    format: DatasetFormat
    organization_id: str
    dataset_path: str
    is_active: bool = True


class ProcessStatus(str, Enum):
    """Enum for process status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Process(BaseModel):
    """Model for process information"""

    id: Optional[str] = None  # Firestore auto-generated ID
    created_at: Optional[datetime] = None  # Firestore SERVER_TIMESTAMP
    user_uuid: str
    name: str
    status: ProcessStatus = ProcessStatus.PENDING


class DatasetUploadProcess(Process):
    """Model for dataset upload process information"""

    dataset: Dataset
