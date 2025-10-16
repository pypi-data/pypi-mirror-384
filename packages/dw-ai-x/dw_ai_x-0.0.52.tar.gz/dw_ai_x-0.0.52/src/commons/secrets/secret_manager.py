import logging
from google.cloud import secretmanager
from google.api_core import exceptions


logger = logging.getLogger(__name__)


class SecretManager:
    """
    A wrapper class for Google Cloud Secret Manager operations.

    This class provides simplified methods to create, access, and update secrets
    within a specified Google Cloud project. It uses logging for output.
    """

    def __init__(self, project_id: str):
        """
        Initializes the SecretManager.

        Args:
            project_id (str): The Google Cloud Project ID.
        """
        self._project_id = project_id
        self._client = secretmanager.SecretManagerServiceClient()
        logger.info("SecretManager initialized for project ID: %s", self._project_id)

    def _secret_path(self, secret_id: str) -> str:
        """
        Helper function to construct the full secret path.

        Args:
            secret_id (str): The ID of the secret without the project id specification.

        Returns:
            str: The full path to the secret in the format
                 "projects/PROJECT_ID/secrets/SECRET_ID".
        """
        return self._client.secret_path(self._project_id, secret_id)

    def _secret_version_path(self, secret_id: str, version_id: str) -> str:
        """
        Helper function to construct the full secret version path.

        Args:
            secret_id (str): The ID of the secret.
            version_id (str): The version of the secret (e.g., "latest" or a specific version number).

        Returns:
            str: The full path to the secret version in the format
                 "projects/PROJECT_ID/secrets/SECRET_ID/versions/VERSION_ID".
        """
        return self._client.secret_version_path(self._project_id, secret_id, version_id)

    def create_secret(
        self, secret_id: str, payload_data: str
    ) -> tuple[str | None, str | None]:
        """
        Creates a new secret and adds an initial version with the given payload.
        If the secret already exists, it will attempt to add a new version to it.

        Args:
            secret_id (str): The ID for the new secret.
            payload_data (str): The string data to store in the secret's initial version.
                                An empty string is allowed, but None is not.

        Returns:
            tuple[str | None, str | None]: A tuple containing the name of the created secret
                                           and the name of the first secret version.
                                           Returns (None, None) if secret creation fails.
                                           Returns (secret_name, None) if secret is created/exists
                                           but adding the version fails.

        Raises:
            ValueError: If secret_id is empty or payload_data is None.
        """
        if not secret_id:
            raise ValueError("Secret ID cannot be empty for creation.")
        if payload_data is None:
            raise ValueError(
                "Payload data cannot be None for creation (empty string is allowed)."
            )

        parent = f"projects/{self._project_id}"  # This f-string is for constructing a path, not logging.
        secret_full_path = self._secret_path(secret_id)
        created_secret_name = None

        try:
            secret = self._client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            logger.info("Created secret container: %s", secret.name)
            created_secret_name = secret.name
        except exceptions.AlreadyExists:
            logger.info(
                "Secret container %s already exists. Will add a new version.",
                secret_full_path,
            )
            created_secret_name = secret_full_path
        except Exception as e:
            logger.error("Error creating secret container %s: %s", secret_full_path, e)
            return None, None

        if created_secret_name:
            try:
                payload_bytes = payload_data.encode("UTF-8")
                version = self._client.add_secret_version(
                    request={
                        "parent": created_secret_name,
                        "payload": {"data": payload_bytes},
                    }
                )
                logger.info(
                    "Added secret version: %s to secret %s",
                    version.name,
                    created_secret_name,
                )
                return created_secret_name, version.name
            except Exception as e:
                logger.error(
                    "Error adding version to secret %s: %s", created_secret_name, e
                )
                return created_secret_name, None
        else:
            logger.error(
                "Unexpected state: Secret container name not set for %s before adding version.",
                secret_full_path,
            )
            return None, None

    def access_secret(self, secret_id: str, version_id: str = "latest") -> str | None:
        """
        Accesses the payload of a specific secret version using secret_id and version_id.

        Args:
            secret_id (str): The ID of the secret.
            version_id (str, Optional): The version of the secret to access, default to "latest".

        Returns:
            str | None: The secret payload as a string, or None if an error occurs.

        Raises:
            ValueError: If secret_id is empty.
        """
        if not secret_id:
            raise ValueError("Secret ID cannot be empty for access.")

        full_version_path = self._secret_version_path(secret_id, version_id)
        try:
            response = self._client.access_secret_version(
                request={"name": full_version_path}
            )
            payload = response.payload.data.decode("UTF-8")
            logger.info("Accessed secret version: %s", full_version_path)
            return payload
        except exceptions.NotFound:
            logger.warning("Secret version %s not found.", full_version_path)
            return None
        except Exception as e:
            logger.error("Error accessing secret version %s: %s", full_version_path, e)
            return None

    def access_secret_by_full_path(self, secret_version_path: str) -> str | None:
        """
        Accesses the payload of a secret version using its full path.

        Args:
            secret_version_path (str): The full path to the secret version
                                       (e.g., "projects/PROJECT_ID/secrets/SECRET_ID/versions/VERSION_ID").

        Returns:
            str | None: The secret payload as a string, or None if an error occurs.

        Raises:
            ValueError: If secret_version_path is empty.
        """
        if not secret_version_path:
            raise ValueError("Full secret version path cannot be empty.")
        try:
            response = self._client.access_secret_version(
                request={"name": secret_version_path}
            )
            payload = response.payload.data.decode("UTF-8")
            logger.info(
                "Accessed secret version via full path: %s", secret_version_path
            )
            return payload
        except exceptions.NotFound:
            logger.warning(
                "Secret version %s not found (accessed by full path).",
                secret_version_path,
            )
            return None
        except Exception as e:
            logger.error(
                "Error accessing secret version %s (accessed by full path): %s",
                secret_version_path,
                e,
            )
            return None

    def update_secret(self, secret_id: str, payload_data: str) -> str | None:
        """
        Updates a secret by adding a new version with the given payload.
        This makes the new version the "latest".

        Args:
            secret_id (str): The ID of the secret to update.
            payload_data (str): The new string data to store.

        Returns:
            str | None: The name of the new secret version, or None on failure.

        Raises:
            ValueError: If secret_id is empty or payload_data is None.
        """
        if not secret_id:
            raise ValueError("Secret ID cannot be empty for update.")
        if payload_data is None:
            raise ValueError("Payload data cannot be None for update.")

        secret_name = self._secret_path(secret_id)
        payload_bytes = payload_data.encode("UTF-8")

        try:
            version = self._client.add_secret_version(
                request={"parent": secret_name, "payload": {"data": payload_bytes}}
            )
            logger.info("Added new version %s to secret %s", version.name, secret_name)
            return version.name
        except exceptions.NotFound:
            logger.warning("Secret %s not found. Cannot add version.", secret_name)
            return None
        except Exception as e:
            logger.error("Error adding new version to secret %s: %s", secret_name, e)
            return None

    def list_secrets(self) -> list[str]:
        """
        Lists all secrets in the project.

        Returns:
            list[str]: A list of secret names (full path).
        """
        parent = f"projects/{self._project_id}"
        secrets_list = []
        try:
            for secret in self._client.list_secrets(request={"parent": parent}):
                secrets_list.append(secret.name)
            logger.info(
                "Found %s secrets in project %s.", len(secrets_list), self._project_id
            )
        except Exception as e:
            logger.error(
                "Error listing secrets for project %s: %s", self._project_id, e
            )
        return secrets_list

    def delete_secret(self, secret_id: str) -> bool:
        """
        Deletes a secret and all its versions.

        Args:
            secret_id (str): The ID of the secret to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            ValueError: If secret_id is empty.
        """
        if not secret_id:
            raise ValueError("Secret ID cannot be empty for deletion.")

        name = self._secret_path(secret_id)
        try:
            self._client.delete_secret(request={"name": name})
            logger.info("Deleted secret: %s", name)
            return True
        except exceptions.NotFound:
            logger.warning("Secret %s not found. Cannot delete.", name)
            return False
        except Exception as e:
            logger.error("Error deleting secret %s: %s", name, e)
            return False


