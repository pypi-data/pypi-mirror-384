from gzspidertools.config import setup_lazy_import

_MODULES = {
    "impersonate.ImpersonateDownloadHandler": ["ImpersonateDownloadHandler"],
    "aiohttp.AiohttpDownloadHandler": ["AiohttpDownloadHandler"],

}

setup_lazy_import(
    modules_map=_MODULES,
    base_package="gzspidertools.scraper.handlers",
    globals_dict=globals(),
)
