from dataclasses import dataclass
from typing import Optional

import requests

from fred.monad._either import Either
from fred.ogd.banxico.settings import FRDOGD_BANXICO_SERIES_URL



@dataclass(frozen=True, slots=True)
class BanxicoTimeSeriesInterface:
    code: str
    description: Optional[str] = None
    reference: Optional[str] = None

    @property
    def url(self) -> str:
        return FRDOGD_BANXICO_SERIES_URL.format(serie_id=self.code)
    
    @property
    def request(self) -> Either[requests.Response]:
        return Either.from_value(self.url).map(
            lambda url: (response := requests.get(url)).raise_for_status() or response
        )
    
    def fetch(self) -> Either[dict]:
        return self.request.map(lambda response: response.json())
