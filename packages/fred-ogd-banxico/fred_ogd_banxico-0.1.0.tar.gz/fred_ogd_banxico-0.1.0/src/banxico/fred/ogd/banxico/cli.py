import os
from typing import Optional

from fred.cli.interface import AbstractCLI
from fred.utils.dateops import datetime_utcnow

from fred.ogd.layer.catalog import LayerCatalog
from fred.ogd.banxico.timeseries.catalog import BanxicoTimeSeriesCatalog
from fred.ogd.banxico.settings import (
    FRDOGD_SOURCE_FULLNAME,
    FRDOGD_BACKEND_SERVICE,
)


class OGDExtCLI(AbstractCLI):

    def timeseries(self) -> dict[str, str]:
        return {
            item.name: item.value.description or item.value.reference or item.value.code
            for item in BanxicoTimeSeriesCatalog
        }

    def landing(self, timeserie: str, backend: Optional[str] = None, **kwargs) -> str:
        from fred.ogd.source.catalog import SourceCatalog

        run_ts = datetime_utcnow()
        series = BanxicoTimeSeriesCatalog[timeserie]
        layer_type = LayerCatalog.LANDING
        layer = layer_type.auto(
            source=SourceCatalog.REQUEST.name,
            backend=backend or FRDOGD_BACKEND_SERVICE,  # e.g., MINIO
            source_kwargs={
                "target_url": series.value.url,
                **kwargs.pop("source_kwargs", {}),
            },
            backend_kwargs={
                **kwargs.pop("backend_kwargs", {}),
            },
        )
        return layer.run(
            output_path=os.path.join(
                FRDOGD_SOURCE_FULLNAME,
                layer_type.name.lower(),
                timeserie,
                run_ts.strftime("%Y"),
                run_ts.strftime("%m"),
            ),
            **kwargs,
        )
