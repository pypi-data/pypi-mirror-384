from gzspidertools.config import setup_lazy_import

_MODULES = {
    "prometheus.PrometheusWebService": ["PrometheusWebService"],
}

setup_lazy_import(
    modules_map=_MODULES,
    base_package="gzspidertools.scraper.extensions",
    globals_dict=globals(),
)
