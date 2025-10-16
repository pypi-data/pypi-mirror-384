from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos import CosServiceError, CosClientError
from qcloud_cos.cos_threadpool import SimpleThreadPool
import io
import contextlib
import sys
import os
from PIL import Image
from .io_utils import write_list_to_txt, to_absolute_path
from .parallel import multi_thread_tasks
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tqdm import tqdm 

@contextlib.contextmanager
def SuppressPrint():
    """
    A context manager to temporarily suppress print statements.

    Usage:
    with SuppressPrint():
        noisy_function()
    """
    original_stdout = sys.stdout
    with open(os.devnull, 'w') as devnull:
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = original_stdout
            

def _split_cospath(cos_path: str) -> tuple:
    """
    Split the given COS file path into its components.

    Args:
    path (str): The COS file path to be split.

    Returns:
    tuple: A tuple containing the bucket name, prefix, and file name.
    """
    split_path = cos_path.split("/")
    bucket_name = split_path[0]
    prefix = "/".join(split_path[1:-1])
    file_name = split_path[-1]
    return bucket_name, prefix, file_name

def _split_cosdir(cos_dir: str) -> tuple:
    """
    Split the given COS directory into its components.

    Args:
    path (str): The COS directory to be split.

    Returns:
    tuple: A tuple containing the bucket name, prefix.
    """
    if cos_dir.endswith("/"):
        split_dir = cos_dir.split("/")[:-1]
    else:
        split_dir = cos_dir.split("/")
    bucket_name = split_dir[0]
    prefix = "/".join(split_dir[1:])
    return bucket_name, prefix

########################################################
# List
########################################################

def list_all_files_under_cos_dir(
    cos_dir: str, 
    config: dict,
    verbose: bool = True, 
    return_path_only: bool = True
) -> list:
    bucket_name, prefix = _split_cosdir(cos_dir)
    
    if verbose:
        print(f"Listing all files under {bucket_name}/{prefix}...")
        
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)
    
    marker = ""
    count = 0
    all_info = []
    while True:
        if verbose:
            print(f"{count * 1000} files have been found!", end="\r")
        response = client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix,
            Marker=marker
            )
        if 'Contents' in response:
            all_info.extend(response['Contents'])
        if response['IsTruncated'] == 'false':
            break 
        marker = response['NextMarker']
        count += 1
    if verbose:
        print(f"Total {len(all_info)} files have been found!")
        
    if not return_path_only:
        return all_info
    else:
        return [f"{bucket_name}/{file['Key']}" for file in all_info]


def list_all_files_under_cos_dir_cli(
    cos_dir: str, 
    config: dict,
    verbose: bool = True, 
    list_result_save_path: str = "list_result.txt"
) -> None:
    bucket_name, prefix = _split_cosdir(cos_dir)
    
    if verbose:
        print(f"Listing all files under {bucket_name}/{prefix}...")
        
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)
    
    marker = ""
    count = 0
    all_info = []
    while True:
        if verbose:
            print(f"{count * 1000} files have been found!", end="\r")
        response = client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix,
            Marker=marker
            )
        if 'Contents' in response:
            all_info.extend(response['Contents'])
        if response['IsTruncated'] == 'false':
            break 
        marker = response['NextMarker']
        count += 1
    if verbose:
        print(f"Total {len(all_info)} files have been found!")
        
    all_paths = [f"{bucket_name}/{file['Key']}" for file in all_info]
    write_list_to_txt(all_paths, list_result_save_path)
    print(f"List result has been saved to {list_result_save_path}")


########################################################
# Check
########################################################

def check_cos_path_exist(
    cos_path,
    config
):
    """
    Check if the given COS path exists.
    Input:
        cos_path: str, the path of the COS file
        config: dict, the configuration of the COS client
    Output:
        bool, True if the file exists, False otherwise
    """
    bucket_name, prefix, file_name = _split_cospath(cos_path)
    object_key = f"{prefix}/{file_name}"
    
    config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(config)
    
    response = client.object_exists(
        Bucket=bucket_name,
        Key=object_key
    )
    return response

