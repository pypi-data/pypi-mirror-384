#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
import traceback

# Import your existing functions
from .cos_core_ops import (
    list_all_files_under_cos_dir_cli,
    download_cos_file,
    download_cos_dir_cli,
    delete_cos_file,
    upload_file2cos,
    upload_dir2cos_cli,
    _split_cosdir,
    _split_cospath,
)


def to_absolute_path(path: str) -> str:
    """
    Convert a given path (which may contain ~, ., or ..)
    into an absolute, normalized path.

    Examples:
        ~/project   → /home/jiaqi/project
        ./data/..   → /current/working/dir
        ../logs     → /parent/of/current/working/dir/logs
    """
    # 1. Expand ~ (home directory)
    expanded = os.path.expanduser(path)
    # 2. Convert to absolute path (resolves . and ..)
    absolute = os.path.abspath(expanded)
    # 3. Normalize redundant slashes, etc.
    normalized = os.path.normpath(absolute)
    return normalized


def get_cos_config():
    """Get COS config from environment variables"""
    try:
        return {
            'secret_id': os.environ["COS_SECRET_ID"],
            'secret_key': os.environ["COS_SECRET_KEY"],
            'region': os.environ["COS_REGION"],
        }
    except KeyError as e:
        print(f"Error: Missing environment variable {e}")
        print("Please set COS_SECRET_ID, COS_SECRET_KEY, and COS_REGION")
        sys.exit(1)


