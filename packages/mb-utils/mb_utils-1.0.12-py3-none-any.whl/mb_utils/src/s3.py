##file for s3 download and upload

import boto3
import os
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from tqdm.auto import tqdm

__all__ = ['download_file', 'upload_file', 'upload_dir', 'download_dir','list_objects']

def download_file(bucket_name, file_name, local_file_name,logger=None):
    """
    download file from s3
    Input:
        bucket_name: name of the bucket
        file_name: name of the file in s3
        local_file_name: name of the file in local
    Output:
        None
    """
    s3 = boto3.resource('s3')
    try:
        s3.Bucket(bucket_name).download_file(file_name, local_file_name)
    except Exception as e:
        if logger:
            logger.error('Error in downloading file from s3')
            logger.error(e)
        raise e
    if logger:
        logger.info('Downloaded file from s3')

def upload_file(bucket_name, file_name, local_file_name,logger=None):
    """
    upload file to s3
    Input:
        bucket_name: name of the bucket
        file_name: name of the file in s3
        local_file_name: name of the file in local
    Output:
        None
    """
    s3 = boto3.resource('s3')
    try:
        s3.Bucket(bucket_name).upload_file(local_file_name, file_name)
    except Exception as e:
        if logger:
            logger.error('Error in uploading file to s3')
            logger.error(e)
        raise e
    if logger:
        logger.info('File uploaded to s3')

def upload_dir(bucket_name, dir_name, local_dir_name,logger=None):
    """
    upload directory to s3
    Input:
        bucket_name: name of the bucket
        dir_name: name of the directory in s3
        local_dir_name: name of the directory in local
    Output:
        results (List) : list of uploaded files location. False if error in uploading individual file
    """
    s3 = boto3.resource('s3')
    
    file_list = []
    def _get_all_files(local_dir_name):
        return [os.path.join(dp, f) for dp, _, filenames in os.walk(local_dir_name) for f in filenames]
    file_list = _get_all_files(local_dir_name)
    
    def _upload_file(bucket,dir_name,file):
        try:
            file_name = file.split('/')[-1]
            file_loc = os.path.join(dir_name, file_name)
            s3.Bucket(bucket).upload_file(file, file_loc)
            return file_loc
        except Exception as e:
            return False

    upload_func = partial(_upload_file, bucket=bucket_name, dir_name=dir_name)

    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(tqdm(executor.map(upload_func, file_list), total=len(file_list), mininterval=1))

    if results.count(False) > 0:
        if logger:
            logger.error('Error in uploading files : {i}'.format(i=results.count(False)))
        else:
            print('Error in uploading files : {i}'.format(i=results.count(False)))
    else:
        if logger:
            logger.info('All files uploaded to s3 : {i}'.format(i=len(results)))
        else:
            print('All files uploaded to s3 : {i}'.format(i=len(results)))
    return results

def download_dir(bucket_name, dir_name, local_dir_name=None,max_workers=8):
    """
    download directory from s3
    Input:
        bucket_name: name of the bucket
        dir_name: name of the directory in s3
        local_dir_name: name of the directory in local
        max_workers: number of parallel workers to use
    Output:
        results (List) : list of downloaded files location
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    def _download_file(bucket, local_dir_name):
        for obj in bucket.objects.filter(Prefix=local_dir_name):
            target = obj.key if local_dir_name is None \
                else os.path.join(local_dir_name, os.path.relpath(obj.key, dir_name))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            if obj.key[-1] == '/':
                continue
            bucket.download_file(obj.key, target)
            return target

    download_func = partial(_download_file, bucket=bucket, local_dir_name=local_dir_name)
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(download_func, [local_dir_name]), total=1, mininterval=1))
    return results  


def list_objects(bucket_name,logger=None,**kwargs):
    """
    List all the objects in the bucket
    Args:
        bucket_name : str
            Name of the bucket
    Returns:
        List of objects in the bucket
    """
    s3 = boto3.resource('s3')
    objects = s3.list_objects_v2(Bucket=bucket_name)

    if 'Contents' in objects:
        for obj in objects['Contents']:
            if logger:
                logger.info(obj['Key'])
            else:
                print(obj['Key'])
        return objects['Contents']
    else:
        if logger:
            logger.info(f"No objects found in {bucket_name}")
        else:
            print(f"No objects found in {bucket_name}")
        return []