########################################################
# Delete File and Directory
########################################################
def delete_cos_file(cos_path: str, config: dict):
    bucket_name, prefix, file_name = _split_cospath(cos_path)
    key = f"{prefix}/{file_name}"
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)

    response = client.delete_object(
        Bucket=bucket_name,
        Key=key
    )
    return response


def delete_cos_dir(
    cos_dir: str,
    config: dict
):
    def delete_files(file_infos, client):

        # 构造批量删除请求
        delete_list = []
        for file in file_infos:
            delete_list.append({"Key": file['Key']})

        response = client.delete_objects(Bucket=bucket_name, Delete={"Object": delete_list})
        # print(response)
        
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)
    bucket_name, prefix = _split_cosdir(cos_dir)
    pool = SimpleThreadPool()
    marker = ""
    while True:
        file_infos = []
        response = client.list_objects(Bucket=bucket_name, Prefix=prefix, Marker=marker, MaxKeys=100)

        if "Contents" in response:
            contents = response.get("Contents")
            file_infos.extend(contents)
            pool.add_task(delete_files, file_infos, client)

        # 列举完成，退出
        if response['IsTruncated'] == 'false':
            break

        # 列举下一页
        marker = response["NextMarker"]

    pool.wait_completion()
        
    return None   


########################################################
# Download File and Directory
########################################################
def percentage_handler(consumed_bytes, total_bytes, start_time=time.time(), bar_length=40):
    """
    Fancy download progress bar with animation, speed, and ETA.

    :param consumed_bytes: Bytes downloaded so far
    :param total_bytes: Total bytes to download
    :param start_time: Download start time (time.time())
    :param bar_length: Visual width of the progress bar
    """
    if not total_bytes:
        return

    progress = min(float(consumed_bytes) / float(total_bytes), 1.0)
    percent = int(progress * 100)
    filled_length = int(bar_length * progress)
    bar = "█" * filled_length + "-" * (bar_length - filled_length)

    # Spinner animation
    spinner = "|/-\\"
    spin_char = spinner[int(time.time() * 8) % len(spinner)]

    # Speed calculation
    elapsed = time.time() - start_time
    speed = consumed_bytes / elapsed if elapsed > 0 else 0  # bytes/sec

    # ETA calculation
    remaining_bytes = total_bytes - consumed_bytes
    eta = remaining_bytes / speed if speed > 0 else 0

    # Format nicely
    def format_time(seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            m, s = divmod(int(seconds), 60)
            return f"{m}m{s:02d}s"
        else:
            h, m = divmod(int(seconds) // 60, 60)
            return f"{h}h{m:02d}m"

    sys.stdout.write(
        f"\r{spin_char} |{bar}| {percent:3d}% "
        f"{consumed_bytes/1e6:6.1f}/{total_bytes/1e6:.1f} MB "
        f"{speed/1e6:5.2f} MB/s ETA {format_time(eta)}"
    )
    sys.stdout.flush()

    if consumed_bytes >= total_bytes:
        sys.stdout.write("\n")


def download_cos_file(
    cos_path: str,
    local_file_path: str,
    config: dict,
    part_size: int = 1,
    max_thread: int = 30,
    enable_crc: bool = False,
    num_retry: int = 10,
    **kwargs
):
    bucket_name, prefix, file_name = _split_cospath(cos_path)
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)

    response = client.download_file(
        Bucket=bucket_name,
        Key=f"{prefix}/{file_name}",
        DestFilePath=local_file_path,
        PartSize=part_size,
        MAXThread=max_thread,
        EnableCRC=enable_crc,
        progress_callback=percentage_handler,
        **kwargs
    )

    # 使用高级接口断点续传，失败重试时不会下载已成功的分块(这里重试10次)
    for i in range(0, num_retry):
        try:
            response = client.download_file(
                Bucket=bucket_name,
                Key=f"{prefix}/{file_name}",
                DestFilePath=local_file_path,
                PartSize=part_size,
                MAXThread=max_thread,
                EnableCRC=enable_crc,
                **kwargs
            )
            break
        except CosClientError or CosServiceError as e:
            print(e)
            
    return response


def download_cos_dir(
    cos_dir: str,
    local_dir: str,
    config: dict, 
    max_thread: int = 30, 
    flat: bool = False,
):
    bucket_name, prefix = _split_cosdir(cos_dir)
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)
    
    filepaths = list_all_files_under_cos_dir(cos_dir, config, return_path_only=True, verbose=False)
    file_infos = sorted(filepaths)
        
        
    pool = SimpleThreadPool(num_threads=max_thread)
    
    for cos_path in file_infos:
        # 文件下载 获取文件到本地
        filename = cos_path.split("/")[-1]
        local_path = f"{local_dir}/{filename}"
        os.makedirs(local_dir, exist_ok=True)

        # skip dir, no need to download it
        if str(local_path).endswith("/"):
            continue
        bucket_name, prefix, filename = _split_cospath(cos_path)
        key = f"{prefix}/{filename}" if prefix else filename
        print(f"Downloading {cos_path} to {local_path}")
        pool.add_task(client.download_file, bucket_name, key, local_path, MAXThread=max_thread)

    pool.wait_completion()


