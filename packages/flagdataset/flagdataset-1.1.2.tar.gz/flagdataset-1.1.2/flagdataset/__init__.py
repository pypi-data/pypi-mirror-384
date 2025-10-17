import csv
import pathlib

from .helper.baai_login import auth_user_login


def new_downloader(ak, sk):
    return Downloader(ak, sk)


class Downloader:
    def __init__(self, ak: str, sk: str):
        self.ak = ak
        self.sk = sk

        auth_user_login(self.ak, self.sk)

    @staticmethod
    def download(dataset_id: str, path: str, target: str):
        from .baai_downloder import executor_download

        meta_path = pathlib.Path(target) / "meta"
        meta_path.mkdir(parents=True, exist_ok=True)
        # 删除所有的csv文件
        for csv_file in meta_path.glob("*.csv"):
            csv_file.unlink()

        executor_download(dataset_id, target, dir_path=path)

    @staticmethod
    def get(dataset_id: str, path: str, target: str):
        from .baai_downloder import executor_download

        meta_path = pathlib.Path(target) / "meta" # noqa
        meta_path.mkdir(parents=True, exist_ok=True)

        down_csv = meta_path / "require_file.csv"

        if meta_path.exists():
            for bin_file in meta_path.glob("*.bin"):
                bin_file.unlink()

        with down_csv.open("w", encoding="utf-8") as fwriter:
            csv_writer = csv.writer(fwriter)
            csv_writer.writerow((path,))

        executor_download(dataset_id, target, dir_path="")
