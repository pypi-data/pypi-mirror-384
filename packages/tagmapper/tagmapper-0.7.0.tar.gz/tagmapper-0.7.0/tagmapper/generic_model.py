import copy
import json
import logging
import os
import yaml as pyyaml
from typing import List, Literal, Optional, Union

from tagmapper.connector_api import (
    get_mappings,
    make_constant_mapping_dict,
    make_timeseries_mapping_dict,
    post_generic_model_mapping,
)
from tagmapper.mapping import Constant, Mapping, Timeseries

logger = logging.getLogger(__name__)


class Attribute:
    """
    Attribute class.

    An attribute is a defined property of a generic model.
    """

    def __init__(self, name: str, data: dict):
        """Initialize an Attribute instance. NB! Does not specify any mappings

        Args:
            name (str): The name of the attribute.
            data (dict): The data for the attribute. The dictionary should contain
                the keys "identifier", "description", "alias", and "type" to set
                the corresponding attributes.

        Raises:
            ValueError: If the input data is not a dictionary.
        """
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dict")

        self.name = name
        if "identifier" in data.keys():
            self.identifier = data["identifier"]
        else:
            self.identifier = name.lower().replace(" ", "_")

        # identifier naming rule not enforced yet
        if False and self.identifier != self.identifier.replace(" ", "_"):
            raise ValueError("Invalid identifier. Whitespace is not allowed.")

        self.description = ""
        if "description" in data.keys():
            self.description = data["description"]

        self.alias = []
        if "alias" in data.keys():
            self.alias = data["alias"]

        if isinstance(self.alias, str):
            if len(self.alias) == 0:
                self.alias = []
            else:
                self.alias = [self.alias]

        # Currently supports types: timeseries, constant
        self.type = ""
        if "type" in data.keys():
            self.type = data["type"]

        # Each attribute can have multiple mappings
        self.mapping = []

    def add_mapping(self, mapping: Union[Mapping, dict]):
        """
        Add a mapping to the attribute
        """
        if isinstance(mapping, dict):
            if "ConstantValue" in mapping.keys():
                mapping = Constant(mapping)
            elif "Timeseries" in mapping.keys():
                mapping = Timeseries(mapping)
            else:
                raise ValueError(
                    "Mapping provided as dict must be a Constant or Timeseries"
                )

        if not isinstance(mapping, Mapping):
            raise ValueError(
                "Input mapping must be a Mapping or a dict that can construct a Mapping."
            )

        if mapping.mode not in [x.mode for x in self.mapping]:
            self.mapping.append(mapping)
        else:
            raise ValueError(
                f"Mapping for mode {mapping.mode} already exists in attribute {self.name}"
            )

    def print_report(self):
        """
        Print a report of the attribute
        """
        print("Attribute Report")
        print(f"Name: {self.name}")
        print(f"Identifier: {self.identifier}")
        print(f"Description: {self.description}")
        print(f"Alias: {self.alias}")
        print(f"Type: {self.type}")
        print("Mappings:")
        for mapping in self.mapping:
            print(f"  {mapping}")

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Attribute):
            return NotImplemented

        return (
            self.name == value.name
            and self.identifier == value.identifier
            and self.description == value.description
            and self.alias == value.alias
            and self.type == value.type
            and len(self.mapping) == len(value.mapping)
            and all(self.mapping[i] in value.mapping for i in range(len(self.mapping)))
        )

    def __str__(self):
        alias = self.alias if self.alias else "''"
        description = self.description if self.description else "''"
        return f"Attribute: {self.name} - ({self.identifier}) - {alias} - {self.type} - {description}"


