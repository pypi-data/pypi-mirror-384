import logging
import pathlib


logger = logging.getLogger(__name__)


def download_dataset(cmd_args):
    from .baai_downloder import executor_download

    dataset_id_arg = cmd_args.dataset
    save_path_arg = cmd_args.save_path
    dir_path_arg = cmd_args.dir_path.strip().lstrip("/").rstrip("/")

    meta_path = pathlib.Path(save_path_arg) / "meta"
    meta_path.mkdir(parents=True, exist_ok=True)
    # 删除所有的csv文件
    for csv_file in meta_path.glob("*.csv"):
        csv_file.unlink()

    logger.info("download_dataset: %s, %s, %s", dataset_id_arg, pathlib.Path(save_path_arg).absolute().__str__(), dir_path_arg)
    executor_download(dataset_id_arg, save_path_arg, dir_path=dir_path_arg)

def download_required(cmd_args):
    import csv
    from .baai_downloder import executor_download

    dataset_id_arg = cmd_args.dataset
    save_path_arg = cmd_args.save_path

    file_path_arg = cmd_args.file_path.strip().lstrip("/")

    meta_path = pathlib.Path(save_path_arg) / "meta"
    meta_path.mkdir(parents=True, exist_ok=True)

    down_csv = meta_path / "require_file.csv"

    if meta_path.exists():
        for bin_file in meta_path.glob("*.bin"):
            bin_file.unlink()

    with down_csv.open("w", encoding="utf-8") as fwriter:
        csv_writer = csv.writer(fwriter)
        csv_writer.writerow((file_path_arg,))

    executor_download(dataset_id_arg, save_path_arg, dir_path="")
