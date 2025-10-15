from tagmapper.connector_api import get_api_client
import pandas as pd
from typing import Optional, List


def get_data_base_well(
    facility_names: Optional[List[str]] = None, limit: int = 10, offset: int = 0
) -> pd.DataFrame:
    if facility_names is None:
        facility_names = []

    query_params = []
    for name in facility_names:
        query_params.append(f"gov_fcty_name={name.replace(' ', '%20')}")

    query_params.append(f"limit={limit}")
    query_params.append(f"offset={offset}")
    query_string = "&".join(query_params)

    url = f"/well-attributes-mapped-to-timeseries-base?{query_string}"
    response = get_api_client().get_json(url)
    df = pd.DataFrame(response["data"])
    return df


def get_data_base_separator(
    facility_names: Optional[List[str]] = None, limit: int = 10, offset: int = 0
) -> pd.DataFrame:
    if facility_names is None:
        facility_names = []

    query_params = []
    for name in facility_names:
        query_params.append(f"gov_fcty_name={name.replace(' ', '%20')}")

    query_params.append(f"limit={limit}")
    query_params.append(f"offset={offset}")
    query_string = "&".join(query_params)

    url = f"/separator-attributes-mapped-to-timeseries-base?{query_string}"
    response = get_api_client().get_json(url)
    df = pd.DataFrame(response["data"])
    return df
