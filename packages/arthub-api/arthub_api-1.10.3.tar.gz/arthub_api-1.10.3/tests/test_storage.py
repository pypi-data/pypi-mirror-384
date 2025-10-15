import pytest
import logging
import time

TEST_DEPOT_NAME = "apg"


def on_api_failed(res):
    logging.error("[TEST][STORAGE] \"%s\" failed, error: %s" % (res.url, res.error_message()))


def on_operation_failed(operation, error_message):
    logging.error("[TEST][STORAGE] %s failed, error: %s" % (operation, error_message))


@pytest.mark.run(order=1)
def test_transfer(tmp_path, storage):
    # download
    def download_progress_cb(completed, total):
        print("download progress: %d/%d" % (completed, total))

    since = time.time()
    res = storage.download_by_path(asset_hub=TEST_DEPOT_NAME,
                                   remote_node_path="arthub_api_test/storage_test/download",
                                   local_dir_path=str(tmp_path),
                                   same_name_override=False,
                                   progress_cb=download_progress_cb)
    if not res.is_succeeded():
        on_operation_failed("download", res.error_message())
        assert 0
    local_downloaded_path = res.data[0]
    logging.info("[TEST][STORAGE] download success, local downloaded path: %s, spend: %f s"
                 % (local_downloaded_path, time.time() - since))
    since = time.time()

    # upload downloaded dir
    def upload_progress_cb(completed, total):
        print("upload progress: %d/%d" % (completed, total))

    res = storage.upload_to_directory_by_path(asset_hub=TEST_DEPOT_NAME,
                                              remote_dir_path="arthub_api_test/storage_test/upload",
                                              local_path=local_downloaded_path,
                                              tags_to_create=["sdk_test"],
                                              same_name_override=False,
                                              need_convert=True,
                                              progress_cb=upload_progress_cb)
    if not res.is_succeeded():
        on_operation_failed("upload", res.error_message())
        assert 0
    logging.info("[TEST][STORAGE] upload success, remote uploaded id: %d, spend: %f s"
                 % (res.data[0], time.time() - since))


def test_get_node_by_path(storage):
    res = storage.get_node_by_path(asset_hub=TEST_DEPOT_NAME, remote_node_path="arthub_api_test/storage_test/download")
    if not res.is_succeeded():
        on_operation_failed("get remote node info", res.error_message())
        assert 0
    logging.info("[TEST][STORAGE] get remote node info success, id: %d, type: %s" % (res.data["id"], res.data["type"]))


def test_delete_node_by_path(storage):
    res = storage.delete_node_by_path(asset_hub=TEST_DEPOT_NAME, remote_node_path="arthub_api_test/storage_test/upload")
    if not res.is_succeeded():
        on_operation_failed("delete remote node info", res.error_message())
        assert 0
    logging.info("[TEST][STORAGE] delete remote node %d success" % res.data)


def test_get_child_nodes(storage):
    res = storage.get_child_nodes(asset_hub=TEST_DEPOT_NAME, parent_path="arthub_api_test/storage_test/download/child",
                                  order={"meta": "name", "type": "descend"})
    if not res.is_succeeded():
        on_operation_failed("get child nodes", res.error_message())
        assert 0
    children_nodes = res.data.children
    assert len(children_nodes) == 3
    logging.info("[TEST][STORAGE] get child nodes")
