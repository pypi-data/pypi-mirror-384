"""
A robust Google Cloud Storage (GCS) client wrapper.

This module provides a comprehensive interface for GCS operations with built-in
error handling, retry mechanisms, and both synchronous and asynchronous capabilities.
It simplifies common storage operations while maintaining reliability and performance.

Features:
    - Automatic retry on transient failures
    - Context manager support for resource cleanup
    - Async file upload support for large files
    - Bucket existence checking
    - File operations (upload, download, delete)
    - Signed URL generation

Usage:
    Basic usage with context manager:
        with GCSClient() as client:
            with client.bucket_scope('my-bucket'):
                client.upload_file('local/file.txt', 'remote/file.txt')

    File operations:
        client = GCSClient()
        with client.bucket_scope('my-bucket'):
            # Upload a file
            client.upload_file('local/data.csv', 'data/data.csv')

            # Download a file
            client.download_file('data/data.csv', 'local/download.csv')

            # List files with prefix
            files = client.get_file_list('data/')

            # Generate temporary access URL
            url = client.get_signed_url('data/data.csv')

    Async file upload:
        async def upload_large_file():
            with GCSClient() as client:
                with client.bucket_scope('my-bucket'):
                    await client.upload_file_async('big_file.zip', 'uploads/big_file.zip')
"""

import json
import aiofiles
from datetime import timedelta
from typing import Optional, Union, Dict, Any
from pathlib import Path
import logging
from contextlib import contextmanager

from google.cloud import storage
from google.auth import default, impersonated_credentials
from google.api_core import retry

from ..utils import constants as kk


def parse_bucket_name_and_filename(gcs_path: str) -> tuple[str, str]:
    """
    Parse the bucket name and filename from a GCS path.

    Args:
        gcs_path: GCS path to parse

    Returns:
        tuple[str, str]: Bucket name and filename
    """
    parts = gcs_path.replace("gs://", "").split("/")
    bucket = parts[0]
    filename = "/".join(parts[1:])
    return bucket, filename


def load_parameters_data(bucket: str, file_name: str) -> Dict[str, Any]:
    """
    Function that loads the parameters data from a JSON file stored in Google Cloud Storage.

    Args:
        bucket_name (str): the name of the bucket where the file is stored
        file_name (str): the name of the file to load.

    Returns:
        dict: the dictionary of parameters that are used by the component.
    """
    with GCSClient() as client:
        with client.bucket_scope(bucket):
            bucket = client.bucket
            blob = bucket.blob(file_name)
            file_contents = blob.download_as_string()
            payload = json.loads(file_contents)
            return payload


def save_json_to_gcs(data: dict, bucket_name: str, file_name: str) -> None:
    """
    Function to store a JSON like object into Google Cloud Storage.

    Args:
        data (dict): the payload to store into the file.
        bucket_name (str): the name of the bucket to store the file into.
        file_name (str): filepath for the file starting from the bucket_name root.
    """

    with GCSClient() as client:
        with client.bucket_scope(bucket_name):
            bucket = client.bucket
            blob = bucket.blob(file_name)
            json_data = json.dumps(data)
            blob.upload_from_string(json_data, "application/json")