def download_cos_dir_cli(
    cos_dir: str,
    local_dir: str,
    config: dict, 
    flat: bool = False,
    max_thread: int = 30,
    max_jobs: int = 16,
    batch_size: int = 10000,
):
    """
    Download all files under a COS directory with a visual progress bar,
    preserving relative paths with respect to `cos_dir`.

    Example:
        cos://my-bucket/a/b/c/x/file.txt  →  /local/output/x/file.txt
    """
    bucket_name, base_prefix = _split_cosdir(cos_dir)
    cos_config = CosConfig(
        Region=config['region'],
        SecretId=config['secret_id'],
        SecretKey=config['secret_key']
    )
    client = CosS3Client(cos_config)
    os.makedirs(local_dir, exist_ok=True)

    filepaths = list_all_files_under_cos_dir(
        cos_dir, config, return_path_only=True, verbose=False
    )
    file_infos = sorted(filepaths)
    total_files = len(file_infos)

    if total_files == 0:
        print("No files found under COS directory.")
        return

    success_count, fail_count = 0, 0

    with tqdm(total=total_files, desc="Downloading files from COS", unit="file") as pbar:
        with ThreadPoolExecutor(max_workers=max_jobs) as executor:
            for i in range(0, len(file_infos), batch_size):
                batch_file_infos = file_infos[i : i + batch_size]
                future_to_task = {}

                for cos_path in batch_file_infos:
                    if cos_path.endswith("/"):
                        pbar.update(1)
                        continue

                    bucket_name, prefix, filename = _split_cospath(cos_path)
                    key = f"{prefix}/{filename}" if prefix else filename

                    # Compute relative path to the given base_prefix (cos_dir)
                    full_key = key  # full path in bucket
                    if base_prefix and full_key.startswith(base_prefix):
                        rel_key = os.path.relpath(full_key, base_prefix)
                    else:
                        rel_key = full_key

                    # Compute local file path
                    if flat:
                        local_path = os.path.join(local_dir, filename)
                    else:
                        local_path = os.path.join(local_dir, rel_key)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)

                    # Submit download
                    future = executor.submit(
                        client.download_file, bucket_name, key, local_path, MAXThread=max_thread
                    )
                    future_to_task[future] = local_path

                # Handle finished downloads
                for future in as_completed(future_to_task):
                    local_path = future_to_task[future]
                    try:
                        future.result()
                        if os.path.exists(local_path):
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        fail_count += 1
                        print(f"Error downloading {local_path}: {e}")
                    finally:
                        pbar.update(1)
                        pbar.set_postfix({"✅": success_count, "❌": fail_count})

    print(f"\nAll Done! ✅ {success_count} succeeded | ❌ {fail_count} failed | Total: {total_files}")


########################################################
# Upload File and Directory
########################################################

