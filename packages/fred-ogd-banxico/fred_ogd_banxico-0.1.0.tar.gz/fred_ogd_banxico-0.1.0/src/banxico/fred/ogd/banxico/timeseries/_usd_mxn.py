import os
import textwrap
from typing import Optional

import yaml

from fred.ogd.banxico.timeseries.interface import BanxicoTimeSeriesInterface


class BanxicoTimeSeriesUsdMxn(BanxicoTimeSeriesInterface):

    @classmethod
    def from_config(cls, serie: str, filepath: Optional[str] = None) -> "BanxicoTimeSeriesUsdMxn":
        filepath = filepath or os.path.join(os.path.dirname(__file__), "_usd_mxn.yaml")
        if not filepath.endswith(".yaml"):
            raise ValueError("The file must be a YAML file with .yaml extension")
        with open(filepath, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        series_data = data.get("series", {}).get(serie)
        if not series_data:
            raise ValueError(f"Series '{serie}' not found in the YAML file.")
        return cls(
            code=series_data.get("code", serie),
            description=textwrap.dedent(series_data.get("description", "")).strip() or None,
            reference=data.get("reference"),
        )