class ModelTemplate:
    """
    Class defining model templates, i.e., models with a set of attributes.

    An instantiated model with mappings to a specific object is called a Model.
    """

    def __init__(self, yaml: Union[dict, str]):
        """
        Initializes the model from a YAML input.

        Args:
            yaml (Union[dict, str]): The model data, either as a dictionary, a YAML string, or a path to a YAML file.

        Raises:
            ValueError: If the input is not a dict or a YAML string.
            ValueError: If required keys ('owner', 'name') are missing in the model data.
            ValueError: If the 'attribute' field is present but not a list or dict.

        Behavior:
            - Loads model data from a dict, YAML string, or YAML file.
            - Extracts the 'model' key if present.
            - Sets 'owner', 'name', 'description', and 'version' attributes.
            - Processes 'attribute' field as a list of Attribute objects or dict of attributes.
        """
        if isinstance(yaml, dict):
            data = yaml
        else:
            if not isinstance(yaml, str):
                raise ValueError("Input yaml must be a dict or a yaml string")
            if os.path.isfile(yaml):
                with open(yaml, "r") as f:
                    data = pyyaml.safe_load(f)
            else:
                data = pyyaml.safe_load(yaml)

        if "model" in data.keys():
            data = data["model"]

        if "owner" not in data.keys():
            raise ValueError("Model data must contain an 'owner' key")
        self.owner = str(data.get("owner"))
        if "name" not in data.keys():
            raise ValueError("Model data must contain a 'name' key")
        self.name = str(data.get("name"))
        self.description = str(data.get("description") or "")
        self.version = str(data.get("version") or "")

        self.attribute = []
        if "attribute" in data.keys():
            attributes = data["attribute"]
            if isinstance(attributes, list):
                self.attribute = copy.deepcopy(attributes)
            elif isinstance(attributes, dict):
                for attkey in attributes.keys():
                    self.attribute.append(Attribute(attkey, attributes[attkey]))
            else:
                raise ValueError("Attribute data must be a list or a dict")

    def get_attribute(self, name: str) -> Attribute:
        """
        Get an attribute by name
        """
        for attribute in self.attribute:
            if attribute.name == name:
                return attribute

        for attribute in self.attribute:
            if name in attribute.alias:
                return attribute

        for attribute in self.attribute:
            if attribute.identifier == name:
                return attribute
        raise ValueError(f"Attribute {name} not found in model {self.name}")

    def as_dict(self) -> dict:
        data = self.__dict__.copy()
        data["attribute"] = {}
        for att in self.attribute:
            if isinstance(att, Attribute):
                data["attribute"][att.name] = att.__dict__.copy()
                # Model template instances shall not contain mapping data
                data["attribute"][att.name].pop("mapping", None)

        return data

    def get_yaml_file(self, filename: str = ""):
        """
        Saves the model template including attributes to a YAML file.

        If a filename is not provided or is empty, the filename is generated using the object's
        `owner` and `name` attributes in the format '{owner}_{name}.yaml'. If the provided filename
        does not end with '.yaml', the extension is appended automatically.

        Args:
            filename (str, optional): The name of the YAML file to write to. Defaults to an empty string,
                which triggers automatic filename generation.

        Returns:
            None

        Raises:
            Exception: Propagates any exceptions raised during file writing.
        """
        if filename is None or len(filename) == 0:
            filename = f"{self.owner}_{self.name}.yaml"

        if not filename.endswith(".yaml"):
            filename += ".yaml"

        with open(filename, "w") as f:
            pyyaml.dump(
                {"model": self.as_dict()}, f, sort_keys=False, default_flow_style=False
            )

    def get_yaml(self):
        """
        Get the YAML string for the model template including attributes
        """

        d = {"model": self.as_dict()}
        return pyyaml.dump(d, sort_keys=False, default_flow_style=False)

    def print_report(self):
        """
        Print a report of the model template
        """
        print("Generic Model Template Report")
        print(f"Model Owner: {self.owner}")
        print(f"Model Name: {self.name}")
        print(f"Model Description: {self.description}")
        print(f"Model Version: {self.version}")
        print("Attributes:")
        for attribute in self.attribute:
            print(f"  {attribute}")

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ModelTemplate):
            return NotImplemented

        return (
            self.owner == value.owner
            and self.name == value.name
            and self.description == value.description
            and self.version == value.version
            and len(self.attribute) == len(value.attribute)
            and all(
                self.attribute[i] in value.attribute for i in range(len(self.attribute))
            )
        )

    def __str__(self):
        return f"Generic Model Template: {self.owner} - {self.name} - {self.description} - {self.version}"


