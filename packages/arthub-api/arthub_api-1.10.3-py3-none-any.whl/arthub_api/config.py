"""
arthub_api.config
~~~~~~~~~~~~~~

This module provides configure that are used within API
"""
# online configuration
_api_host_oa = "service.arthub.woa.com"
_api_host_qq = "service.arthub.qq.com"
_api_host_public = "api.arthubdam.com"
_client_proxy_host_oa = "client-proxy.arthub.woa.com"
_client_proxy_host_qq = "client-proxy.arthub.qq.com"
_client_proxy_host_public = "client-proxy.arthubdam.com"

_api_host_oa_test = "arthub-service-test.woa.com"
_api_host_qq_test = "arthub-innertest.qq.com"
_client_proxy_host_oa_test = "arthub-client-proxy-test.woa.com"
_client_proxy_host_qq_test = "arthub-storage-1.qq.com"

# config for access ArtHub intranet domain
api_config_oa = {
    "http_scheme": "http:",
    "web_socket_scheme": "ws:",
    "host": _api_host_oa,
    "client_proxy_host": _client_proxy_host_oa,
    "timeout": 10,
}

# config for access ArtHub extranet domain
api_config_qq = {
    "http_scheme": "https:",
    "web_socket_scheme": "wss:",
    "host": _api_host_qq,
    "client_proxy_host": _client_proxy_host_qq,
    "timeout": 10,
}

# config for access ArtHub public cloud version
api_config_public = {
    "http_scheme": "https:",
    "web_socket_scheme": "wss:",
    "host": _api_host_public,
    "client_proxy_host": _client_proxy_host_public,
    "timeout": 10,
}

# config for internal test
api_config_oa_test = {
    "http_scheme": "http:",
    "web_socket_scheme": "ws:",
    "host": _api_host_oa_test,
    "client_proxy_host": _client_proxy_host_oa_test,
    "timeout": 10,
}

# config for internal test
api_config_qq_test = {
    "http_scheme": "https:",
    "web_socket_scheme": "wss:",
    "host": _api_host_qq_test,
    "client_proxy_host": _client_proxy_host_qq_test,
    "timeout": 10,
}
