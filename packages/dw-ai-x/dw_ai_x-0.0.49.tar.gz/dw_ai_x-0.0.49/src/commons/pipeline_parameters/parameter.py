"""
Parameter classes for pipeline parameters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum
import pandas as pd
import joblib

from google.cloud import storage, aiplatform

from ..databases.gcs import parse_bucket_name_and_filename, GCSClient
from ..databases.fs import FirestoreWrapper


class ParameterType(Enum):
    BIGQUERY_TABLE_ID = "BigQuery table id"
    CLOUD_STORAGE_PATH = "Cloud Storage path"
    COMMIT_SHA = "Commit SHA"
    MODEL_REGISTRY_DISPLAY_NAME = "Model registry display name"
    FIRESTORE_DOCUMENT_ID = "Firestore document id"
    VERTEX_AI_ENDPOINT = "Vertex AI endpoint"


class Parameter(ABC):
    """Abstract base class for parameters."""

    def __init__(self, resource_name: str, resource_value: str, resource_type: str):
        self.resource_name = resource_name
        self.resource_value = resource_value
        self.resource_type = resource_type

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, str]) -> "Parameter":
        """Initialize the parameter instance from a dictionary."""

    def to_dict(self) -> Dict[str, str]:
        """Convert the parameter instance to a dictionary."""
        return {
            "resource_name": self.resource_name,
            "resource_value": self.resource_value,
            "resource_type": self.resource_type,
        }

    def get_value(self) -> str:
        return self.resource_value

    @abstractmethod
    def get_instance(self) -> Any:
        """Return the instance of the parameter."""


class BigQueryTable(Parameter):
    """Parameter type for BigQuery tables."""

    def __init__(self, resource_name, resource_value):
        super().__init__(
            resource_name, resource_value, ParameterType.BIGQUERY_TABLE_ID.value
        )

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "BigQueryTable":
        if data.get("resource_type") != ParameterType.BIGQUERY_TABLE_ID.value:
            raise ValueError("Invalid resource type for BigQueryTable")
        return cls(
            resource_name=data["resource_name"], resource_value=data["resource_value"]
        )

    def get_instance(self) -> pd.DataFrame:
        """Return a dataframe with the data from the BigQuery table."""
        query = f"SELECT * FROM `{self.resource_value}`"
        # TODO: Do we need big query?
        return None

class CloudStorageFile(Parameter):
    """Parameter type for Cloud Storage files."""

    def __init__(self, resource_name, resource_value):
        super().__init__(
            resource_name, resource_value, ParameterType.CLOUD_STORAGE_PATH.value
        )

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CloudStorageFile":
        if data.get("resource_type") != ParameterType.CLOUD_STORAGE_PATH.value:
            raise ValueError("Invalid resource type for CloudStorageTable")
        return cls(
            resource_name=data["resource_name"], resource_value=data["resource_value"]
        )

    def get_instance(self) -> str:
        """Download the file from Cloud Storage and return the local file path."""
        bucket_name, filename = parse_bucket_name_and_filename(self.resource_value)
        with GCSClient() as storage_client:
            with storage_client.bucket_scope(bucket_name):
                blob = storage_client.bucket.blob(filename)
                destination_file_name = filename.split("/")[-1]
                blob.download_to_filename(destination_file_name)
                return destination_file_name

    def set_instance(self, file_path: str) -> None:
        """Upload the file to Cloud Storage."""
        bucket_name, filename = parse_bucket_name_and_filename(self.resource_value)
        with GCSClient() as storage_client:
            with storage_client.bucket_scope(bucket_name):
                blob = storage_client.bucket.blob(filename)
                blob.upload_from_filename(file_path)


class CommitSha(Parameter):
    """Parameter type for Commit SHA."""

    def __init__(self, resource_name, resource_value):
        super().__init__(resource_name, resource_value, ParameterType.COMMIT_SHA.value)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CommitSha":
        if data.get("resource_type") != ParameterType.COMMIT_SHA.value:
            raise ValueError("Invalid resource type for CommitSha")
        return cls(
            resource_name=data["resource_name"], resource_value=data["resource_value"]
        )

    def get_instance(self):
        """Return the commit SHA."""
        return self.resource_value


class ModelRegistryDisplayName(Parameter):
    """Parameter type for Model Registry display name."""

    def __init__(self, resource_name, resource_value):
        super().__init__(
            resource_name,
            resource_value,
            ParameterType.MODEL_REGISTRY_DISPLAY_NAME.value,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ModelRegistryDisplayName":
        if data.get("resource_type") != ParameterType.MODEL_REGISTRY_DISPLAY_NAME.value:
            raise ValueError("Invalid resource type for ModelRegistryDisplayName")
        return cls(
            resource_name=data["resource_name"], resource_value=data["resource_value"]
        )

    def get_instance(self):
        """Return the Model Registry display name."""
        return aiplatform.Model(self.resource_value)
    

class FirestoreDocument(Parameter):
    """Parameter type for Firestore collections."""

    def __init__(self, resource_name, resource_value):
        super().__init__(
            resource_name, resource_value, ParameterType.FIRESTORE_DOCUMENT_ID.value
        )
        self.fs_client = FirestoreWrapper()

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "FirestoreDocument":
        if data.get("resource_type") != ParameterType.FIRESTORE_DOCUMENT_ID.value:
            raise ValueError("Invalid resource type for FirestoreDocument")
        return cls(
            resource_name=data["resource_name"], resource_value=data["resource_value"]
        )

    def get_instance(self):
        """Return the Firestore document."""
        collection_name, document_id = self.resource_value.split("/")
        document = self.fs_client.get_document(collection_name, document_id)
        return document
    
    def get_instance_pydantic(self, pydantic_model):
        """Return the Firestore document as a Pydantic model."""
        collection_name, document_id = self.resource_value.split("/")
        document = self.fs_client.get_document_pydantic(collection_name, document_id, pydantic_model)
        return document

    def get_document_id(self):
        return self.resource_value.split("/")[-1]
    
    def get_collection_name(self):
        return self.resource_value.split("/")[0]
    

class VertexAIEndpoint(Parameter):
    """
    Parameter type that represents Vertex AI Endpoints
    """


    def __init__(self, resource_name: str, resource_value: str):
        super().__init__(
            resource_name=resource_name, resource_value=resource_value, resource_type=ParameterType.VERTEX_AI_ENDPOINT.value
        )

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "VertexAIEndpoint":
        if data.get("resource_type") != ParameterType.VERTEX_AI_ENDPOINT.value:
            raise ValueError(f"Invalid resource type for VertexAIEndpoint, got {data.get("resource_type")} instead of {ParameterType.VERTEX_AI_ENDPOINT.value}")
        return cls(
            resource_name=data["resource_name"], resource_value=data["resource_value"]
        )

    def get_instance(self):
        """Return the Vertex AI endpoint."""
        return aiplatform.Endpoint(self.resource_value)
    