def save_img2cos(
    img: Image.Image,
    cos_save_path: str,
    config: dict,
) -> dict:
    img_stream = io.BytesIO()
    img.save(img_stream, format="JPEG")
    img_stream.seek(0)
    return upload_stream2cos(img_stream, cos_save_path, config)

def upload_stream2cos(
    stream: io.BytesIO,
    cos_save_path: str,
    config: dict,
) -> dict:
    
    bucket_name, prefix, file_name = _split_cospath(cos_save_path)
    key_name = f"{prefix}/{file_name}"
    
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)
    
    response = client.put_object(
        Bucket=bucket_name,
        Body=stream,
        Key=key_name,
    )
    return response


def upload_file2cos(
    local_file_path: str,
    cos_save_path: str,
    config: dict, 
    part_size: int = 1, 
    max_thread: int = 30, 
    enable_md5: bool = False
) -> dict:
    """
    Upload a local file to COS.

    Args:
    local_file_path (str): The path to the local file to upload.
    cos_save_path (str): The path to save the file on TOS.
    config (dict): The configuration for the COS client.
    part_size (int): The size of the part to upload.(Unit: MB)
    max_thread (int): The maximum number of threads to use.
    enable_md5 (bool): Whether to enable MD5 checksum.

    """
    bucket_name, prefix, file_name = _split_cospath(cos_save_path)
    key_name = f"{prefix}/{file_name}"
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])
    client = CosS3Client(cos_config)
    
    response = client.upload_file(
        Bucket=bucket_name,
        LocalFilePath=local_file_path,
        Key=key_name,
        PartSize=part_size,
        MAXThread=max_thread,
        EnableMD5=enable_md5,
        progress_callback=percentage_handler,
    )
    return response

def upload_dir2cos(
    local_upload_dir: str,
    cos_dir: str,
    config: dict,
    part_size: int = 1,
    max_thread: int = 30,
    enable_md5: bool = False,
    flat: bool = False,
    verbose: bool = False,
    check_exist: bool = True,
):
    """
    Upload a local directory to COS.

    Args:
        local_upload_dir (str): The local directory to upload.
        cos_dir (str): The COS directory to upload to.
        config (dict): The configuration for the COS client.
        part_size (int): The size of the part to upload.(Unit: MB)
        max_thread (int): The maximum number of threads to use.
        enable_md5 (bool): Whether to enable MD5 checksum.
        flat (bool): Whether to upload the files flatly.
        verbose (bool): Whether to print verbose information.
    """
    bucket_name, prefix = _split_cosdir(cos_dir)
    cos_config = CosConfig(Region=config['region'], SecretId=config['secret_id'], SecretKey=config['secret_key'])  # 获取配置对象
    client = CosS3Client(cos_config)

    bucket_name, prefix = _split_cosdir(cos_dir)

    # 创建上传的线程池
    pool = SimpleThreadPool()
    # 创建线程池时若不指定线程数则默认为5。线程数可通过参数指定，例如指定线程数为10：
    # pool = SimpleThreadPool(num_threads=10)
    for path, dir_list, file_list in os.walk(local_upload_dir):
        for file_name in file_list:
            local_filepath = os.path.join(path, file_name)
            if flat:
                cosObjectKey = os.path.join(prefix, file_name)
            else:
                parent_dir = path.split('/')[-1]
                cosObjectKey = os.path.join(prefix, parent_dir, file_name)
                
                
            # 判断 COS 上文件是否存在
            exists = False
            if check_exist:
                try:
                    response = client.head_object(Bucket=bucket_name, Key=cosObjectKey)
                    exists = True
                except CosServiceError as e:
                    if e.get_status_code() == 404:
                        exists = False
                    else:
                        if verbose:
                            print("Error happened, reupload it.")
                            
                            
            if check_exist and not exists:
                if verbose:
                    print("File %s not exists in cos, upload it", local_filepath)
                pool.add_task(client.upload_file,
                    Bucket=bucket_name,
                    Key=cosObjectKey,
                    LocalFilePath=local_filepath,
                    PartSize=part_size,
                    MAXThread=max_thread,
                    EnableMD5=enable_md5
                )


    pool.wait_completion()
    result = pool.get_result()
    if not result['success_all']:
        if verbose:
            print("Not all files upload successed. you should retry")
    else:
        if verbose:
            print("All files upload successed.")
    return result 


