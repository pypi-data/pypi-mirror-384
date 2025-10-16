from abc import ABC
from typing import Optional


class Mapping(ABC):
    """
    Abstract mapping class.

    A mapping refers to a single row in generic model table. It is an instantiation
    of a generic model attribute. In the table there is also

    Currently two types of mappings are supported:
    - Timeseries: a timeseries attribute
    - Constant: a constant attribute
    """

    def __init__(self, data):
        """Initialize a Mapping object.

        Args:
            data (dict): Input data for the mapping. The dictionary should contain
                the keys "attribute_name", "description", "comment", "mode", and
                "unit_of_measure" to set the corresponding attributes.
        """
        self.mode = ""
        self.comment = ""
        self.unit_of_measure = ""

        if isinstance(data, dict):
            self.from_dict(data)

    def from_dict(self, data):
        """Update a Mapping object from a dictionary.

        Args:
            data (dict): Input data for the mapping. The dictionary should contain
                the keys "comment", "mode", and "unit_of_measure" to set the
                corresponding attributes.

        Raises:
            ValueError: If the input data is not a dictionary.
        """
        self.comment = ""
        self.mode = ""
        self.unit_of_measure = ""

        if not isinstance(data, dict):
            raise ValueError("Input data must be a dict")

        if "comment" in data.keys():
            self.comment = data["comment"]
        elif "mapped_comment" in data.keys():
            self.comment = data["mapped_comment"]

        if "mode" in data.keys():
            self.mode = data["mode"]
        else:
            pass

        if "unit_of_measure" in data.keys():
            self.unit_of_measure = data["unit_of_measure"]
        elif "UnitOfMeasure" in data.keys():
            self.unit_of_measure = data["UnitOfMeasure"]
        else:
            # Well data does not contain unit of measure
            pass

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Mapping):
            return NotImplemented

        return (
            self.comment == value.comment
            and self.mode == value.mode
            and self.unit_of_measure == value.unit_of_measure
        )

    @staticmethod
    def _create_mapping_data_dict(
        comment: Optional[str] = "",
        mode: Optional[str] = "",
        unit_of_measure: Optional[str] = "",
    ) -> dict:
        """
        Create a mapping object from a dictionary
        """

        data = {}
        if comment is not None:
            if not isinstance(comment, str):
                raise ValueError("Input data must be a string")
            data["comment"] = comment

        if mode is not None:
            if not isinstance(mode, str):
                raise ValueError("Input data must be a string")
            data["mode"] = mode

        if unit_of_measure is not None:
            if not isinstance(unit_of_measure, str):
                raise ValueError("Input data must be a string")
            data["unit_of_measure"] = unit_of_measure

        return data


class Timeseries(Mapping):
    """
    Timeseries mapping class.
    """

    def __init__(self, data):
        """Initialize a Timeseries mapping object.

        Args:
            data (dict): Input data for the mapping. The dictionary shall contain
                the keys "tag" and "source" to set the corresponding attributes.
                The dictionary can also contain the keys "comment", "mode", and
                "unit_of_measure" to set the corresponding attributes.
        """
        self.tag = ""
        self.source = ""

        super().__init__(data)

    def from_dict(self, data):
        """
        Update a Timeseries object from a dictionary
        """
        self.tag = ""
        self.source = ""

        super().from_dict(data)

        # populate tag
        if "tag" in data.keys():
            self.tag = data["tag"]
        elif "TAG_ID" in data.keys():
            self.tag = data["TAG_ID"]
        elif "Tag_Id" in data.keys():
            self.tag = data["Tag_Id"]
        elif "timeseries_name" in data.keys():
            self.tag = data["timeseries_name"]
        elif "TimeSeriesTagNo" in data.keys():
            self.tag = data["TimeSeriesTagNo"]
        else:
            pass

        # populate source
        if "source" in data.keys():
            self.source = data["source"]
        elif "ims_collective" in data.keys():
            self.source = data["ims_collective"]
        elif "TimeseriesSource" in data.keys():
            self.source = data["TimeseriesSource"]
        else:
            pass

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Timeseries)
            and super().__eq__(value)
            and (self.tag == value.tag and self.source == value.source)
        )

    def __str__(self):
        return " ".join(
            filter(
                None,
                [
                    "Timeseries:",
                    f"{self.mode} -" if self.mode else None,
                    self.tag,
                    f"@ {self.source}",
                    f"[{self.unit_of_measure}]",
                    f"- {self.comment}" if self.comment else "''",
                ],
            )
        )

    @staticmethod
    def create(
        tag: str,
        source: str,
        comment: Optional[str] = "",
        mode: Optional[str] = "",
        unit_of_measure: Optional[str] = "",
    ) -> "Timeseries":
        data = Mapping._create_mapping_data_dict(
            comment=comment, mode=mode, unit_of_measure=unit_of_measure
        )

        if not isinstance(tag, str):
            raise ValueError("Input data must be a string")
        data["tag"] = tag
        if not isinstance(source, str):
            raise ValueError("Input data must be a string")
        data["source"] = source

        return Timeseries(data)


class Constant(Mapping):
    """
    Constant mapping class
    """

    def __init__(self, data):
        """Initialize a Constant mapping object.

        Args:
            data (dict): Input data for the mapping. The dictionary should contain
                the keys "value", "ConstantValue" to set the value.
                The dictionary can also contain the keys "comment", "mode", and
                "unit_of_measure" to set the corresponding attributes.
        """
        self.value = ""

        super().__init__(data)

    def from_dict(self, data):
        """
        Update a Constant object from a dictionary
        """
        self.value = ""

        super().from_dict(data)

        # populate value
        if "value" in data.keys():
            self.value = data["value"]
        elif "ConstantValue" in data.keys():
            self.value = data["ConstantValue"]
        else:
            pass

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Constant)
            and super().__eq__(value)
            and (self.value == value.value)
        )

    def __str__(self):
        return " ".join(
            filter(
                None,
                [
                    "Constant:",
                    f"{self.mode} -" if self.mode else None,
                    self.value,
                    f"[{self.unit_of_measure}]",
                    f"- {self.comment}" if self.comment else "''",
                ],
            )
        )

    @staticmethod
    def create(
        value: str,
        comment: Optional[str] = "",
        mode: Optional[str] = "",
        unit_of_measure: Optional[str] = "",
    ) -> "Constant":
        data = Mapping._create_mapping_data_dict(
            comment=comment, mode=mode, unit_of_measure=unit_of_measure
        )

        if not isinstance(value, str):
            raise ValueError("Input data must be a string")
        data["value"] = value

        return Constant(data)
