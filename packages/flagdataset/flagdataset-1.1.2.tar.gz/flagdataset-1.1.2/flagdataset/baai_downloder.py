import sys
import logging
import time
import pathlib
import hashlib
import queue
import csv
import mmap
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from .baai_config import Application, Progress
from .helper.baai_jwtsign import jwtsign_parse
from .helper.baai_read import read_base_meta
from .helper import baai_requests as requests


logger = logging.getLogger(__name__)

application = Application()
progress = Progress()

executor_pipe = ThreadPoolExecutor(max_workers=application.executor_worker_size)
executor_pipe_queue = queue.Queue(maxsize=application.executor_worker_size)
executor_down = ThreadPoolExecutor(max_workers=application.executor_down_size)
executor_merge = ThreadPoolExecutor(max_workers=application.executor_merge_size)

def download_readrows(meta_path):
    # 单线程
    list_bin = meta_path.glob("*.bin")
    for row_bin in list_bin:
        rows = read_base_meta(row_bin)
        for row_base in rows:
            download_path, download_size, _ = row_base
            download_size = int(download_size)
            progress.add_require_count(1)
            progress.add_require_size(download_size)

def download_progress(meta_path, data_path, temp_path):
    # 单线程
    for _ in range(100):
        if progress.require_count > 0 and progress.require_size > 0:
            time.sleep(0.01)
            break

    list_bin = meta_path.glob("*.bin")
    for row_bin in list_bin:
        rows = read_base_meta(row_bin)
        for row_base in rows:
            download_path, download_size, _ = row_base
            download_size = int(download_size)

            executor_pipe_queue.put(1)
            executor_pipe.submit(download_file, download_path, download_size, data_path, temp_path)
            progress.add_download_submit_count(1)


def download_file(download_path: str, download_size: int, data_path: pathlib.Path, temp_path: pathlib.Path):
    config = Application()

    storage_proto = jwtsign_parse(download_path).get("proto")
    storage_prefix = jwtsign_parse(download_path).get("prefix")
    storage_path = jwtsign_parse(download_path).get("path")

    _, storage_pos = storage_proto.split("://", maxsplit=1)
    storage_path = f"{storage_pos}/{storage_prefix}/{storage_path}"
    _, storage_name = storage_path.split("/", maxsplit=1)

    file_path = data_path / storage_name
    # 文件存在不进行下载
    if check_file(file_path.absolute().__str__(), download_size):
        time.sleep(0.01)
        progress.add_download_size(download_size)
        progress.add_download_count(1)
        executor_pipe_queue.get()
        return

    chunk_size = config.chunk_size
    total_parts = int((download_size + chunk_size - 1) / chunk_size)

    file_hash = hashlib.md5(file_path.absolute().__str__().encode()).hexdigest()
    file_name = file_path.name

    # 分块任务
    download_futures = []
    progress.add_required_part_count(total_parts)
    for part_index in range(total_parts):
        start = part_index * chunk_size
        end = min(start + chunk_size, download_size)
        part_path = temp_path / f"{part_index}__{file_hash}__{file_name}.bin"
        task_down = executor_down.submit(download_part_write, download_path, start, end, part_path)

        download_futures.append(task_down)

    # 等待完成
    for future in as_completed(download_futures):
        future.result()

    # 合并下载
    progress.add_required_merged_count(1)
    executor_merge.submit(download_part_merge,  file_path, temp_path, file_hash, file_name, total_parts)
    executor_pipe_queue.get()

def download_part_write(download_path: str, start: int, end: int, part_path: pathlib.Path):
    if check_file(part_path.__str__(),  end-start):
        progress.add_download_part_count(1)
        progress.add_download_size(end - start)
    else:
        range_header = f"bytes={start}-{end - 1}"
        try:
            sign_addr = sign_download(download_path)
        except Exception as e:
            logger.info(f"download_part_write, sign err {e}")
            sign_addr = ""

        # TODO: 签名失败

        resp_file = None
        for retry in range(1, 4):
            try:
                resp_file = requests.get(sign_addr, headers={"Range": range_header})
                break
            except Exception as e:
                logger.info(f"download_part_write, {sign_addr}, {e}")
                time.sleep(2 * retry)
                continue

        if resp_file and resp_file.status_code in [200, 206]:
            with part_path.open("wb") as fwriter:
                fwriter.write(resp_file.content)
                # 下载的大小
                progress.add_download_part_count(1)
                progress.add_download_size(end - start)
        else:
            # TODO: 下载失败
            pass

def download_part_merge(file_path: pathlib.Path, temp_path: pathlib.Path, file_hash, file_name, total_parts):


    target_path = file_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("ab") as fwriter:
        for part_idx in range(total_parts):
            part_name = temp_path / f"{part_idx}__{file_hash}__{file_name}.bin"
            with part_name.open("rb") as f:
                with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                    fwriter.write(mm)

                # TODO: 删除分片文件
                # part_name.unlink()

    # 合并完成才算下载完成
    progress.add_download_merged_count(1)
    progress.add_download_count(1)