# --- Example Usage (requires Google Cloud authentication and Secret Manager API enabled) ---
if __name__ == "__main__":
    # Basic logging configuration for the example
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(levelname)s - %(message)s",
    )

    try:
        PROJECT_ID = "dw-obj-det-dev"
        if PROJECT_ID == "your-gcp-project-id":
            logger.warning(
                "Please update the PROJECT_ID in the example usage section before running."
            )
        else:
            wrapper = SecretManager(project_id=PROJECT_ID)

            client_secret: str = "projects/49311732213/secrets/dev-api-key/versions/1"

            logger.info("Client secret path: %s", client_secret)

            secret = wrapper.access_secret_by_full_path(client_secret)

            if secret is not None:
                logger.info("Retrieved secret payload: %s", secret)

            else:
                logger.critical(
                    "Failed to retrieve secret payload. Check if the secret exists and you have access."
                )

            # Example secret operations
            logger.info(
                "\n--- Starting secret management demo for project: %s ---", PROJECT_ID
            )
            # Define a test secret ID and payloads for demonstration
            test_secret_id = "test-secret-id"
            initial_payload = "Initial secret data for %s style logging demo!"
            updated_payload = "UPDATED secret data for %s style logging demo!"

            created_secret_full_name = None
            first_version_full_name = None

            logger.info("\n--- Listing existing secrets ---")
            existing_secrets = wrapper.list_secrets()
            logger.info(
                "Existing secrets in project '%s': %s", PROJECT_ID, existing_secrets
            )

            logger.info("\n--- Attempting to create secret: %s ---", test_secret_id)
            created_secret_full_name, first_version_full_name = wrapper.create_secret(
                test_secret_id, initial_payload % "initial"
            )

            if created_secret_full_name and first_version_full_name:
                logger.info(
                    "Successfully created secret '%s' with version '%s'.",
                    created_secret_full_name,
                    first_version_full_name,
                )

                logger.info(
                    "\n--- Attempting to access secret: %s (3) ---", test_secret_id
                )
                retrieved_payload = wrapper.access_secret(test_secret_id)
                if retrieved_payload is not None:
                    logger.info("Retrieved payload (3): '%s'", retrieved_payload)
                    assert (
                        retrieved_payload == initial_payload % "initial"
                    ), "Payload mismatch after creation!"

                logger.info(
                    "\n--- Attempting to access secret: %s (version 1) ---",
                    test_secret_id,
                )
                retrieved_payload_v1 = wrapper.access_secret(test_secret_id)
                if retrieved_payload_v1 is not None:
                    logger.info(
                        "Retrieved payload for version 1: '%s'", retrieved_payload_v1
                    )
                    assert (
                        retrieved_payload_v1 == initial_payload % "initial"
                    ), "Payload (v1) mismatch after creation!"

                logger.info("\n--- Attempting to update secret: %s ---", test_secret_id)
                new_version_name = wrapper.update_secret(
                    test_secret_id, updated_payload % "updated"
                )
                if new_version_name:
                    logger.info(
                        "Successfully updated secret, new version: '%s'.",
                        new_version_name,
                    )

                    logger.info(
                        "\n--- Attempting to access updated secret (latest): %s ---",
                        test_secret_id,
                    )
                    retrieved_updated_payload = wrapper.access_secret(test_secret_id)
                    if retrieved_updated_payload is not None:
                        logger.info(
                            "Retrieved updated payload: '%s'", retrieved_updated_payload
                        )
                        assert (
                            retrieved_updated_payload == updated_payload % "updated"
                        ), "Payload mismatch after update!"

                    logger.info(
                        "\n--- Attempting to access original version (v1) of secret: %s ---",
                        test_secret_id,
                    )
                    retrieved_original_payload = wrapper.access_secret(
                        test_secret_id, version_id="1"
                    )
                    if retrieved_original_payload is not None:
                        logger.info(
                            "Retrieved original payload (v1): '%s'",
                            retrieved_original_payload,
                        )
                        assert (
                            retrieved_original_payload == initial_payload % "initial"
                        ), "Original payload (v1) mismatch!"
            else:
                logger.error(
                    "Failed to create secret '%s' or its first version. Check permissions and API status.",
                    test_secret_id,
                )

            logger.info(
                "\n--- Attempting to retrieve secret using a full path (simulating Firestore retrieval) ---"
            )

            simulated_path_from_firestore = first_version_full_name

            if simulated_path_from_firestore:
                logger.info(
                    "Simulating Firestore returned path: %s",
                    simulated_path_from_firestore,
                )
                payload_from_fs_path = wrapper.access_secret_by_full_path(
                    simulated_path_from_firestore
                )
                if payload_from_fs_path is not None:
                    logger.info(
                        "Payload retrieved using full path (simulated from Firestore): '%s'",
                        payload_from_fs_path,
                    )
                    assert (
                        payload_from_fs_path == initial_payload % "initial"
                    ), "Payload mismatch for Firestore simulated path"
                else:
                    logger.warning(
                        "Failed to retrieve payload using simulated Firestore path."
                    )
            else:
                logger.info(
                    "Skipping Firestore path example as 'first_version_full_name' was not set (secret creation might have failed)."
                )

            logger.info("\n--- Attempting to access a non-existent secret ---")
            non_existent_payload = wrapper.access_secret(
                "missing secret", version_id="3"
            )
            assert (
                non_existent_payload is None
            ), "Accessing non-existent secret should return None."
            logger.info("Test for non-existent secret access completed as expected.")

            if created_secret_full_name:
                logger.info("\n--- Attempting to delete secret: %s ---", test_secret_id)
                if wrapper.delete_secret(test_secret_id):
                    logger.info("Successfully deleted secret '%s'.", test_secret_id)
                else:
                    logger.warning(
                        "Failed to delete secret '%s'. It might have already been deleted or an error occurred.",
                        test_secret_id,
                    )

    except ValueError as ve:
        logger.critical("Configuration Error: %s", ve)
    except NameError:
        logger.critical(
            "Import Error: The 'google-cloud-secret-manager' library is not installed."
        )
        logger.critical(
            "Please install it using: pip install google-cloud-secret-manager"
        )
    except Exception as e:
        logger.critical(
            "An unexpected error occurred in the example usage: %s", e, exc_info=True
        )
        logger.critical(
            "Ensure you have authenticated with Google Cloud ('gcloud auth application-default login')"
        )
        logger.critical("and that the Secret Manager API is enabled for your project.")
