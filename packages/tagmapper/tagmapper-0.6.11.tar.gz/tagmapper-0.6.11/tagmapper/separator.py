from typing import List
import pandas as pd

from tagmapper.mapping import Timeseries
from tagmapper.base_model import get_data_base_separator


class Separator:
    """
    Separator class
    """

    _sep_attributes = pd.DataFrame()

    def __init__(self, usi):

        if isinstance(usi, str):
            data = Separator.get_separator_attributes(usi)
        elif isinstance(usi, pd.DataFrame):
            if usi.empty:
                raise ValueError("Input dataframe is empty")
            data = usi

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a dataframe")

        if data.empty:
            if isinstance(usi, str):
                raise ValueError(f"No data found for {usi}")
            else:
                raise ValueError("Invalid input, empty dataframe provided.")

        self.usi = usi
        self.attributes = []
        for _, r in data.iterrows():
            self.attributes.append(Timeseries(r.to_dict()))

    def __str__(self):
        return f"Separator: ({self.usi})"

    @classmethod
    def get_all_separators(cls) -> List["Separator"]:
        usi = Separator._get_separator_names()
        sep = []

        for u in usi:
            sep.append(Separator(Separator.get_separator_attributes(u)))

        return sep

    @classmethod
    def get_separator(cls, inst_code: str, tag_no: str) -> "Separator":
        return Separator(Separator.get_separator_attributes(f"{inst_code}-{tag_no}"))

    @classmethod
    def get_separator_attributes(cls, usi: str = "") -> pd.DataFrame:
        if cls._sep_attributes.empty:
            cls._sep_attributes = get_data_base_separator(limit=1000, offset=0)

        if usi:
            ind = cls._sep_attributes["unique_separator_identifier"] == usi
            if not ind.any():
                raise ValueError(f"No separator found with USI: {usi}")
            return cls._sep_attributes.loc[ind, :]
        else:
            return cls._sep_attributes

    @staticmethod
    def _get_separator_names() -> List[str]:
        d = Separator.get_separator_attributes()
        usi = list(d["unique_separator_identifier"].unique())
        usi.sort()
        return usi

    @staticmethod
    def get_usi() -> List[str]:
        return Separator._get_separator_names()
