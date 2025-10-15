import pytest
from arthub_api import arthub_api_config
from arthub_api import OpenAPI
from arthub_api import Storage
from . import _utils


def pytest_addoption(parser):
    parser.addoption(
        "--env", action="store", default="qq",
        help="api config option: oa or qq or test_oa or test_qq"
    )


@pytest.fixture
def env(request):
    return request.config.getoption("--env")


@pytest.fixture()
def open_api(env):
    _c = _utils.get_config(env)
    open_api = OpenAPI(config=_c,
                       get_token_from_cache=False,
                       login_public_keys=arthub_api_config.login_public_keys)
    res = open_api.login(arthub_api_config.account_email, arthub_api_config.password)
    assert res.is_succeeded()
    return open_api


@pytest.fixture()
def storage(open_api):
    return Storage(open_api)
