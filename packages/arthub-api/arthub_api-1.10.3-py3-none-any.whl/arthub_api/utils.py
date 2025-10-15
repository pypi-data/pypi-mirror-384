# -*- coding: utf-8 -*-
"""
arthub_api.utils
~~~~~~~~~~~~~~

This module provides utilities that are used within API
"""
import logging
import os
import shutil
import time
import random
import string
import requests
import threading
from . import models
from platformdirs import user_cache_dir
from .config import (
    api_config_oa,
    api_config_qq,
    api_config_public,
    api_config_oa_test,
    api_config_qq_test
)
from base64 import b64encode, b64decode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

from .__version__ import __title__

logger = logging.getLogger(__title__)


def _path_preprocess(path):
    path = path.strip()
    path = path.rstrip("\\/")
    return path


def create_empty_file(path):
    try:
        open(path, "w").close()
        return True
    except Exception:
        return False


def mkdir(path):
    path = _path_preprocess(path)
    if os.path.isdir(path):
        return True
    if os.path.isfile(path):
        return False
    try:
        os.makedirs(path)
    except Exception as e:
        return False
    return True


def remove(path):
    path = _path_preprocess(path)
    if not os.path.exists(path):
        return True
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except Exception as e:
        return False
    return True


def current_milli_time():
    return (lambda: int(round(time.time() * 1000)))()


def get_random_string(length):
    return ''.join(random.sample(string.ascii_letters + string.digits, length))


class UploadFilePartReader(object):
    def __init__(self, file_, offset, length, callback=None):
        self._file = file_
        self._file.seek(offset)
        self._total_size = length
        self._completed_size = 0
        self._finished = False
        self._callback = callback

    def read(self, size=-1):
        if size == -1:
            self._finished = True
            return ""
        uncompleted_size = self._total_size - self._completed_size
        size_to_read = min(uncompleted_size, size)
        if size_to_read == 0:
            self._finished = True
            return ""
        content = self._file.read(size_to_read)
        self._completed_size += len(content)
        if self._callback:
            self._callback(len(content))
        return content


def upload_part_of_file(url, file_path, offset, length, callback=None, timeout=30):
    try:
        if not os.path.isfile(file_path):
            return models.Result(False, error_message="file \"%s\" not exist" % file_path)
        with open(file_path, 'rb') as file_:
            res = requests.put(url, data=UploadFilePartReader(file_, offset, length, callback), headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/octet-stream",
                "Content-Length": str(length)
            }, timeout=timeout)
            if not res.ok:
                return models.Result(False, error_message="status code: %d, response: %s" % (res.status_code, res.text))
            return models.Result(True, data=res)
    except requests.exceptions.Timeout as e:
        error_message = "upload request timeout after %d seconds: %s" % (timeout, str(e))
        logger.error("[UploadFilePart] %s" % error_message)
        return models.Result(False, error_message=error_message, can_retry=True)
    except requests.exceptions.RequestException as e:
        error_message = "upload request failed: %s" % str(e)
        logger.error("[UploadFilePart] %s" % error_message)
        return models.Result(False, error_message=error_message, can_retry=True)
    except Exception as e:
        error_message = "unexpected error during upload: %s" % str(e)
        logger.error("[UploadFilePart] %s" % error_message)
        return models.Result(False, error_message=error_message)


class UploadFileReader(object):
    def __init__(self, file_, callback):
        self._file = file_
        self._file.seek(0)
        self._total_size = os.path.getsize(file_.name)
        self._completed_size = 0
        self._finished = False
        self._callback = callback

    def read(self, size=-1):
        if size == -1:
            self._finished = True
            return ""
        content = self._file.read(size)
        self._completed_size += len(content)
        if self._callback:
            self._callback(len(content))
        return content


def upload_file(url, file_path, callback=None, timeout=5):
    try:
        if not os.path.isfile(file_path):
            return models.Result(False, error_message="file \"%s\" not exist" % file_path)
        with open(file_path, 'rb') as file_:
            res = requests.put(url, data=UploadFileReader(file_, callback), headers={
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/octet-stream",
                "Content-Length": str(os.path.getsize(file_path))
            }, timeout=timeout)
            if not res.ok:
                return models.Result(False, error_message="status code: %d" % res.status_code)
            return models.Result(True, data=res)
    except Exception as e:
        error_message = "send request \"%s\" exception \"%s\"" % (url, str(e))
        logger.error("[UploadFile] %s" % error_message)
        return models.Result(False, error_message=error_message)


def download_file(url, file_path, progress_cb=None, total_size=None, timeout=5,
                  progress_min_bytes=256 * 1024, progress_min_interval_ms=250, chunk_size=256 * 1024,
                  progress_percent_step=0.01):
    try:
        if os.path.exists(file_path):
            remove(file_path)

        if not create_empty_file(file_path):
            return models.Result(False, error_message="create \"%s\" failed" % file_path)

        # download file
        download_dir_path = os.path.dirname(file_path)
        if not mkdir(download_dir_path):
            return models.Result(False, error_message="create directory \"%s\" failed" % download_dir_path)

        res_download = requests.get(url, stream=True, timeout=timeout)

        if not res_download:
            return models.Result(False, error_message="request \"%s\" failed" % url)
        bytes_completed = 0
        stop_event = threading.Event()

        def _reporter():
            try:
                # fixed-interval reporting regardless of delta
                while not stop_event.wait(progress_min_interval_ms / 1000.0):
                    if progress_cb:
                        try:
                            progress_cb(bytes_completed, total_size if total_size is not None else 0)
                        except Exception:
                            pass
            except Exception:
                pass

        reporter_thread = None
        try:
            if progress_cb:
                reporter_thread = threading.Thread(target=_reporter, daemon=True)
                reporter_thread.start()

            with open(file_path, "ab") as f:
                for chunk in res_download.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    f.flush()
                    bytes_completed += len(chunk)

            # ensure a final progress callback at completion
            if progress_cb:
                try:
                    progress_cb(bytes_completed, total_size if total_size is not None else 0)
                except Exception:
                    pass
        finally:
            try:
                stop_event.set()
                if reporter_thread is not None:
                    reporter_thread.join(timeout=1.0)
            except Exception:
                pass

        return models.Result(True)

    except Exception as e:
        return models.Result(False, error_message=e)


