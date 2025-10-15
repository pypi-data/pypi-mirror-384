import logging
import os
from arthub_api import utils
from arthub_api import OpenAPI
from arthub_api import api_config_oa_test
from contextlib import contextmanager

TEST_DEPOT_NAME = "apg"


def on_api_failed(res):
    logging.error("[TEST][API] \"%s\" failed, error: %s" % (res.url, res.error_message()))


@contextmanager
def set_env_var(name, value):
    original_value = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if original_value is None:
            del os.environ[name]
        else:
            os.environ[name] = original_value


def test_blade_env():
    with set_env_var("BLADE_NETWORK_TYPE", "oa_test"):
        open_api = OpenAPI(apply_blade_env=True)
        assert open_api.config == api_config_oa_test


def test_account(open_api):
    assert open_api.is_login()
    assert open_api.get_account_phone()
    assert open_api.get_account_qywx_name()
    assert open_api.get_account_qywx_alias()
    assert open_api.get_account_nick_name()
    assert open_api.get_account_department()
    assert open_api.get_account_company()
    assert open_api.get_account_icon_url()
    assert open_api.get_account_email()


def test_depot_get_root_id(open_api):
    res = open_api.depot_get_root_id(TEST_DEPOT_NAME)
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, depot id: %d" % (res.url, res.results.get(0)))


def test_depot_get_node_brief_by_ids(open_api):
    res = open_api.depot_get_node_brief_by_ids(TEST_DEPOT_NAME, [120347220059298, 120347220059299])
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    node_1 = res.results.get(0)
    node_2 = res.results.get(1)
    logging.info("[TEST][API] \"%s\" success, name_1: %s, name_2: %s" % (res.url, node_1["name"], node_2["name"]))


def test_depot_get_child_node_count(open_api):
    res = open_api.depot_get_child_node_count(TEST_DEPOT_NAME, [120347220059339])
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, count: %d" % (res.url, res.results.get(0)["count"]))


def test_depot_get_download_signature(open_api):
    res = open_api.depot_get_download_signature(TEST_DEPOT_NAME,
                                                nodes=[{"object_id": 120347220059338, "object_meta": "origin_url"}])
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, signed url: %s" % (res.url, res.results.get(0)["signed_url"]))


def test_depot_get_upload_signature(open_api):
    file_name = "new_asset_to_upload"
    res_0 = open_api.depot_create_asset(TEST_DEPOT_NAME, [{
        "parent_id": 120347220059339,
        "name": file_name,
        "add_new_version": False
    }])
    if not res_0.is_succeeded():
        on_api_failed(res_0)
        assert 0

    asset_id = res_0.results.get(0)["id"]

    res_1 = open_api.depot_get_upload_signature(TEST_DEPOT_NAME, nodes=[
        {"object_id": asset_id, "object_meta": "origin_url", "file_name": file_name}])
    if not res_1.is_succeeded():
        on_api_failed(res_1)
        assert 0

    logging.info("[TEST][API] \"%s\" success, signed url: %s" % (res_1.url, res_1.results.get(0)["signed_url"]))


def test_depot_get_child_node_id_in_range(open_api):
    res = open_api.depot_get_child_node_id_in_range(TEST_DEPOT_NAME, parent_id=120347220059339, offset=0, count=2,
                                                    query_filters=[{"meta": "type", "condition": "x != directory"}],
                                                    is_recursive=True)
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    nodes = res.results.get(0)["nodes"]
    logging.info("[TEST][API] \"%s\" success" % res.url)


def test_depot_get_node_brief_by_path(open_api):
    res = open_api.depot_get_node_brief_by_path(TEST_DEPOT_NAME, root_id=120347220059296,
                                                path="open_api_test/asset.jpg")
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    node = res.results.get(0)
    logging.info("[TEST][API] \"%s\" success, name: %s" % (res.url, node["name"]))


def test_depot_add_asset_tag(open_api):
    new_tag_name = utils.get_random_string(5)
    res = open_api.depot_add_asset_tag(TEST_DEPOT_NAME, asset_id=120347220059344, tag_name=[new_tag_name])
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    new_tag_id = res.results.get(0)
    logging.info("[TEST][API] \"%s\" success, new tag id: %d" % (res.url, new_tag_id))

    res = open_api.depot_get_asset_tag(TEST_DEPOT_NAME, asset_id=120347220059344)
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0
    find_new_tag = False
    for tag in res.result:
        if tag["id"] == new_tag_id and tag["tag_name"] == new_tag_name:
            find_new_tag = True
            break
    if not find_new_tag:
        assert 0
    logging.info("[TEST][API] \"%s\" success" % res.url)


def test_get_account_detail(open_api):
    res = open_api.get_account_detail()
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, email: %s" % (res.url, res.results.get(0)["email"]))


def test_get_ticket(open_api):
    res = open_api.get_ticket()
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, ticket: %s" % (res.url, res.results.get(0)))


def test_get_last_access_location_by_account(open_api):
    res = open_api.get_last_access_location_by_account()
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, last access location: %s" % (res.url, res.results.get(0)))


def test_depot_create_directory(open_api):
    res = open_api.depot_create_directory(TEST_DEPOT_NAME, [{
        "parent_id": 120347220059339,
        "name": "new_dir",
        "allowed_rename": True,
        "return_existing_id": False
    }])
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, new dir id: %s" % (res.url, res.results.get(0)["id"]))


def test_depot_create_multi_asset(open_api):
    res = open_api.depot_create_multi_asset(TEST_DEPOT_NAME, [{
        "parent_id": 120347220059339,
        "name": "new_multi_asset"
    }])
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success, new multi asset id: %s" % (res.url, res.results.get(0)["id"]))


def test_depot_move_node(open_api):
    res = open_api.depot_move_node(TEST_DEPOT_NAME, ids=[120347220064827], other_parent_id=120347220064825)
    if not res.is_succeeded():
        on_api_failed(res)
        assert 0

    logging.info("[TEST][API] \"%s\" success" % res.url)