def list_files():
    """CLI command to list files in COS directory"""
    parser = argparse.ArgumentParser(description='List files in COS directory')
    parser.add_argument('cos_dir', help='COS directory path (cos://bucket/prefix)')
    parser.add_argument('-f', '--list_result_save_path', help='Path to save list result', default="list_result.txt")
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    config = get_cos_config()
    
    try:
        list_all_files_under_cos_dir_cli(
            cos_dir=args.cos_dir,
            config=config,
            verbose=args.verbose,
            list_result_save_path=args.list_result_save_path,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def download_file():
    """CLI command to download file from COS"""
    parser = argparse.ArgumentParser(description='Download file from COS')
    parser.add_argument('cos_path', help='COS file path (cos://bucket/path/file.txt)')
    parser.add_argument('given_path', help='Local file path to save to')
    parser.add_argument('--part_size', type=int, help='The size of the part to download.(Unit: MB)', default=1)
    parser.add_argument('--max_thread', '-j', type=int, help='The maximum number of threads to use.', default=30)
    parser.add_argument('--enable_crc', action='store_true', help='Whether to enable CRC checksum.', default=False)
    parser.add_argument('--num_retry', '-r', type=int, help='The number of times to retry the download.', default=1)
    args = parser.parse_args()
    config = get_cos_config()
    is_dir = False
    if args.given_path.endswith("/"):
        is_dir = True
    given_path = to_absolute_path(args.given_path)
    
    _, _, file_name = _split_cospath(args.cos_path)
    if os.path.isdir(given_path):
        local_file_path = os.path.join(given_path, file_name)
    elif os.path.isfile(given_path):
        local_file_path = given_path
    else:
        if is_dir:
            local_file_path = os.path.join(given_path, file_name)
            os.makedirs(local_file_path, exist_ok=True)
        else:
            local_file_path = given_path
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    
    try:
        download_cos_file(
            cos_path=args.cos_path,
            local_file_path=local_file_path,
            config=config,
            part_size=args.part_size,
            max_thread=args.max_thread,
            enable_crc=args.enable_crc,
            num_retry=args.num_retry,
        )
        print(f"Downloaded {args.cos_path} to {local_file_path}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)
        
        
def download_dir():
    """CLI command to download file from COS"""
    parser = argparse.ArgumentParser(description='Download file from COS')
    parser.add_argument('cos_dir', help='COS dir path (cos://bucket/path/)')
    parser.add_argument('given_local_dir', help='Local dir to save to')
    parser.add_argument('--max_thread', '-j', help='The maximum number of threads to use.', default=30)
    parser.add_argument('--flat', '-f', action='store_true', help='whether to download the cos dir flatly', default=False)
    args = parser.parse_args()
    config = get_cos_config()
    given_local_dir = to_absolute_path(args.given_local_dir)
    _, prefix = _split_cosdir(args.cos_dir)
    cos_dirname = prefix.split("/")[-1]
    if args.flat:
        given_local_dir = given_local_dir
    else:
        given_local_dir = os.path.join(given_local_dir, cos_dirname)
    os.makedirs(given_local_dir, exist_ok=True)
    
    try:
        download_cos_dir_cli(
            cos_dir=args.cos_dir,
            local_dir=given_local_dir,
            config=config,
            max_thread=args.max_thread,
            flat=args.flat,
        )
        print(f"Downloaded {args.cos_dir} to {given_local_dir}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


def upload_file():
    """CLI command to upload file to COS"""
    parser = argparse.ArgumentParser(description='Upload file to COS')
    parser.add_argument('local_path', help='Local file path to upload')
    parser.add_argument('cos_path', help='COS file path (cos://bucket/path/file.txt)')
    parser.add_argument('--part_size', type=int, help='The size of the part to upload.(Unit: MB)', default=1)
    parser.add_argument('--max_thread', '-j', type=int, help='The maximum number of threads to use.', default=30)
    parser.add_argument('--enable_md5', action='store_true', help='Whether to enable MD5 checksum.', default=False)
    args = parser.parse_args()
    config = get_cos_config()
    
    is_dir = False
    if args.cos_path.endswith("/"):
        is_dir = True
    
    if not os.path.exists(to_absolute_path(args.local_path)):
        raise FileNotFoundError(f"File {args.local_path} not found")
    
    local_filename = os.path.basename(args.local_path)
    if is_dir:
        cos_path = f"{args.cos_path}{local_filename}"
    else:
        cos_path = args.cos_path
    
    try:
        upload_file2cos(
            local_file_path=args.local_path,
            cos_save_path=cos_path,
            config=config,
            part_size=args.part_size,
            max_thread=args.max_thread,
            enable_md5=args.enable_md5,
        )
        print(f"Uploaded {args.local_path} to {cos_path}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"cos save path: {cos_path}")
        traceback.print_exc()
        sys.exit(1)


def upload_dir():
    """CLI command to upload dir to COS"""
    parser = argparse.ArgumentParser(description='Upload dir to COS')
    parser.add_argument('local_dir', help='Local dir to upload')
    parser.add_argument('cos_dir', help='COS dir path (cos://bucket/path/)')
    parser.add_argument('--part_size', help='The size of the part to upload.(Unit: MB)', default=1)
    parser.add_argument('--max_thread', '-j', help='The maximum number of threads to use.', default=30)
    parser.add_argument('--enable_md5', help='Whether to enable MD5 checksum.', default=False)
    parser.add_argument('--flat', '-f', help='whether to upload the local dir flatly', default=False)
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    config = get_cos_config()
    
    
    local_upload_dir = to_absolute_path(args.local_dir)
    if not os.path.exists(local_upload_dir):
        raise FileNotFoundError(f"Dir {local_upload_dir} not found")
    
    try:
        upload_dir2cos_cli(
            local_upload_dir=local_upload_dir,
            cos_dir=args.cos_dir,
            config=config,
            part_size=args.part_size,
            max_thread=args.max_thread,
            enable_md5=args.enable_md5,
            flat=args.flat,
        )
        print(f"Uploaded {args.local_dir} to {args.cos_dir}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    



def delete_file():
    """CLI command to delete file from COS"""
    parser = argparse.ArgumentParser(description='Delete file from COS')
    parser.add_argument('cos_path', help='COS file path (cos://bucket/path/file.txt)')
    parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    
    args = parser.parse_args()
    config = get_cos_config()
    
    if not args.confirm:
        response = input(f"Are you sure you want to delete {args.cos_path}? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    
    try:
        delete_cos_file(
            cos_path=args.cos_path,
            config=config,
        )
        print(f"Deleted {args.cos_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)