def get_download_file_size(url):
    try:
        # Send a GET request with Range header to get the file size
        headers = {'Range': 'bytes=0-0'}
        response = requests.get(url, headers=headers, allow_redirects=True)

        # Check the response status code
        if response.status_code == 416:
            return models.Result(True, data=0)  # Requested range not satisfiable
        elif response.status_code == 403:
            return models.Result(False, error_message="URL expired or access forbidden")

        # Try to get the file size from the response
        file_size = get_capacity_from_response(response)
        if file_size is None:
            return models.Result(False, error_message="Can't parse content-range from response")

        return models.Result(True, data=file_size)

    except Exception as e:
        return models.Result(False, error_message=str(e))

def get_capacity_from_response(response):
    # Check the Content-Range header
    content_range = response.headers.get('Content-Range')
    if content_range is None:
        return None

    # Parse the Content-Range header
    try:
        range_str = content_range
        pos = range_str.find("/")
        if pos == -1:
            return None
        size_str = range_str[pos + 1:]
        return int(size_str)  # Convert file size to integer
    except ValueError:
        return None


def splite_path(path_):
    path_list = []
    while path_:
        l = os.path.split(path_)
        path_ = l[0]
        if l[1]:
            path_list.insert(0, l[1])
    return path_list


def rename_path_text(path_):
    path_ = _path_preprocess(path_)
    path_without_ext, ext = os.path.splitext(path_)
    suffix_number = 1
    while os.path.exists(path_):
        path_ = "%s (%d)%s" % (path_without_ext, suffix_number, ext)
        suffix_number += 1
    return path_


def parse_cookies(cookie_str):
    cookies = {}
    cookie_strs = cookie_str.split(';')
    for _item in cookie_strs:
        _item = _item.strip()
        _pair = _item.split('=')
        if len(_pair) == 2:
            cookies[_pair[0]] = _pair[1]
    return cookies


def rename_path(src, dest):
    if not mkdir(os.path.dirname(dest)):
        return False
    try:
        shutil.move(src, dest)
    except Exception:
        return False
    return True


def count_files(root_path):
    total_files = 0
    if not os.path.exists(root_path):
        return total_files
    item_list = os.listdir(root_path)
    if len(item_list) == 0:
        return total_files
    for item in item_list:
        next_path = os.path.join(root_path, item)
        if os.path.isfile(next_path):
            total_files += 1
        else:
            total_files += count_files(next_path)
    return total_files


def read_file(file_path):
    with open(file_path, "r") as file_obj:
        return file_obj.read()


def write_file(file_path, data):
    with open(file_path, "w") as file_obj:
        file_obj.write(data)


def get_cache_dir(api_host):
    root = user_cache_dir(appname="arthub", opinion=False)
    d = os.path.join(root, api_host)
    try:
        os.makedirs(d)
    except Exception as e:
        pass
    return d


def get_token_cache_file(api_host):
    root = get_cache_dir(api_host)
    return os.path.join(root, "arthub_token")


def get_token_from_cache(api_host):
    token_file = get_token_cache_file(api_host)
    try:
        if os.path.exists(token_file):
            return read_file(token_file)
    except Exception as e:
        logger.warning("[TokenCache] get token from file \"%s\" error: %s",
                       token_file, str(e))
    return ""


def save_token_to_cache(token, api_host):
    token_file = get_token_cache_file(api_host)
    try:
        write_file(token_file, token)
    except Exception as e:
        logger.warning("[TokenCache] save token to file \"%s\" error: %s",
                       token_file, str(e))


def remove_token_cache_file(api_host):
    remove(get_token_cache_file(api_host))


def get_config_by_name(env, default_config=None):
    _env_map = {
        "oa": api_config_oa,
        "qq": api_config_qq,
        "oa_test": api_config_oa_test,
        "qq_test": api_config_qq_test,
        "public": api_config_public
    }
    c = _env_map.get(env)
    if not c:
        if default_config:
            return default_config
        return api_config_oa
    return c


def encrypt(public_key_str, plain_text):
    try:
        public_key_bytes = b64decode(public_key_str)
        public_key = RSA.import_key(public_key_bytes)

        block_size = 256 - 2 * 32 - 2
        plain_text_blocks = [plain_text[i:i + block_size] for i in range(0, len(plain_text), block_size)]

        encrypted_blocks = []
        for block in plain_text_blocks:
            cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
            encrypted_block = cipher.encrypt(block.encode())
            encrypted_blocks.append(b64encode(encrypted_block).decode())

        encrypted_text = ".".join(encrypted_blocks)
        return encrypted_text
    except Exception as e:
        print("Error during encryption:", str(e))
        return ""
