"""
Factory class that is responsible for instantiating the parameters based on the resource type.
"""

import json

from ..databases.gcs import (
    parse_bucket_name_and_filename,
    load_parameters_data,
    save_json_to_gcs,
)
from .parameter import (
    Parameter,
    ParameterType,
    BigQueryTable,
    CloudStorageFile,
    CommitSha,
    ModelRegistryDisplayName,
    FirestoreDocument,
)


class ParameterFactory:
    """
    Factory class that instantiates the parameters for the Pipelines' components based on the resource type.
    """

    @staticmethod
    def create_parameter(
        resource_type: str, resource_name: str, resource_value: str
    ) -> Parameter:
        """
        Function that creates the parameter instance based on the resource type.

        Args:
            resource_type (str): string representing the type of the resource.
            resource_name (str): string representing the name of the resource.
            resource_value (str): string representing the value of the resource.

        Returns:
            Parameter: the instance of the parameter.
        """

        if resource_type == ParameterType.BIGQUERY_TABLE_ID.value:
            return BigQueryTable(resource_name, resource_value)
        elif resource_type == ParameterType.CLOUD_STORAGE_PATH.value:
            return CloudStorageFile(resource_name, resource_value)
        elif resource_type == ParameterType.COMMIT_SHA.value:
            return CommitSha(resource_name, resource_value)
        elif resource_type == ParameterType.MODEL_REGISTRY_DISPLAY_NAME.value:
            return ModelRegistryDisplayName(resource_name, resource_value)
        elif resource_type == ParameterType.FIRESTORE_DOCUMENT_ID.value:
            return FirestoreDocument(resource_name, resource_value)
        else:
            raise ValueError(f"Parameter type {resource_type} is not supported")

    @classmethod
    def parse_parameter_json(cls, gcs_path: str) -> dict[str, Parameter]:
        """
        Function that generates the parameters by parsing the JSON data stored in a GCS bucket.

        Args:
            gcs_path (str): string representing the filepath of the parameters file in the GCS bucket.

        Returns:
            Dict[str, Parameter]: the dictionary mapping the parameters' names with the relative instance.
        """

        bucket, filename = parse_bucket_name_and_filename(gcs_path)

        parameters = load_parameters_data(bucket, filename)

        parameters_dict = {}

        for parameter in parameters["parameters"]:
            parameters_dict[parameter["resource_name"]] = (
                ParameterFactory.create_parameter(**parameter)
            )

        return parameters_dict

    @classmethod
    def upload_parameters(cls, parameters: dict[str, Parameter], gcs_path: str) -> None:
        """
        Function that uploads the parameters to a GCS bucket.

        Args:
            parameters (dict[str, Parameter]): the dictionary mapping the parameters' names with the relative instance.
            gcs_path (str): string representing the filepath of the parameters file in the GCS bucket.
        """

        bucket, filename = parse_bucket_name_and_filename(gcs_path)

        output = {"parameters": []}
        parameter_list = []
        for parameter_name, parameter_instance in parameters.items():
            parameter_list.append(parameter_instance.to_dict())
        output["parameters"] = parameter_list

        save_json_to_gcs(output, bucket, filename)
