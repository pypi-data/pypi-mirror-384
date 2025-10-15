from fred.settings import get_environ_variable


FRDOGD_BANXICO_SERIES_URL = get_environ_variable(
    name="FRDOGD_BANXICO_SERIES_URL",
    default="https://www.banxico.org.mx/SieInternet/consultaSerieGrafica.do?s={serie_id}",
)

FRDOGD_SOURCE_FULLNAME = get_environ_variable(
    name="FRDOGD_SOURCE_FULLNAME",
    default="fred-ogd-source-banxico",
)

FRDOGD_BACKEND_SERVICE = get_environ_variable(
    name="FRDOGD_BACKEND_SERVICE",
    default="MINIO",
)