# --------- executor_download ------------
def executor_download(dataset_id: str, save_path: str, **extra_kwargs):

    print("-----------executor----------------")
    print("executor_worker_size: ", application.executor_worker_size)
    print("executor_down_size: ", application.executor_down_size)


    # 登录测试
    try:
        executor_user_signin()
    except AssertionError as e:
        print("登录信息获取失败，请重新登录")
        return
    except Exception as e:
        logger.error(e)
        return


    logger_download(dataset_id, 0, extra_kwargs.pop("dir_path", ""))

    # 下载 meta 信息
    try:
        executor_meta_download(dataset_id, save_path, dir_path=extra_kwargs.get("dir_path"))
    except AssertionError as e:
        print(e)
        return
    except Exception as e:
        logger.error(e)
        return

    # 下载数据
    try:
        executor_data_download_with_pbar(dataset_id, save_path)
    except AssertionError as e:
        print(e)
    except Exception as e:
        logger.error(e)
        return

    logger_download(dataset_id, 1, extra_kwargs.pop("dir_path", ""))



def executor_data_download_with_pbar(dataset_id: str, save_path: str):
    import threading
    import pathlib
    import platform

    import psutil

    from .helper.baai_pbar import pbar_show, pbar_time, pbar_description

    meta_path = pathlib.Path(save_path) / "meta"
    data_path = pathlib.Path(save_path) / "data"
    temp_path = pathlib.Path(save_path) / "temp"

    print("-----------envs---------------------")
    print(f"cmd_envs, meta_path: {meta_path.absolute()}")
    print(f"cmd_envs, temp_path: {temp_path.absolute()}")
    print(f"cmd_envs, data_path: {data_path.absolute()}")
    print("")

    # 创建文件夹
    meta_path.mkdir(parents=True, exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)
    temp_path.mkdir(parents=True, exist_ok=True)

    executor_readrows_ = threading.Thread(target=download_readrows, args=(meta_path,))
    executor_readrows_.start()

    executor_progress_ = threading.Thread(target=download_progress, args=(meta_path, data_path, temp_path))
    executor_progress_.start()

    start_time = time.time()

    last_update_size = 0
    last_update_time = start_time
    last_rate_fmt =  ""
    last_change_size = 0

    while True:
        time.sleep(1)

        try:
            curr_update_time = time.time()
            curr_update_size = progress.download_size

            use_duration = curr_update_time - start_time
            change_duration = curr_update_time - last_update_time
            change_size = curr_update_size - last_update_size # speed
            if change_size <= 0:
                change_size = last_change_size
            rate_fmt = f"{psutil._common.bytes2human(int(change_size / change_duration), format="%(value).2f%(symbol)s")}/s"
            remaining = pbar_time((progress.require_size-progress.download_size)/change_size)

            # show pbar
            down_size = psutil._common.bytes2human(progress.download_size, format="%(value).2f%(symbol)s")
            total_size = psutil._common.bytes2human(progress.require_size, format="%(value).2f%(symbol)s")
            percent = progress.download_size / progress.require_size

            pbar_desc = pbar_description(progress, rate_fmt, remaining)
            pbar_output = f"[{pbar_time(use_duration)}] | {percent:.2%} | {pbar_show(percent)} | {down_size}/{total_size} | {pbar_desc}"
            logger.info(pbar_output)
            sys.stdout.write(f"\033[K{pbar_output}\r")
            sys.stdout.flush()

            last_update_time = curr_update_time
            last_update_size = curr_update_size
            last_rate_fmt = rate_fmt
            last_change_size = change_size
        except Exception: # noqa
            pass

        if progress.download_count == progress.require_count and progress.download_submit_count == progress.require_count:
            break

    executor_readrows_.join()
    executor_progress_.join()

    use_duration = pbar_time(time.time() - start_time)
    pbar_desc = pbar_description(progress, last_rate_fmt, (progress.require_size-progress.download_size)/last_change_size)
    down_size = psutil._common.bytes2human(progress.download_size, format="%(value).2f%(symbol)s")
    total_size = psutil._common.bytes2human(progress.require_size, format="%(value).2f%(symbol)s")

    pbar_end_output = f"{use_duration}] | {1:.2%} | {pbar_show(1)} | {down_size}/{total_size} | {pbar_desc}"
    sys.stdout.write(f"\033[K{pbar_end_output}\r")
    sys.stdout.flush()
    print("")


