from gzspidertools.config import setup_lazy_import

_MODULES = {
    "headers.ua": ["RandomRequestUaMiddleware"],
    "netlib.aiohttplib": ["AiohttpDownloaderMiddleware"],
    "proxy.dynamic": [
        "AbuDynamicProxyDownloaderMiddleware",
        "DynamicProxyDownloaderMiddleware",
    ],
    "proxy.exclusive": ["ExclusiveProxyDownloaderMiddleware"],
    "drissionpage.drissionpage": ["DrissionPageMiddleware"]
}

setup_lazy_import(
    modules_map=_MODULES,
    base_package="gzspidertools.scraper.middlewares",
    globals_dict=globals(),
)
