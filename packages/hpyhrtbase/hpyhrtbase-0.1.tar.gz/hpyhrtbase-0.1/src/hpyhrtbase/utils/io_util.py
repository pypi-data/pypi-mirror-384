import json
import logging
import os
import shutil
import time
import zipfile
from datetime import datetime, timedelta
from typing import Any

import requests

from hpyhrtbase import hpyhrt_context

mod_logger = logging.getLogger(__name__)


class IOUtil:
    @staticmethod
    def download_file(url: str, local_filepath: str, *, max_retry: int = 2) -> None:
        for i in range(max_retry):
            try:
                with requests.get(url, stream=True, verify=False) as r:
                    r.raise_for_status()
                    total_size_in_bytes = int(r.headers.get("content-length", 0))
                    total_written = 0
                    with open(local_filepath, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                                total_written += len(chunk)
                                mod_logger.debug(
                                    f"downloading {url}: written {total_written} / {total_size_in_bytes}"
                                )
                    mod_logger.debug(f"download_file {url} to {local_filepath} succeed")
                return
            except Exception as e:
                if i == (max_retry - 1):
                    mod_logger.warning(
                        f"download_file {url} to {local_filepath} failed: {e}"
                    )
                    raise e

    @staticmethod
    def download_if_needed(src_url: str, target_dir: str, *, max_retry: int = 2) -> str:
        base_name = src_url.rsplit("/", 1)[1]
        target_path = os.path.join(target_dir, base_name)

        if os.path.exists(target_path):
            return target_path

        target_path_temp = target_path + ".temp"

        IOUtil.download_file(src_url, target_path_temp, max_retry=max_retry)
        os.rename(target_path_temp, target_path)

        return target_path

    @staticmethod
    def download_url(
        url: str,
        retry_count: int = 3,
        timeout: float = 10,
        need_throttle: bool = False,
        rethrow: bool = True,
    ) -> requests.Response:
        for idx in range(retry_count):
            if need_throttle:
                hpyhrt_context.get_global_context().throttle.wait(url)
            try:
                mod_logger.debug(f"Try {idx} Begin: to download from: {url}")
                rsp = requests.get(url, timeout=timeout)
                mod_logger.debug(
                    f"Try {idx} End: finish download from: {url}, "
                    f"rsp.status_code {rsp.status_code}"
                )

                if not 200 <= rsp.status_code < 300:
                    mod_logger.warning(
                        f"Try {idx} failed: url {url}, rsp code {rsp.status_code}, text {rsp.text}"
                    )
                    continue

                return rsp
            except Exception as e:
                mod_logger.info(f"warn: download {url} failed: {e}")
                time.sleep(10)

                if idx == (retry_count - 1):
                    mod_logger.warning(f"error: download {url} failed")

                    if rethrow:
                        raise e

        raise Exception(f"Failed to download {url}")

    @staticmethod
    def find_abs_path(in_path: str, iter_lvl: int = 5) -> str | None:
        log_prefix = "find_abs_path:"

        mod_logger.info(f"{log_prefix} Enter to find {in_path}")

        abs_path: str | None = None

        if os.path.isabs(in_path):
            if os.path.exists(in_path):
                abs_path = in_path
        else:
            rel_path = in_path
            for _ in range(iter_lvl):
                if os.path.exists(rel_path):
                    abs_path = os.path.abspath(rel_path)
                    break
                rel_path = os.path.join("..", rel_path)

        if not abs_path:
            mod_logger.debug(f"{log_prefix} Leave without found")
            return None

        mod_logger.debug(f"{log_prefix} Leave with found {abs_path}")

        return abs_path

    @staticmethod
    def find_root_dir(
        config_file: str, check_dir_names: list[str] | None = None
    ) -> str:
        prev_dir = None
        cur_dir = os.path.dirname(config_file)

        if not check_dir_names:
            check_dir_names = ["data", "config"]

        while True:
            if cur_dir == prev_dir:
                raise Exception(f"Can't find root dir for {config_file}")

            all_check_pass = True

            for check_dir_name in check_dir_names:
                check_dir = os.path.join(cur_dir, check_dir_name)

                if not os.path.isdir(check_dir):
                    all_check_pass = False
                    break

            if all_check_pass:
                return cur_dir

            prev_dir = cur_dir
            cur_dir = os.path.abspath(os.path.join(cur_dir, ".."))

    @staticmethod
    def get_local_abs_file_path(file_path: str) -> str:
        # download from remote if not exist in local and cache in local
        if file_path.startswith("http"):
            local_abs_file_path = IOUtil.download_if_needed(
                file_path, hpyhrt_context.get_config_inst().data_cache_dir
            )
        else:
            local_abs_file_path = os.path.join(
                hpyhrt_context.get_config_inst().data_dir, file_path
            )
            if not os.path.exists(local_abs_file_path):
                raise Exception(
                    f"get_local_abs_file_path failed, file_path {local_abs_file_path} doesn't exist"
                )

        return local_abs_file_path

    @staticmethod
    def load_json_from_url(json_url: str, timeout: float = 10) -> Any:
        text = IOUtil.load_text_from_url(json_url, timeout=timeout)
        json_data = json.loads(text)
        return json_data

    @staticmethod
    def load_text_from_url(text_url: str, timeout: float = 10) -> str:
        if text_url.startswith("http"):
            return IOUtil.load_text_from_http_url(text_url, timeout)
        else:
            return IOUtil.load_text_from_file_url(text_url)

    @staticmethod
    def load_text_from_http_url(text_url: str, timeout: float = 10) -> str:
        headers: dict[str, str] = {}

        r = requests.get(text_url, headers=headers, timeout=timeout, verify=False)

        if 200 <= r.status_code < 300:
            text_content = r.text
            return text_content
        else:
            raise Exception(f"bad status code {r.status_code}")

    @staticmethod
    def load_text_from_file_url(text_url: str) -> str:
        with open(text_url, encoding="utf-8") as text_file:
            text_content = text_file.read()
            return text_content

    @staticmethod
    def maybe_make_dir(dirname: str) -> None:
        """Make a directory if it doesn't exist."""
        os.makedirs(dirname, exist_ok=True)

    @staticmethod
    def rm_file(file_path: str) -> None:
        log_prefix = "rm_file:"

        try:
            os.remove(file_path)
            mod_logger.debug(f"{log_prefix} file_path: {file_path}")
        except Exception as err:
            mod_logger.debug(f"{log_prefix} exception {err}")

    @staticmethod
    def rm_old(
        dir_path: str,
        days: float = 7,
        force: bool = False,
        filter_list: list[str] | None = None,
        remove_indeed: bool = True,
    ) -> None:
        log_prefix = "rm_old:"

        if not os.path.isdir(dir_path):
            return

        datetime_thres_obj = datetime.now() - timedelta(days=days)
        datetime_thres = datetime_thres_obj.timestamp()
        mod_logger.debug(
            f"{log_prefix} dir_path: {dir_path}, force_delete: {force}, "
            f"remove_indeed {remove_indeed}, datetime_thres {datetime_thres_obj}"
        )

        with os.scandir(dir_path) as it:
            for entry in it:
                stat_result = entry.stat()
                if False:
                    mod_logger.debug(
                        f"{log_prefix}, path: {entry.path}, st_mtime: {stat_result.st_mtime}, date_time_thres: {datetime_thres}, cur_time: {datetime.now()}"
                    )
                # 1604799194 is 2020-11-08 09:33:14
                if force or datetime_thres > stat_result.st_mtime > 1604799194:
                    if entry.is_dir():
                        mod_logger.debug(f"{log_prefix}, rm dir {entry.path}")
                        if remove_indeed:
                            if not filter_list or (
                                filter_list and entry.path not in filter_list
                            ):
                                shutil.rmtree(entry.path)
                                mod_logger.debug(
                                    f"{log_prefix}, rm dir {entry.path} done"
                                )
                    else:
                        mod_logger.debug(f"{log_prefix}, rm file {entry.path}")
                        if remove_indeed:
                            if not filter_list or (
                                filter_list and entry.path not in filter_list
                            ):
                                os.remove(entry.path)
                                mod_logger.debug(
                                    f"{log_prefix}, rm file {entry.path} done"
                                )

    @staticmethod
    def save_text_to_path(in_text: str, out_path: str) -> None:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(in_text)

    @staticmethod
    def unzip_to_dir(zip_path: str, dir_path: str | None = None) -> None:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dir_path)

    @staticmethod
    def zip_path(in_path: str, zip_file_path: str | None = None) -> None:
        def addToZip(zf: zipfile.ZipFile, path: str, zippath: str) -> None:
            if os.path.isfile(path):
                zf.write(path, zippath, zipfile.ZIP_DEFLATED)
            elif os.path.isdir(path):
                if zippath:
                    zf.write(path, zippath)
                for nm in sorted(os.listdir(path)):
                    addToZip(zf, os.path.join(path, nm), os.path.join(zippath, nm))

        if zip_file_path is None:
            zip_file_path = os.path.basename(in_path) + ".zip"
        with zipfile.ZipFile(zip_file_path, "w") as zf:
            zippath = os.path.basename(in_path)
            if not zippath:
                zippath = os.path.basename(os.path.dirname(in_path))
            if zippath in ("", os.curdir, os.pardir):
                zippath = ""
            addToZip(zf, in_path, zippath)