def upload_dir2cos_cli(
    local_upload_dir: str,
    cos_dir: str,
    config: dict,
    flat: bool = False,
    max_thread: int = 30,
    max_jobs: int = 16,
    part_size: int = 1,
    enable_md5: bool = False,
    batch_size: int = 10000,
    check_exist: bool = True,
    verbose: bool = False,
):
    """
    Upload a local directory to COS with a visual progress bar.
    Args:
        local_upload_dir (str): The local directory to upload.
        cos_dir (str): The COS directory to upload to, e.g. "cos://bucket-name/folder/".
        config (dict): COS config containing region, secret_id, secret_key.
        flat (bool): If True, upload all files directly under `prefix/`.
        max_thread (int): Max internal threads for each upload_file.
        max_jobs (int): Max concurrent upload tasks.
        part_size (int): Upload part size in MB.
        enable_md5 (bool): Whether to enable MD5 verification.
        batch_size (int): Number of files per job batch.
        check_exist (bool): Skip upload if file already exists on COS.
        verbose (bool): Print detailed upload info.
    """
    # Setup COS client
    bucket_name, prefix = _split_cosdir(cos_dir)
    cos_config = CosConfig(
        Region=config['region'],
        SecretId=config['secret_id'],
        SecretKey=config['secret_key']
    )
    client = CosS3Client(cos_config)

    # Gather all local files
    file_paths = []
    for root, _, files in os.walk(local_upload_dir):
        for fname in files:
            file_paths.append(os.path.join(root, fname))
    total_files = len(file_paths)

    if total_files == 0:
        print("No local files found to upload.")
        return

    success_count, fail_count, skipped_count = 0, 0, 0

    with tqdm(total=total_files, desc="Uploading files to COS", unit="file") as pbar:
        with ThreadPoolExecutor(max_workers=max_jobs) as executor:
            for i in range(0, len(file_paths), batch_size):
                batch_files = file_paths[i : i + batch_size]
                future_to_task = {}

                for local_path in batch_files:
                    file_name = os.path.basename(local_path)
                    if flat:
                        cos_key = f"{prefix}/{file_name}" if prefix else file_name
                    else:
                        # preserve subdirectory name relative to local_upload_dir
                        rel_dir = os.path.relpath(os.path.dirname(local_path), local_upload_dir)
                        cos_key = os.path.join(prefix, rel_dir, file_name).replace("\\", "/")

                    # Optional: check if file exists remotely
                    if check_exist:
                        try:
                            client.head_object(Bucket=bucket_name, Key=cos_key)
                            skipped_count += 1
                            pbar.update(1)
                            continue  # Skip already uploaded files
                        except CosServiceError as e:
                            if e.get_status_code() != 404:
                                print(f"⚠️ Error checking {cos_key}: {e}")
                                pbar.update(1)
                                continue

                    # Submit upload
                    future = executor.submit(
                        client.upload_file,
                        Bucket=bucket_name,
                        Key=cos_key,
                        LocalFilePath=local_path,
                        PartSize=part_size,
                        MAXThread=max_thread,
                        EnableMD5=enable_md5,
                    )
                    future_to_task[future] = (local_path, cos_key)

                # Process results
                for future in as_completed(future_to_task):
                    local_path, cos_key = future_to_task[future]
                    try:
                        future.result()
                        success_count += 1
                        if verbose:
                            print(f"✅ Uploaded: {local_path} → {cos_key}")
                    except Exception as e:
                        fail_count += 1
                        print(f"❌ Failed: {local_path} ({e})")
                    finally:
                        pbar.update(1)
                        pbar.set_postfix({"✅": success_count, "❌": fail_count, "⏭️": skipped_count})

    print(f"\nAll Done! ✅ {success_count} | ❌ {fail_count} | ⏭️ Skipped {skipped_count}")