def executor_meta_download(dataset_id: str, save_path: str, **extra_kwargs):
    config = Application()
    meta_path = pathlib.Path(save_path) / "meta"


    print("-----------meta--------------------")
    meta_list = meta_path.glob("*.bin")
    for idx, meta_file in enumerate(meta_list):
        print(f"{meta_file.absolute()}")
        if idx >= 5:
            print("...")
            break

    # 读取需求获取meta信息
    csv_list = list(meta_path.glob("*.csv"))
    if len(csv_list) > 0:
        post_api = config.meta_download_api % "meta-setup"
        for idx, csv_file in enumerate(csv_list):
            with csv_file.open("r") as freader:
                csv_reader = csv.reader(freader)
                dataset_files = []
                for row in csv_reader:
                    if row[0] == "":
                        break
                    dataset_files.append(row[0])
                    try:
                        req_data = {"dataset_id": dataset_id, "dataset_files": dataset_files}
                        resp_meta_ = read_remote_meta(f"{post_api}", json=req_data)
                    except AssertionError as e:
                        raise e
                        logger.error(e)
                        break
                    else:
                        meta_part_path = meta_path / f"{dataset_id}_setup_{idx}.bin"
                        meta_data_part = resp_meta_.get("data").get("download_set")
                        if len(meta_data_part) != 0:
                            save_remote_meta(meta_part_path, meta_data_part)
    else:
        post_api = config.meta_download_api % "meta-down"
        offset, limit = 0, 500
        while True:
            try:
                req_data = {"dataset_id": dataset_id, "prefix": extra_kwargs.get("dir_path")}
                logger.info("meta-down: %s", req_data)
                resp_meta_ = read_remote_meta(f"{post_api}?offset={offset}&limit={limit}", json=req_data)
                assert resp_meta_.get("code") == 0, resp_meta_.get("message")
            except AssertionError as e:
                raise e
                logger.error(e)
                break
            else:
                meta_part_path = meta_path / f"{dataset_id}_{offset}.bin"
                meta_data_part= resp_meta_.get("data").get("download_set")
                if len(meta_data_part) != 0:
                    save_remote_meta(meta_part_path, meta_data_part)
                if resp_meta_.get("data").get("search_count") == 0:
                    break
                offset = offset + limit


# ------- download data ----------

def check_file(file_path: str, length: int):
    path = pathlib.Path(file_path)
    if not path.exists():
        return False
    check_size = path.stat().st_size
    return check_size== length

def sign_download(sign_path: str):
    config = Application()

    user_login_token = config.try_login()
    req_headers = {
        "Authorization": f"Bearer {user_login_token}",
    }
    req_headers.update(config.req_header)

    req_sign_json = { # noqa
        "network": config.network or "public",
        "download_sign": sign_path,
    }

    try:
        resp_sign = requests.post(config.sign_download_api, headers=req_headers, json=req_sign_json)
    except Exception as e:
        logger.error(e)
        sign_addr = ""
    else:
        sign_addr = resp_sign.json().get("data").get("endpoint")
    return sign_addr

# --------- remote meta -----------
def read_remote_meta(request_api, json=None, **kwargs): # noqa
    config = Application()

    user_login_token = config.try_login()
    req_headers = {
        "Authorization": f"Bearer {user_login_token}",
    }
    req_headers.update(config.req_header)

    try:
        resp = requests.post(request_api, json=json, headers=req_headers)
        if resp.status_code == 401:
            raise AssertionError("请重新登录")
        assert resp.status_code == 200, f"status_code: {resp.status_code}"
        assert resp.json().get("code") == 0, resp.json().get("message")
        data_meta = resp.json()
        return data_meta
    except AssertionError as e:
        logger.info(f"read_remote_meta, {request_api}, {e}")
        raise AssertionError(f"{e}")



def save_remote_meta(meta_path: pathlib.Path, meta_data):
    print(f"meta_download: {meta_path.absolute().__str__()}")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w") as fwriter:
        csv_writer = csv.DictWriter(fwriter, fieldnames=["download_sign", "download_size", "download_extn"])
        csv_writer.writeheader()
        csv_writer.writerows(meta_data)


# --------- auth login -----------
def executor_user_signin():
    config = Application()

    resp = requests.post(config.auth_login_api, headers=config.req_header, json={"ak": config.ak, "sk": config.sk})
    assert resp.status_code == 200, resp.status_code
    assert resp.json().get("code") == 0, resp.text
    config.set_init_token(resp.json().get("data").get("token"))


# --------- logger_download -----------
def logger_download(dataset_id: str, status: int=1, search: str="/"):
    config = Application()

    user_login_token = config.try_login()
    req_headers = {
        "Authorization": f"Bearer {user_login_token}",
    }
    req_headers.update(config.req_header)
    data = {"datasetId": dataset_id, "status": status, "filePath": search or "/"}
    try:
        resp = requests.post(config.log_download_api, headers=req_headers, json=data, timeout=2)
    except Exception as e:
        logger.error(f"logger_download,  {e}")
    else:
        logger.info(f"logger_download, {resp.status_code}, {resp.text}")
