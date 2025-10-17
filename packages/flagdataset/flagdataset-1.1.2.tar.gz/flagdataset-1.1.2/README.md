# flagdataset
---------------------

flagdataset 是一个用于下载数据集的 Python 包。


## 示例


### sdk

```python
# pip install flagdataset

from flagdataset import new_downloader

if __name__ == "__main__":

    # 初始化, 传入AK,SK
    loader = new_downloader(ak="<Access Key>", sk="<Secret Key>")

    # 整体下载: 下载数据集全部内容
    loader.download(dataset_id="10372875450064908", target="/path/to/local/folder")

    # 文件夹下载: 下载数据集指定文件夹下内容
    loader.download(dataset_id="10372875450064908", path="/path/to/source/folder", target="/path/to/local/folder")

    # 单文件下载: 下载数据集指定文件
    loader.get(dataset_id="10372875450064908", path="/path/to/source/folder/example.txt", target="/path/to/local/folder")

```


### cli

```sh
# 安装
pip install flagdataset

# 查看帮助
flagdataset -h

# 常用参数说明
#  -d 数据集ID: dataset-id
#  -p 数据集文件(夹)路径: path
#  -t 下载保存路径: target

# 使用AK,SK登录
flagdataset login

# 整体下载: 下载数据集全部内容
flagdataset download -d 10372875450064908 -t .

# 文件夹下载: 下载数据集指定文件夹下内容，需要指定 -p 参数
flagdataset download -d 10372875450064908 -t . -p "/path/to/source/folder"

# 单文件下载: 下载数据集指定文件，需要指定 -p 参数
flagdataset get -d 10372875450064908 -t . -p "/path/to/source/folder/example.json"
```