class GCSClient:
    """
    A wrapper class for Google Cloud Storage operations.

    This class provides a simplified interface to interact with GCS buckets
    while handling common errors and providing retry mechanisms. It supports
    both synchronous and asynchronous operations.

    Attributes:
        gcs_client: The underlying Google Cloud Storage client
        bucket: The currently connected GCS bucket
        logger: Logger instance for operation tracking
    """

    def __init__(self, project_id: str = kk.PROJECT_ID):
        """
        Initialize a new GCS client instance.

        Args:
            project_id: The Google Cloud project ID. Defaults to value in constants.
        """
        self.gcs_client = storage.Client(project=project_id)
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.gcs_client.close()

    @contextmanager
    def bucket_scope(self, bucket_name: str = kk.BUCKET_NAME):
        """
        Provide a context manager for bucket operations.

        Creates a temporary scope where a bucket connection is automatically
        managed. The connection is closed when exiting the context.

        Args:
            bucket_name: Name of the bucket to connect to

        Raises:
            ConnectionError: If bucket connection fails
        """
        success = self.connect_to_bucket(bucket_name)
        if not success:
            raise ConnectionError(f"Failed to connect to bucket {bucket_name}")
        try:
            yield self
        finally:
            self.bucket = None

    def connect_to_bucket(self, bucket_name: str = kk.BUCKET_NAME) -> bool:
        """
        Connect to a specific GCS bucket.

        Args:
            bucket_name: Name of the bucket to connect to

        Returns:
            bool: True if connection successful, False otherwise

        Example:
            success = client.connect_to_bucket("my-bucket")
            if success:
                print("Connected to bucket")
        """
        try:
            self.bucket = self.gcs_client.bucket(bucket_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to GCS: {str(e)}")
            return False

    def check_bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        try:
            return self.gcs_client.lookup_bucket(bucket_name) is not None
        except Exception as e:
            self.logger.error(f"Failed to check bucket existence: {str(e)}")
            return False

    @retry.Retry()
    def get_file_list(self, prefix: str) -> Optional[list]:
        """
        Get a list of files in the GCS bucket with the specified prefix.

        Args:
            prefix: Prefix to filter files by
        """
        try:
            blobs = list(self.bucket.list_blobs(prefix=prefix))
            return [blob.name[len(prefix) :] for blob in blobs if blob.name != prefix]
        except Exception as e:
            self.logger.error(f"Failed to list files in GCS: {str(e)}")
            return None

    @retry.Retry()
    def get_file_list_ordered_by_time(self, prefix: str) -> Optional[list]:
        """
        Get a list of files in the GCS bucket with the specified prefix ordered by time.

        Args:
            prefix: Prefix to filter files by
        """
        try:
            blobs = list(self.bucket.list_blobs(prefix=prefix))
            blobs.sort(key=lambda x: x.time_created, reverse=True)
            return [blob.name[len(prefix) :] for blob in blobs if blob.name != prefix]
        except Exception as e:
            self.logger.error(f"Failed to list files in GCS: {str(e)}")
            return None

    def file_exists(self, blob_name: str) -> bool:
        """Check if a file exists in the bucket."""
        try:
            return self.bucket.blob(blob_name).exists()
        except Exception as e:
            self.logger.error(f"Failed to check file existence: {str(e)}")
            return False

    def folder_exists(self, folder_name: str) -> bool:
        """Check if a folder exists in the bucket."""
        try:
            blobs = list(self.bucket.list_blobs(prefix=folder_name, max_results=1))
            return len(blobs) > 0
        except Exception as e:
            self.logger.error(f"Failed to check folder existence: {str(e)}")
            return False

    @retry.Retry()
    def create_folder(self, folder_name: str) -> bool:
        """Create a folder in the bucket.

        Args:
            folder_name: Name of the folder to create

        Returns:
            bool: True if folder created successfully, False otherwise
        """
        try:
            blob = self.bucket.blob(folder_name)
            blob.upload_from_string(
                "", content_type="application/x-www-form-urlencoded"
            )
            self.logger.info(f"Folder {folder_name} created")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create folder: {str(e)}")
            return False

    @retry.Retry()
    def upload_file(
        self, source_path: Union[str, Path], destination_blob_name: str
    ) -> bool:
        """
        Upload a file to GCS bucket.

        Args:
            source_path: Local file path
            destination_blob_name: Destination path in GCS bucket

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(str(source_path))
            self.logger.info(f"File {source_path} uploaded to {destination_blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload file: {str(e)}")
            return False

    async def upload_file_async(
        self, source_path: Union[str, Path], destination_blob_name: str
    ) -> bool:
        """Asynchronously upload a large file."""
        try:
            blob = self.bucket.blob(destination_blob_name)
            async with aiofiles.open(str(source_path), "rb") as f:
                content = await f.read()
                blob.upload_from_string(content)
            self.logger.info(f"File {source_path} uploaded to {destination_blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload file asynchronously: {str(e)}")
            return False

    @retry.Retry()
    def download_file(
        self, source_blob_name: str, destination_path: Union[str, Path]
    ) -> bool:
        """
        Download a file from GCS bucket.

        Args:
            source_blob_name: Source path in GCS bucket
            destination_path: Local destination file path

        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(str(destination_path))
            self.logger.info(
                f"File {source_blob_name} downloaded to {destination_path}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to download file: {str(e)}")
            return False

    @retry.Retry()
    def download_folder(
        self, folder_name: str, destination_path: Union[str, Path]
    ) -> bool:
        """Download a folder from the bucket."""
        try:
            destination_path = Path(destination_path)  # Ensure it's a Path object
            blobs = list(self.bucket.list_blobs(prefix=folder_name))
            for blob in blobs:
                relative_path = Path(blob.name).relative_to(
                    folder_name
                )  # Remove folder prefix
                local_file_path = (
                    destination_path / relative_path
                )  # Append to destination
                local_file_path.parent.mkdir(parents=True, exist_ok=True)

                blob.download_to_filename(str(local_file_path))
            self.logger.info(f"Folder {folder_name} downloaded to {destination_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to download folder: {str(e)}")
            return False

    @retry.Retry()
    def delete_file(self, blob_name: str) -> bool:
        """Delete a file from the bucket."""
        try:
            blob = self.bucket.blob(blob_name)
            if not blob.exists():
                return False
            blob.delete()
            self.logger.info(f"File {blob_name} deleted")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file: {str(e)}")
            return False

    @retry.Retry()
    def delete_folder(self, folder_name: str) -> bool:
        """Delete a folder from the bucket."""
        try:
            blobs = list(self.bucket.list_blobs(prefix=folder_name))
            for blob in blobs:
                blob.delete()
            self.logger.info(f"Folder {folder_name} deleted")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete folder: {str(e)}")
            return False

    async def generate_signed_url(
        self,
        bucket_name: str,
        blob_name: str,
        target_principal: str,
        expiration: int = 3600,
        method: str = "GET",
        content_type: str = None,
    ) -> str:
        """
        Generate a signed URL for a file in Google Cloud Storage.

        Args:
            - bucket_name (str): The name of the Google Cloud Storage bucket.
            - blob_name (str): The name of the file in the bucket.
            - target_principal (str): The service account that must be impersonated.
            - expiration (int): The number of seconds the signed URL should be valid for (default is 1 hour).
            - method (str): The HTTP method to allow for the signed URL (default is "GET").
            - content_type (str): The content type of the file (optional).

        Returns:
            - str: The signed URL.
        """
        # Get the default credentials
        credentials, _ = default()
        target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        signing_credentials = impersonated_credentials.Credentials(
            source_credentials=credentials,
            target_principal=target_principal,
            target_scopes=target_scopes,
            lifetime=3600,
        )

        # Client di Storage usando credenziali impersonate
        storage_client = storage.Client(credentials=signing_credentials)

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Check if the blob (PDF) exists
        if method == 'GET':
            if not blob.exists():
                return ""  # Return None if the blob does not exist

        # Generate the signed URL
        url = blob.generate_signed_url(
            version="v4",
            # This URL is valid for 1 hour
            expiration=timedelta(seconds=expiration),
            # Allow GET requests using this URL.
            method=method,
            credentials=signing_credentials,
            content_type=content_type,
        )

        return url

    def move_file(self, source_blob_name, destination_blob_name):
        """Move a file within the bucket."""
        try:
            source_blob = self.bucket.blob(source_blob_name)
            destination_blob = self.bucket.blob(destination_blob_name)
            destination_blob.rewrite(source_blob)
            source_blob.delete()
            self.logger.info(f"Moved {source_blob_name} to {destination_blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file: {str(e)}")
            return False
