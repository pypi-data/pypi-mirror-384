from typing import List
import yaml
from tagmapper.connector_api import get_api_client
from tagmapper.generic_model import ModelTemplate


class Schema:
    """A Class containing metadata for a schema. And methods to get the complete yaml."""

    def __init__(self, file_name, owner, name, description, version):
        self.file_name = file_name
        self.owner = owner
        self.name = name
        self.description = description
        self.version = version

    def __repr__(self):
        return f"Schemas(filename='{self.file_name}', owner='{self.owner}', name='{self.name}', description='{self.description}', version={self.version})"

    def to_dict(self) -> dict:
        """Convert the object to a dictionary."""
        return {
            "file_name": self.file_name,
            "owner": self.owner,
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }

    def get_yaml(self):
        """
        Get the YAML file for the schema
        """
        url = f"/download-schema?filename={self.file_name}"
        return yaml.safe_load(get_api_client().get_file(url, "", stream=True))

    def get_ModelTemplate(self):
        """
        Get the ModelTemplate for the schema
        """
        return ModelTemplate(self.get_yaml())

    @staticmethod
    def from_dict(data) -> "Schema":
        """Create an instance from a dictionary."""
        return Schema(
            file_name=data["filename"],
            owner=data["owner"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
        )

    @staticmethod
    def get_schemas() -> List["Schema"]:
        """
        Get existing schemas from the API.
        """

        url = "/get-schema"
        response = get_api_client().get_json(url)

        if isinstance(response, dict):
            if "data" in response.keys():
                return [Schema.from_dict(item) for item in response["data"]]
        raise ValueError("Response is not a valid JSON object")

    @staticmethod
    def download_schema(file_name: str):
        """Download the yaml file from the given URL and save it to current working directory."""
        url = f"/download-schema?filename={file_name}"
        get_api_client().get_file(url, file_name, stream=True)