class Model(ModelTemplate):
    """
    Generic model class including mappings
    """

    def __init__(self, data: dict[str, str]):
        """Initialize a Model object.

        Args:
            data (dict[str, str]): Input data for the model. The dictionary should contain
                the keys "name", "description", "comment", "owner", and "object_name" to set
                the corresponding attributes.

        Raises:
            ValueError: If the input is not a dict or a YAML string.
            ValueError: If required keys ('owner', 'name', 'object_name') are missing in the model data.
            ValueError: If the 'attribute' field is present but not a list or dict.
        """
        super().__init__(data)

        if not isinstance(data, dict):
            raise ValueError("Input data must be a dict")

        # Model object name is the unique identifier for the object the model is associated with
        if "object_name" not in data.keys() or len(data["object_name"]) == 0:
            raise ValueError("Input data must contain a valid 'object_name' key")
        self.object_name = data["object_name"]
        self.comment = data.get("comment", "")

    def add_attribute(
        self,
        type: Literal["constant", "timeseries"],
        name: str,
        identifier: Optional[str] = "",
        description: Optional[str] = "",
        alias: Optional[Union[str, List[str]]] = "",
    ):
        """
        Add an attribute to the model.
        """

        if not identifier or len(identifier) == 0:
            identifier = name.lower().replace(" ", "_")

        if identifier != identifier.lower().replace(" ", "_"):
            raise ValueError(
                "Invalid identifier. Capital letters and whitespace is not allowed."
            )

        if not identifier or not type:
            raise ValueError("Identifier and type are required")

        attr = Attribute(
            name,
            {
                "identifier": identifier,
                "type": type,
                "description": description,
                "alias": alias,
            },
        )

        if attr.name in [a.name for a in self.attribute]:
            raise ValueError(f"Attribute {attr.name} already exists in the model")

        if attr.identifier in [a.identifier for a in self.attribute]:
            raise ValueError(
                f"Identifier {attr.identifier} already exists in the model"
            )

        self.attribute.append(attr)

    def add_constant_attribute(
        self,
        name: str,
        identifier: Optional[str] = "",
        description: Optional[str] = "",
        alias: Optional[Union[str, List[str]]] = "",
    ):
        """
        Add an attribute of type Constant to the model.
        """
        self.add_attribute("constant", name, identifier, description, alias)

    def add_timeseries_attribute(
        self,
        name: str,
        identifier: Optional[str] = "",
        description: Optional[str] = "",
        alias: Optional[Union[str, List[str]]] = "",
    ):
        """
        Add an attribute of type Timeseries to the model.

        Parameters:
            name (str): The name of the timeseries attribute.
            identifier (Optional[str], optional): A unique identifier for the attribute. Defaults to an empty string.
            description (Optional[str], optional): A description of the attribute. Defaults to an empty string.
            alias (Optional[str], optional): An alternative name for the attribute. Defaults to an empty string.

        Returns:
            None
        """

        self.add_attribute("timeseries", name, identifier, description, alias)

    def add_mapping(self, attribute_name, mapping: Union[Constant, Timeseries, dict]):
        """
        Add an attribute to the model
        """

        if isinstance(mapping, dict):
            if "ConstantValue" in mapping.keys():
                mapping = Constant(mapping)
            elif "Timeseries" in mapping.keys():
                mapping = Timeseries(mapping)
            else:
                raise ValueError("Mapping must be a Constant or Timeseries")

        if not isinstance(mapping, (Constant, Timeseries)):
            raise ValueError("Input data must be a Constant or Timeseries")

        if attribute_name in [a.name for a in self.attribute]:
            # Update existing attribute
            for i, attr in enumerate(self.attribute):
                if attr.name == attribute_name:
                    if attr.type.lower() == mapping.__class__.__name__.lower():
                        self.attribute[i].add_mapping(mapping)
                    else:
                        raise ValueError(
                            f"Attribute {attribute_name} is a {attr.type} while mapping is a {mapping.__class__.__name__}"
                        )
        elif attribute_name in [a.identifier for a in self.attribute]:
            # Update existing attribute
            for i, attr in enumerate(self.attribute):
                if attr.identifier == attribute_name:
                    if attr.type.lower() == mapping.__class__.__name__.lower():
                        self.attribute[i].add_mapping(mapping)
                    else:
                        raise ValueError(
                            f"Attribute {attribute_name} is a {attr.type} while mapping is a {mapping.__class__.__name__}"
                        )
        else:
            raise ValueError(
                f"Attribute {attribute_name} does not exist in the model. Please add it first."
            )

    def add_constant_mapping(
        self,
        attribute_name: str,
        value: str,
        unit_of_measure: Optional[str] = None,
        comment: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        """
        Add an  of type Constant to the model. If the attribute already exists,
        it will be updated.
        """

        self.add_mapping(
            attribute_name,
            Constant.create(
                value=value,
                unit_of_measure=unit_of_measure,
                comment=comment,
                mode=mode,
            ),
        )

    def add_timeseries_mapping(
        self,
        attribute_name: str,
        tagNo: str,
        source: str,
        unit_of_measure: Optional[str] = None,
        comment: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        """
        Add a mapping of type Timeseries to the attribute. If a mapping with the the same mode already exists,
        it will be updated.
        """

        self.add_mapping(
            attribute_name,
            Timeseries.create(
                tag=tagNo,
                source=source,
                unit_of_measure=unit_of_measure,
                comment=comment,
                mode=mode,
            ),
        )

    def post_mappings(self, model_owner: str = "", model_name: str = ""):
        """
        Posts attribute mappings for the current model to the backend.

        This method iterates over all attributes of the model and collects their mappings.
        For each mapping, it determines whether it is a Constant or Timeseries mapping,
        constructs the appropriate mapping dictionary, and appends it to a list.
        If any mappings are found, they are posted using the `post_generic_model_mapping` function.

        Args:
            model_owner (str, optional): The owner of the model. If not provided or empty, defaults to `self.owner`.
            model_name (str, optional): The name of the model. If not provided or empty, defaults to `self.name`.

        Returns:
            None
        """
        if model_owner is None or len(model_owner) == 0:
            model_owner = self.owner

        if model_name is None or len(model_name) == 0:
            model_name = self.name

        mappings = []
        for att in self.attribute:
            for mapping in att.mapping:
                if isinstance(mapping, Constant):
                    mappings.append(
                        make_constant_mapping_dict(
                            object_name=self.object_name,
                            model_owner=model_owner,
                            model_name=model_name,
                            attribute_name=att.name,
                            value=mapping.value,
                            mode=mapping.mode,
                            unit_of_measure=mapping.unit_of_measure,
                            comment=mapping.comment,
                        )
                    )
                elif isinstance(mapping, Timeseries):
                    mappings.append(
                        make_timeseries_mapping_dict(
                            object_name=self.object_name,
                            model_owner=model_owner,
                            model_name=model_name,
                            attribute_name=att.name,
                            time_series_tag_no=mapping.tag,
                            timeseries_source=mapping.source,
                            mode=mapping.mode,
                            unit_of_measure=mapping.unit_of_measure,
                            comment=mapping.comment,
                        )
                    )
        if len(mappings) > 0:
            post_generic_model_mapping(mappings)

    def get_mappings(self):
        """
        Retrieves mapping configurations for the current model and processes each mapping.

        For each mapping retrieved:
          - If the mapping contains a "ConstantValue", it adds a constant mapping using `add_constant_mapping`.
          - Otherwise, it adds a timeseries mapping using `add_timeseries_mapping`.

        The mappings are fetched based on the model's owner, name, and object name.

        Returns:
            None
        """
        mappings = get_mappings(
            model_owner=self.owner, model_name=self.name, object_name=self.object_name
        )
        for map in mappings:
            if "constant_value" in map.keys() and map["constant_value"] is not None:
                self.add_constant_mapping(
                    attribute_name=map["attribute_name"],
                    value=map["constant_value"],
                    unit_of_measure=map["unit_of_measure"],
                    comment=map["comment"],
                    mode=map["mode"],
                )
            elif (
                "timeseries_tag_number" in map.keys()
                and map["timeseries_tag_number"] is not None
            ):
                self.add_timeseries_mapping(
                    map["attribute_name"],
                    map["timeseries_tag_number"],
                    map["timeseries_source"],
                    unit_of_measure=map["unit_of_measure"],
                    comment=map["comment"],
                    mode=map["mode"],
                )
            else:
                logger.warn("Mapping is neither Constant nor Timeseries")

    def print_report(self):
        """
        Print a report of the model
        """
        print("Model Report")
        print(f"Model Object Name: {self.object_name}")
        print(f"Model Comment: {self.comment}")
        print(f"Model Owner: {self.owner}")
        print(f"Model Name: {self.name}")
        print(f"Model Description: {self.description}")
        print(f"Model Version: {self.version}")
        print("Attributes:")
        for attribute in self.attribute:
            print(f"  {attribute}")
            for mapping in attribute.mapping:
                print(f"    {mapping}")

    def as_dict(self) -> dict:
        data = self.__dict__.copy()
        data["attribute"] = {}
        for att in self.attribute:
            if isinstance(att, Attribute):
                curr_att = att.__dict__.copy()
                curr_att["mapping"] = [x.__dict__ for x in curr_att["mapping"]]
                data["attribute"][att.name] = curr_att

        return data

    def to_json(self, file_path: Optional[str] = None, indent: int = 0):
        if file_path is None or len(file_path) == 0:
            return json.dumps(self, default=vars, indent=indent)

        with open(file_path, "w") as f:
            json.dump(self, f, default=vars, indent=indent)

    @staticmethod
    def from_ModelTemplate(
        model_template: ModelTemplate, object_name: str = "", comment: str = ""
    ) -> "Model":
        """
        Create a Model from a ModelTemplate.
        This method copies the attributes from the ModelTemplate and adds the object_name and comment.
        Args:
            model_template (ModelTemplate): The ModelTemplate to copy attributes from.
            object_name (str): The unique identifier for the object the model is associated with.
            comment (str): An optional comment for the model.
        Returns:
            Model: A new Model instance with attributes copied from the ModelTemplate.
        """
        if not isinstance(model_template, ModelTemplate):
            raise ValueError("Input data must be a ModelTemplate")

        data = copy.deepcopy(model_template.__dict__)
        data["object_name"] = object_name
        data["comment"] = comment

        return Model(data=data)

    @staticmethod
    def get_model(
        object_name: str,
        model_name: str,
        model_owner: str = "",
        get_from_api: bool = True,
    ):
        """
        Get a model including any mapping data from the API, without following schema.
        """

        data = {}
        data["description"] = ""
        if get_from_api:
            mappings = get_mappings(
                model_owner=model_owner, model_name=model_name, object_name=object_name
            )

            # todo: convert ValueError to a warning?
            if not mappings or len(mappings) == 0:
                raise ValueError("No mappings found for model")

            data["name"] = mappings[0]["model_name"]
            data["owner"] = mappings[0]["model_owner"]
            data["object_name"] = mappings[0]["unique_object_identifier"]
        else:
            data["name"] = model_name
            data["owner"] = model_owner
            data["object_name"] = object_name
            mappings = []

        mod = Model(data=data)
        for map in mappings:
            if "constant_value" in map.keys():
                mod.add_constant_attribute(name=map["attribute_name"])
                mod.add_constant_mapping(
                    attribute_name=map["attribute_name"],
                    value=map["constant_value"],
                    unit_of_measure=map["unit_of_measure"],
                    comment=map["comment"],
                    mode=map["mode"],
                )
            else:
                mod.add_timeseries_attribute(name=map["attribute_name"])
                mod.add_timeseries_mapping(
                    attribute_name=map["attribute_name"],
                    tagNo=map["timeseries_tag_number"],
                    source=map["timeseries_source"],
                    unit_of_measure=map["unit_of_measure"],
                    comment=map["comment"],
                    mode=map["mode"],
                )

        return mod
