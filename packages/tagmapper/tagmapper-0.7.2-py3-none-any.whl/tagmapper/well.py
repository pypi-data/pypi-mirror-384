from typing import List
import pandas as pd

from tagmapper.mapping import Timeseries
from tagmapper.base_model import get_data_base_well


class Well:
    """
    Well class
    """

    _well_attributes = pd.DataFrame()

    def __init__(self, uwi):
        if isinstance(uwi, str):
            # assume data is UWI
            data = Well.get_well_attributes(uwi)
        elif isinstance(uwi, pd.DataFrame):
            data = uwi

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a dataframe")

        if data.empty:
            raise ValueError("Input data can not be empty")
        self.uwi = data["unique_well_identifier"].iloc[0]

        self.attributes = []
        for _, r in data.iterrows():
            self.attributes.append(Timeseries(r.to_dict()))

    def __str__(self):
        return f"Well: {self.uwi}"

    @classmethod
    def get_all_wells(cls):
        uwi = Well.get_uwis()
        well = []

        for u in uwi:
            well.append(Well(Well.get_well_attributes(u)))

        return well

    @classmethod
    def get_well(cls, inst_code: str, tag_no: str):
        return Well(Well.get_well_attributes(f"{inst_code}-{tag_no}"))

    @classmethod
    def get_well_attributes(cls, uwi: str = ""):
        if cls._well_attributes.empty:
            cls._well_attributes = get_data_base_well(limit=1000000, offset=0)
        if uwi:
            ind = cls._well_attributes["unique_well_identifier"] == uwi
            return cls._well_attributes.loc[ind, :]
        else:
            return cls._well_attributes

    @staticmethod
    def get_uwis(facility: str = "") -> List[str]:
        d = Well.get_well_attributes()
        if facility:
            # facility name is no longer in table
            raise NotImplementedError(
                "Filtering by facility is not currently supported"
            )
        uwi = list(d["unique_well_identifier"].unique())
        uwi.sort()
        return uwi
