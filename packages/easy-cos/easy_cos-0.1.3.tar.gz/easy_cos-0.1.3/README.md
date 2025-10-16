# easy_cos

让数据流动变得简单！Make data flow!
```bash
pip install cos-python-sdk-v5

pip install easy_cos==0.1.3 --index-url https://pypi.tuna.tsinghua.edu.cn/simple
# pip install easy_cos==0.1.3 --index-url https://pypi.org/simple  #清华等其他镜像源可能同步慢
```


这个库的开发是包含了大部分常用的 cos 脚本操作，避免许多重复代码。以及让很多新入职的同事能够快速用起来我们的数据。、
<br>
<br>
<br>

## 快捷命令行指令
```bash
# 在 ～/.bashrc 中添加：
export COS_SECRET_ID="YOUR_COS_SECRET_ID"
export COS_SECRET_KEY="YOUR_COS_SECRET_KEY"
export COS_REGION="ap-guangzhou"

# 之后则可以使用快捷命令行指令：
cos_list        bucket_name/prefix                                  # 列出 bucket_name/prefix 下的所有文件
cos_download    bucket_name/prefix/file.txt local/path/file.txt     # 下载 bucket_name/prefix/file.txt 到 local/path/file.txt
cos_download_r  bucket_name/dir local/path                          # 下载 bucket_name/prefix 到 local/path
cos_upload      local/path bucket_name/prefix/file.txt              # 上传 local/path 到 bucket_name/prefix/file.txt
cos_upload_r    local/dir bucket_name/prefix                        # 上传 local/path 到 bucket_name/prefix
cos_delete      bucket_name/prefix/file.txt                         # 删除 bucket_name/prefix/file.txt
```

<br>
<br>
<br>

# Python API 示例
```python
import os
COS_CONFIG = {
    'secret_id': f'{os.environ["COS_SECRET_ID"]}',
    'secret_key': f'{os.environ["COS_SECRET_KEY"]}',
    'region': f'{os.environ["COS_REGION"]}',
}
```


## 场景一（list all files under a cos dir）：

```python
from easy_cos import list_all_files_under_cos_dir

list_all_files_under_cos_dir(
    cos_dir="bucket_name/prefix",
    config=COS_CONFIG,
    verbose=True,
    return_path_only=True,
)
```

## 场景二（check if a cos path exists）：

```python
from easy_cos import check_cos_path_exist

check_cos_path_exist(
    cos_path="bucket_name/prefix/file.txt",
    config=COS_CONFIG,
)
``` 

## 场景三（delete a cos file）：

```python
from easy_cos import delete_cos_file

delete_cos_file(
    cos_path="bucket_name/prefix/file.txt",
    config=COS_CONFIG,
)
```

## 场景四（delete a cos dir）：

```python
from easy_cos import delete_cos_dir

delete_cos_dir(
    cos_dibucket_name/prefix",
    config=COS_CONFIG,
)
```

## 场景五（download a cos file）：

```python
from easy_cos import download_cos_file

download_cos_file(
    cos_path="bucket_name/prefix/file.txt",
    local_file_path="local/path/file.txt",
    config=COS_CONFIG,
)
```

## 场景六（download a cos dir）：

```python
from easy_cos import download_cos_dir

download_cos_dir(
    cos_dir="bucket_name/prefix",
    local_dir="local/path",
    config=COS_CONFIG,
)
```


## 场景七（save an image to cos）：

```python
from easy_cos import save_img2cos

save_img2cos(
    img=Image.open("image.jpg"),
    cos_save_path="bucket_name/prefix/image.jpg",
    config=COS_CONFIG,
)
```

## 场景八（upload a file to cos）：

```python
from easy_cos import upload_file2cos

upload_file2cos(
    local_file_path="local/path/file.txt",
    cos_save_path="bucket_name/prefix/file.txt",
    config=COS_CONFIG,
)
```


## 场景九（upload a dir to cos）：

```python
from easy_cos import upload_dir2cos

upload_dir2cos(
    local_upload_dir="local/path",
    cos_dir="bucket_name/prefix",
    config=COS_CONFIG,
)