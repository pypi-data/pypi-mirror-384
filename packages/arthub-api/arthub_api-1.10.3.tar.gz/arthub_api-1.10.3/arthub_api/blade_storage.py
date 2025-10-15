# -*- coding:utf-8 -*-
"""internal COS API can be used to upload and download files from COS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import logging
import six
import socket
import os
import time
import threading
import requests
import concurrent
import json
import warnings

# Import third-party modules
import requests

# Import third-party modules
from tenacity import retry as tenacity_retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_fixed
from tenacity import RetryError
from tenacity.before import before_log
from xml.etree import ElementTree

from arthub_api.open_api import APIError
# Import local modules
from arthub_api.utils import logger
import arthub_api.utils as utils
import arthub_api._internal_utils as _internal_utils


allowed_schemes = ["http", "https"]


def normalize_scheme(scheme):
    scheme = scheme.rstrip(":")
    if scheme not in allowed_schemes:
        scheme = "https"
    return scheme


if six.PY2:
    class PermissionError(OSError):
        pass
    class FileNotFoundError(IOError):
        pass

class SignerError(RuntimeError):
    pass

class COSHttpError(RuntimeError):
    pass

# signer for blade api
class RemoteSignerForPackage(object):    
    def __init__(self, blade_backend, force=False):
        self.cli = blade_backend
        self.force = force
        self.scheme = "https"

    def set_scheme(self, scheme):
        self.scheme = normalize_scheme(scheme)

    @classmethod
    def _remove_suffix(cls, s, sf):
        if s.endswith(sf):
            return s[:len(s)-len(sf)]
        return s

    @classmethod
    def _key_to_pkg(cls, key):
        if not key.startswith("pkg_distribution/7z/"):
            return {}
        result = key.split("/")
        if len(result) < 5:
            return {}
        result[4] = cls._remove_suffix(result[4], ".7z")
        if result[2] != result[4]:
            return {}
        return {"name": result[2], "version": result[3]}
    
    def _take_signed_url(self, arthub_response, type_of_sign=""):
        arthub_response.raise_for_err()
        logger.debug('{0} sign-url rsp is {1}'.format(type_of_sign, arthub_response.result))
        if len(arthub_response.result) == 0:
            raise SignerError("arthub api: result is empty")
        return self.scheme + ":" + arthub_response.result[0].get('signed_url')
        
    # we use bucket + key to identify a file. 
    # however bucket might be fixed for ArtHub condition, so bucket input is ignored
    # pkg do not supports for expired argument
    def _get_package_download_sign(self, bucket, key, expired=1200):
        pkg = self._key_to_pkg(key)
        # this will return a url expires in 10 minutes
        signed = self.cli.blade_download_package([pkg])
        signed.raise_for_err()
        if len(signed.result) == 0:
            raise SignerError("arthub api: result is empty")
        logger.debug("download sign-url rsp is {0}".format(signed.result))
        return signed.result
    
    # pkg do not supports for expired argument
    def get_download_url(self, bucket, key, expired=1200):
        signed = self._get_package_download_sign(bucket, key, expired)
        return self.scheme + ":" + signed[0].get('signed_url')
        
    def get_file_size(self, bucket, key):
        signed = self._get_package_download_sign(bucket, key)
        return signed[0].get('size')
    
    def get_upload_url(self, bucket, key, expired=1200):
        pkg = self._key_to_pkg(key)
        signed = self.cli.blade_upload_package([pkg], self.force)
        return self._take_signed_url(signed, "upload")
    
    def get_begin_multipart_upload_url(self, bucket, key, expired=1200):
        pkg = self._key_to_pkg(key)
        signed = self.cli.blade_begin_multipart_package_upload([pkg], self.force)
        return self._take_signed_url(signed, "begin multipart upload")
    
    def get_upload_part_url(self, bucket, key, upload_id, part_number, expired=1200):
        pkg = self._key_to_pkg(key)
        pkg.update({"upload_id": upload_id, "part_number": part_number})
        signed = self.cli.blade_part_package_upload([pkg], self.force)
        return self._take_signed_url(signed, "upload part")
    
    def get_complete_multipart_upload_url(self, bucket, key, upload_id, expired=1200):
        pkg = self._key_to_pkg(key)
        pkg.update({"upload_id": upload_id})
        signed = self.cli.blade_complete_multipart_package_upload([pkg], self.force)
        return self._take_signed_url(signed, "end multipart upload")

class RemoteSigner(object):    
    def __init__(self, blade_backend, force=True):
        self.cli = blade_backend
        self.force = force
        self.scheme = "https"

    def set_scheme(self, scheme):
        self.scheme = normalize_scheme(scheme)

    def _take_signed_url(self, arthub_response, type_of_sign=""):
        arthub_response.raise_for_err()
        logger.debug('{0} sign-url rsp is {1}'.format(type_of_sign, arthub_response.result))
        if len(arthub_response.result) == 0:
            raise SignerError("arthub api: result is empty")
        return self.scheme + ":" + arthub_response.result[0].get('signed_url')
        
    # we use bucket + key to identify a file. 
    # however bucket might be fixed for ArtHub condition, so bucket input is ignored
    def _get_download_sign(self, bucket, key, expired=1200):
        # this will return a url expires in 10 minutes
        signed = self.cli.blade_download_sign([{"cos_key": key, "expired": expired}])
        signed.raise_for_err()
        if len(signed.result) == 0:
            raise SignerError("arthub api: result is empty")
        logger.debug("download sign-url rsp is {0}".format(signed.result))
        return signed.result
    
    def get_download_url(self, bucket, key, expired=1200):
        signed = self._get_download_sign(bucket, key, expired)
        return self.scheme + ":" + signed[0].get('signed_url')
        
    def get_file_size(self, bucket, key):
        signed = self._get_download_sign(bucket, key)
        size = signed[0].get('size')
        if not size:
            return 0
        return size
    
    def get_upload_url(self, bucket, key, expired=1200):
        item = {"cos_key": key, "expired": expired}
        signed = self.cli.blade_upload_sign([item], self.force)
        return self._take_signed_url(signed, "upload")
    
    def get_begin_multipart_upload_url(self, bucket, key, expired=1200):
        item = {"cos_key": key, "expired": expired}
        signed = self.cli.blade_begin_multipart_upload_sign([item], self.force)
        return self._take_signed_url(signed, "begin multipart upload")
    
    def get_upload_part_url(self, bucket, key, upload_id, part_number, expired=1200):
        item = {"cos_key": key, "expired": expired, "upload_id": upload_id, "part_number": part_number}
        signed = self.cli.blade_part_upload_sign([item], self.force)
        return self._take_signed_url(signed, "upload part")
    
    def get_complete_multipart_upload_url(self, bucket, key, upload_id, expired=1200):
        item = {"cos_key": key, "expired": expired, "upload_id": upload_id}
        signed = self.cli.blade_complete_multipart_upload_sign([item], self.force)
        return self._take_signed_url(signed, "end multipart upload")


class ProgressCallback():
    def __init__(self, file_size, progress_callback):
        self.__lock = threading.Lock()
        self.__finished_size = 0
        self.__file_size = file_size
        self.__progress_callback = progress_callback

    def report(self, size):
        with self.__lock:
            self.__finished_size += size
            self.__progress_callback(self.__finished_size, self.__file_size)
            
    def get(self):
        return self.__finished_size, self.__file_size
            
    def get_percent(self):
        return self.__finished_size / self.__file_size


class Client(object):
    def __init__(self, signer=None, timeout=5):
        if signer is None:
            raise ReferenceError("signer is None: must provide signer arg")
        self.remote_signer = signer
        self.timeout = timeout
        
    def download_file(self, Bucket, Key, DestFilePath, PartSize=20, MAXThread=5, EnableCRC=False, progress_callback=None):
        if EnableCRC:
            warnings.warn("EnableCRC is not supported")
        part_size = PartSize * 1024 * 1024
        file_size = self.remote_signer.get_file_size(Bucket, Key)
        if file_size is None:
            raise RetryError('failed to get file_size for {0}, file might not exist'.format(Key))
        callback = None
        if progress_callback:
            callback = ProgressCallback(file_size, progress_callback)
        resumable_downloader = ResumableDownLoader(self.remote_signer, Bucket, Key, DestFilePath, file_size, part_size, MAXThread, callback, self.timeout)
        if file_size < 20 * 1024 * 1024:
            resumable_downloader.simple_download()
            return
            
        resumable_downloader.download()
        
    def upload_file(self, Bucket, Key, LocalFilePath, PartSize=20, MAXThread=5, EnableCRC=False, progress_callback=None):
        if EnableCRC:
            warnings.warn("EnableCRC is not supported")
        if not os.path.isfile(LocalFilePath):
            raise OSError("not found file: {0}".format(LocalFilePath))
        file_size = os.path.getsize(LocalFilePath)
        part_size = PartSize * 1024 * 1024
        callback = None
        if progress_callback:
            callback = ProgressCallback(file_size, progress_callback)
        resumableUploader = ResumableUploader(self.remote_signer, Bucket, Key, LocalFilePath, file_size, part_size, MAXThread, callback, self.timeout)
        if file_size < 20 * 1024 * 1024:
            resumableUploader.simple_upload()
            return
            
        resumableUploader.upload()

    def get_download_url(self, Bucket, Key, Expired=1200):
        return self.remote_signer.get_download_url(Bucket, Key, Expired)

    # check file exists with http-get method
    def check_exists(self, bucket, key):
        headers = {'Range': 'bytes=0-0'}
        self.download_url = self.remote_signer.get_download_url(bucket, key)
        response = requests.get(self.download_url, headers=headers, timeout=self.timeout)
        if response.status_code == 404:
            return False
        if response.status_code == 416:
            return True
        response.raise_for_status()
        return True


class ResumableDownLoader(object):
    def __init__(self, remote_signer, bucket, key, local_path, file_size, part_size=5*1024*1024, thread_num=4, progress_callback=None, timeout=5):
        self.remote_signer = remote_signer
        self.bucket = bucket
        self.key = key
        self.local_path = local_path
        self.part_size = part_size
        self.thread_num = thread_num
        self.progress_callback = progress_callback
        self.file_size = file_size
        self.download_url = None
        self.expired = 600
        self.timeout = timeout
        self.url_expire_time = None
        self.tmp_file = '{0}_ahtmp'.format(local_path)
        self.record_file = '{0}_dl_ahrecord'.format(local_path)
        self.lock = threading.Lock()

    def _refresh_download_url(self):
        current_time = time.time()
        if self.download_url is None or current_time >= self.url_expire_time:
            self.download_url = self.remote_signer.get_download_url(self.bucket, self.key, self.expired)
            self.url_expire_time = current_time + self.expired - 20  # 10 minutes expiry time

    def _load_progress(self):
        res = []
        try:
            if os.path.exists(self.record_file):
                with open(self.record_file, 'r') as f:
                    res = [tuple(map(int, line.strip().split('-'))) for line in f]
        except:
            logger.error("cannot load progress file, treat as new download")
        finally:
            return res

    def _save_progress(self, start, end):
        with self.lock:
            with open(self.record_file, 'a') as f:
                f.write('{start}-{end}-{part_size}\n'.format(start=start, end=end, part_size=self.part_size))  # Save part_size along with the progress, part_size is not current chunk_length

    def _download_part(self, start, end):
        self._refresh_download_url()
        headers = {'Range': 'bytes={start}-{end}'.format(start=start, end=end)}
        try:
            response = requests.get(self.download_url, headers=headers, stream=True, timeout=self.timeout)
        except Exception as e:
            raise COSHttpError("error with requests {0}".format(e))
        response.raise_for_status()
        expected_len = end - start + 1
        real_len = 0
        with open(self.tmp_file, 'rb+') as f:
            f.seek(start)
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                real_len += len(chunk)
                if self.progress_callback:
                    self.progress_callback.report(len(chunk))
        if real_len != expected_len:
            raise IOError("download part length is not expected")
        self._save_progress(start, end)  # Save progress after part is downloaded

    def simple_download(self):
        self._refresh_download_url()
        try:
            response = requests.get(self.download_url, stream=True, timeout=self.timeout)
        except Exception as e:
            raise COSHttpError("error with requests {0}".format(e))
        response.raise_for_status()
        real_len = 0
        with open(self.tmp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                real_len += len(chunk)
                if self.progress_callback:
                    self.progress_callback.report(len(chunk))
        if real_len != self.file_size:
            raise IOError("download length is not expected")
        try:
            os.remove(self.local_path)
        except:
            pass
        os.rename(self.tmp_file, self.local_path)
        if os.path.exists(self.record_file):  # Remove existing progress record file
            os.remove(self.record_file)
                    
    def download(self):
        self._refresh_download_url()
        part_ranges = self._calculate_part_ranges()
        progress_record = self._load_progress()
        
        # create if not exists
        with open(self.tmp_file,"a+"):
            pass
            
        # Call progress_callback with the existing progress if there is a progress record
        if progress_record and self.progress_callback:
            total_downloaded = sum(end - start + 1 for start, end, _ in progress_record)
            self.progress_callback.report(total_downloaded)

        # Use a ThreadPoolExecutor to limit the number of threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_num) as executor:
            # Submit download tasks to the thread pool
            futures = [executor.submit(self._download_part, start, end) for start, end in part_ranges if (start, end, self.part_size) not in progress_record]

            # Wait for all download tasks to complete, allowing KeyboardInterrupt (Ctrl-C) to stop the process
            try:
                for future in concurrent.futures.as_completed(futures):
                    future.result()
            except KeyboardInterrupt as e:
                print("Download interrupted by user. Stopping...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise e
        try:
            os.remove(self.local_path)
        except:
            pass
        os.rename(self.tmp_file, self.local_path)
        if os.path.exists(self.record_file):  # Remove existing progress record file
            os.remove(self.record_file)

    def _calculate_part_ranges(self):
        part_ranges = []
        num_parts = self.file_size // self.part_size
        if self.file_size % self.part_size != 0:
            num_parts += 1

        for i in range(num_parts):
            start = i * self.part_size
            end = min((i + 1) * self.part_size - 1, self.file_size - 1)
            part_ranges.append((start, end))

        return part_ranges
    

class ResumableUploader(object):
    def __init__(self, remote_signer, bucket, key, local_path, file_size, part_size=5*1024*1024, thread_num=4, progress_callback=None, timeout=5):
        self.remote_signer = remote_signer
        self.bucket = bucket
        self.key = key
        self.local_path = local_path
        self.part_size = part_size
        self.thread_num = thread_num
        self.progress_callback = progress_callback
        self.file_size = file_size
        self.upload_url = None
        self.url_expire_time = None
        self.timeout = timeout
        self.record_file = '{0}_ul_ahrecord'.format(local_path)
        self.lock = threading.Lock()
        
    def _begin_multipart_upload(self, bucket, key, file_name):
        begin_url = self.remote_signer.get_begin_multipart_upload_url(bucket, key)
        # req
        try:
            res = requests.post(begin_url,
                                headers={"content-type": _internal_utils.get_content_type_from_file_name(file_name)}, timeout=self.timeout)
        except Exception as e:
            error_message = "request S3 multipart by url %s upload id exception: %s" % (begin_url, e)
            logger.error("[API] %s" % error_message)
            raise COSHttpError(error_message)
        if not res or not res.ok:
            error_message = "request S3 multipart upload id failed, url: %s, code: %d" % (begin_url, res.status_code)
            logger.error("[API] %s" % error_message)
            raise COSHttpError(error_message)
        # parse
        try:
            xml_tree = ElementTree.fromstring(res.content)
            upload_id = xml_tree.find("UploadId").text
            logger.debug("[API] get multipart upload id: %s" % upload_id)
            return upload_id
        except Exception as e:
            error_message = "parsing S3 multipart upload id from \"%s\" exception, %s" % (res.text, e)
            logger.error("[API] %s" % error_message)
            raise COSHttpError(error_message)
        
    def _upload_part(self, bucket, key, start, end, upload_id, part_number, disable_record=False):
        upload_url = self.remote_signer.get_upload_part_url(bucket, key, upload_id, part_number)
        res = utils.upload_part_of_file(upload_url, self.local_path, start, end-start+1, self._report, self.timeout)
        if not res.is_succeeded():
            err = "upload \"{0}\"th part failed, {1}".format(part_number, res.error_message())
            logger.error("[API] %s" % err)
            raise COSHttpError(err)
        etag = res.data.headers.get("etag").strip('"')
        if not disable_record:
            self._save_progress(start, end, upload_id, part_number, etag)  # Save progress after part is uploaded
        return (part_number, etag)
    
    def _complete_multipart_upload(self, bucket, key, upload_id, etags):
        complete_url = self.remote_signer.get_complete_multipart_upload_url(bucket, key, upload_id)
        etag_data = self._generate_etags_xml(etags)
        # req
        try:
            res = requests.post(complete_url,
                                headers={"content-type": "application/xml"}, data=etag_data, timeout=self.timeout)
        except Exception as e:
            error_message = "request complete S3 multipart by url %s upload id exception: %s" % (complete_url, e)
            logger.error("[API] %s" % error_message)
            raise
        if not res or not res.ok:
            error_message = "request complete S3 multipart upload id failed, url: %s, code: %d" % (complete_url, res.status_code)
            logger.error("[API] %s" % error_message)
            raise COSHttpError(error_message)
        return
        
    def _upload(self, bucket, key):
        upload_url = self.remote_signer.get_upload_url(bucket, key)
        res = utils.upload_file(upload_url, self.local_path, self._report, self.timeout)
        if not res.is_succeeded():
            err = "upload failed, {0}".format(res.error_message())
            logger.error("[API] %s" % err)
            raise COSHttpError(err)
        return 
        
    def _report(self, new_read_size):
        if self.progress_callback:
            self.progress_callback.report(new_read_size)

    def _load_progress(self):
        parts = []
        etags = []
        final_upload_id = ""
        if os.path.exists(self.record_file):
            with open(self.record_file, 'r') as f:
                for line in f:
                    obj = json.loads(line)
                    parts.append((obj.get("start"), obj.get("end"), obj.get("part_size"), obj.get("upload_id"), obj.get("part_number")))
                    etags.append((obj.get("part_number"), obj.get("etag")))
            # check
            for start, end, part_size, upload_id, part_number in parts:
                if final_upload_id == "":
                    final_upload_id = upload_id
                if final_upload_id != upload_id or part_size != self.part_size:
                    os.remove(self.record_file)
                    parts = []
                    etags = []
                    break
        return parts, etags, final_upload_id

    def _save_progress(self, start, end, upload_id, part_number, etag):
        with self.lock:
            with open(self.record_file, 'a') as f:
                line = json.dumps({"start":start, "end":end, "part_size":self.part_size, "upload_id":upload_id, "part_number":part_number, "etag":etag })
                f.write("{0}\n".format(line))

    def simple_upload(self):
        if os.path.exists(self.record_file):  # Remove existing progress record file
            os.remove(self.record_file)
        self._upload(self.bucket, self.key)
                    
    def upload(self, disable_record=False):
        part_ranges = self._calculate_part_ranges()
        
        progress_record = []
        progress_etags = []
        upload_id = ""
        if not disable_record:
            progress_record, progress_etags, upload_id = self._load_progress()
            # Call progress_callback with the existing progress if there is a progress record
            if progress_record and self.progress_callback:
                total_uploaded = sum(end - start + 1 for start, end, _, _, _ in progress_record)
                self.progress_callback.report(total_uploaded)
        
        # begin multipart upload
        if not upload_id:
            upload_id = self._begin_multipart_upload(self.bucket, self.key, self.local_path)

        # Use a ThreadPoolExecutor to limit the number of threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_num) as executor:
            # Submit upload tasks to the thread pool
            futures = []
            for start, end, part_number in part_ranges:
                if (start, end, self.part_size, upload_id, part_number) not in progress_record:
                    futures.append(executor.submit(self._upload_part, self.bucket, self.key, start, end, upload_id, part_number, disable_record))

            # Wait for all upload part tasks to complete, allowing KeyboardInterrupt (Ctrl-C) to stop the process
            try:
                for future in concurrent.futures.as_completed(futures):
                    progress_etags.append(future.result())
            except KeyboardInterrupt as e:
                print("Upload interrupted by user. Stopping...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise e
            
        # end multipart upload
        self._complete_multipart_upload(self.bucket, self.key, upload_id, progress_etags)
        
        if os.path.exists(self.record_file):  # Remove existing progress record file
            os.remove(self.record_file)

    def _calculate_part_ranges(self):
        part_ranges = []
        num_parts = self.file_size // self.part_size
        if self.file_size % self.part_size != 0:
            num_parts += 1

        for i in range(num_parts):
            start = i * self.part_size
            end = min((i + 1) * self.part_size - 1, self.file_size - 1)
            part_ranges.append((start, end, i+1))

        return part_ranges

    def _generate_etags_xml(self, etags):
        root = ElementTree.Element('CompleteMultipartUpload')
        etags = sorted(etags, key=lambda x: x[0])
        for item in etags:
            part = ElementTree.SubElement(root, 'Part')
            etag = ElementTree.SubElement(part, 'ETag')
            etag.text = item[1]
            part_number = ElementTree.SubElement(part, 'PartNumber')
            part_number.text = str(item[0])
        return ElementTree.tostring(root)

class BladeCOSApi(object):
    """API to access THM pipeline installers on Blade storage."""
    # user input:
    def __init__(self, api, force=False, retry=3, cli=None, signer=None, scheme=None, timeout=None):
        self.force = force
        self.retry = retry
        self.signer = signer
        self.cli = cli
        if scheme is None:
            scheme = api.http_scheme
        if timeout is None:
            timeout = api.timeout
        self.timeout = timeout
        # signer
        if signer is None:
            signer = RemoteSignerForPackage(api, force)
        signer.set_scheme(scheme)
        self.signer = signer
        # cli
        if cli is None:
            cli = Client(signer, timeout=timeout)
        self.cli = cli

    def check_file_exist(self, server_path):
        try:
            return self.cli.check_exists("", server_path)
        except ValueError:
            return False

    def get_file_object(self, server_path):
        url = self.get_download_url(server_path)
        try:
            r = requests.get(url, stream=True, timeout=self.timeout)
        except Exception as e:
            raise COSHttpError("error requests {0}".format(e))
        if r.status_code >= 400:
            msg = r.text
            if msg == u'':
                msg = r.headers
            raise COSHttpError("message: {0}, status code: {1}".format(msg, r.status_code))
        obj = dict(r.headers)
        obj.update({"Response": r})
        return obj

    def get_download_url(self, server_path, expired_time=1200):
        return self.cli.get_download_url(
            Bucket="",
            Key=server_path,
            Expired=expired_time,
        )

    @tenacity_retry(
        before=before_log(logger, logging.WARN),
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.5),
        retry=retry_if_exception_type(OSError)
        | retry_if_exception_type(PermissionError)
        | retry_if_exception_type(FileNotFoundError)
        | retry_if_exception_type(APIError)
        | retry_if_exception_type(SignerError)
        | retry_if_exception_type(COSHttpError)
    )
    def download_file(self, server_path, local_path, progress_callback=None):
        """Download file by given server path."""
        return self.cli.download_file(
            Bucket="",
            Key=server_path,
            DestFilePath=local_path,
            MAXThread=10,
            progress_callback=progress_callback,
        )

    @tenacity_retry(
        before=before_log(logger, logging.WARN),
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.5),
        retry=retry_if_exception_type(OSError)
        | retry_if_exception_type(PermissionError)
        | retry_if_exception_type(FileNotFoundError)
        | retry_if_exception_type(APIError)
        | retry_if_exception_type(SignerError)
        | retry_if_exception_type(COSHttpError)
    )
    def upload_file(self, server_path, local_path, progress_callback=None):
        """Upload file by given server path."""
        return self.cli.upload_file(
            Bucket="",
            Key=server_path,
            LocalFilePath=local_path,
            MAXThread=10,
            progress_callback=progress_callback,
        )
        
