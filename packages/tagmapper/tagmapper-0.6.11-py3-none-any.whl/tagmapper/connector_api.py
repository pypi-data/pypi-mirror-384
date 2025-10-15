import json
import logging
from types import SimpleNamespace
from typing import List, Literal, Optional, Union

from eq_api_connector import APIConnector
from requests import HTTPError


logger = logging.getLogger(__name__)

_client = None

_scope_client = "582e9f1c-1814-449b-ae6c-0cdc5fecdba2"


class TagMapperClient(APIConnector):
    def __init__(
        self,
        client_secret: Optional[str] = None,
        scope: Optional[Union[List[str], str]] = [
            f"{_scope_client}/user_impersonation"
        ],
        user_name: Optional[str] = None,
        user_assertion: Optional[str] = None,
    ):
        super().__init__(
            client_id="5850cfaf-0427-4e96-9813-a7874c8324ae",
            client_secret=client_secret,
            scope=scope,
            user_name=user_name,
            user_assertion=user_assertion,
        )
        self.set_url_prod("https://spdapi.radix.equinor.com")
        self.set_url_dev("https://spdapi-dev.radix.equinor.com")


def get_api_client():
    global _client
    if _client is None:
        _client = TagMapperClient()

    return _client


def get_object_from_json(text: str):
    if isinstance(text, list):
        obj = [json.loads(x, object_hook=lambda d: SimpleNamespace(**d)) for x in text]
    else:
        obj = json.loads(text, object_hook=lambda d: SimpleNamespace(**d))
    return obj


def get_generic_model_mappings(data: dict) -> List[dict[str, str]]:
    """Get generic model mappings from the API. Function is typically called from the Model class functions get_mappings().

    Args:
        data (dict): The data to send in the request. A dictionary with keys like "model_owner", "attribute_type", "model_name", and "unique_object_identifier".

    Raises:
        ValueError: If the response is not valid JSON object

    Returns:
        list: A list of generic model mappings
    """

    try:
        response = get_api_client().get_json("/get-model", params=data)
    except HTTPError as ex:
        if (
            ex.response.status_code == 404
            and "No such model exists at blob path" in ex.response.text
        ):
            return []
        raise ex

    if isinstance(response, dict):
        if "data" in response.keys():
            if isinstance(response["data"], list):
                return response["data"]
            else:
                return [response["data"]]
        raise ValueError("Response is not a valid JSON object")
    else:
        print(f"{response}")
        return []


def post_generic_model_mapping(data: Union[dict[str, str], List[dict[str, str]]]):
    """
    Post generic model mapping to the API
    """

    if isinstance(data, dict):
        data = [data]

    for d in data:
        d["AttributeName"] = d["AttributeName"].lower().replace(" ", "_")
        for key in d.keys():
            if d[key] is None:
                d[key] = ""

    response = get_api_client().post_file("/upload-model", {"data": data})
    return response


def post_timeseries_mapping(
    object_name: str,
    model_owner: str,
    model_name: str,
    attribute_name: str,
    time_series_tag_no: str,
    timeseries_source: str,
    mode: Optional[str] = "",
    unit_of_measure: Optional[str] = "",
    comment: Optional[str] = "",
):
    """
    Post a timeseries mapping to the API
    """
    timeseries_dict = make_timeseries_mapping_dict(
        object_name,
        model_owner,
        model_name,
        attribute_name,
        time_series_tag_no,
        timeseries_source,
        mode,
        unit_of_measure,
        comment,
    )

    return post_generic_model_mapping(timeseries_dict)


def make_timeseries_mapping_dict(
    object_name: str,
    model_owner: str,
    model_name: str,
    attribute_name: str,
    time_series_tag_no: str,
    timeseries_source: str,
    mode: Optional[str] = "",
    unit_of_measure: Optional[str] = "",
    comment: Optional[str] = "",
):
    if time_series_tag_no is None or len(time_series_tag_no) == 0:
        raise ValueError("Input time_series_tag_no must be a string with characters")

    if timeseries_source is None or len(timeseries_source) == 0:
        raise ValueError("Input timeseries_source must be a string with characters")

    timeseries_dict = {
        "unique_object_identifier": object_name,
        "model_owner": model_owner,
        "model_name": model_name,
        "mode": mode,
        "UnitOfMeasure": unit_of_measure,
        "TimeseriesSource": timeseries_source,
        "comment": comment,
        "AttributeName": attribute_name,
        "TimeSeriesTagNo": time_series_tag_no,
    }

    return timeseries_dict


def post_constant_mapping(
    object_name: str,
    model_owner: str,
    model_name: str,
    attribute_name: str,
    value: str,
    mode: Optional[str] = "",
    unit_of_measure: Optional[str] = "",
    comment: Optional[str] = "",
):
    """
    Post a constant mapping to the API
    """

    if value is None or len(value) == 0:
        raise ValueError("Input value must be a string with characters")

    return post_generic_model_mapping(
        make_constant_mapping_dict(
            object_name,
            model_owner,
            model_name,
            attribute_name,
            value,
            mode,
            unit_of_measure,
            comment,
        )
    )


def make_constant_mapping_dict(
    object_name: str,
    model_owner: str,
    model_name: str,
    attribute_name: str,
    value: str,
    mode: Optional[str] = "",
    unit_of_measure: Optional[str] = "",
    comment: Optional[str] = "",
):
    constant_dict = {
        "unique_object_identifier": object_name,
        "model_owner": model_owner,
        "model_name": model_name,
        "mode": mode,
        "UnitOfMeasure": unit_of_measure,
        "comment": comment,
        "AttributeName": attribute_name,
        "ConstantValue": value,
    }

    return constant_dict


def get_mappings(
    model_owner: str = "",
    model_name: str = "",
    object_name: str = "",
    attribute_type: Optional[Literal["constant", "timeseries"]] = None,
) -> List[dict[str, str]]:
    """
    Get generic model mappings from the API as List of dicts
    """

    if attribute_type is None:
        const = get_mappings(
            model_owner=model_owner,
            model_name=model_name,
            object_name=object_name,
            attribute_type="constant",
        )

        ts = get_mappings(
            model_owner=model_owner,
            model_name=model_name,
            object_name=object_name,
            attribute_type="timeseries",
        )
        const.extend(ts)
        return const

    model_dict = {
        "model_owner": model_owner,
        "attribute_type": str(attribute_type),
        "model_name": model_name,
        "unique_object_identifier": object_name,
    }

    return get_generic_model_mappings(data=model_dict)


def delete_mapping(
    model_owner: str,
    model_name: str,
    object_name: str,
    attribute_name: Optional[str] = None,
):
    if not (isinstance(model_owner, str) and len(model_owner) > 0):
        raise ValueError("Model owner must be a str.")

    if not (isinstance(model_name, str) and len(model_name) > 0):
        raise ValueError("Model name must be a str.")

    if not (isinstance(object_name, str) and len(object_name) > 0):
        raise ValueError("Object name must be a str.")

    params = {
        "model_owner": model_owner,
        "model_name": model_name,
        "unique_object_identifier": object_name,
    }
    if isinstance(attribute_name, str) and len(attribute_name) > 0:
        params["Attribute_Name"] = attribute_name

    response = get_api_client().post(url="/delete-mapping", params=params)

    return response
