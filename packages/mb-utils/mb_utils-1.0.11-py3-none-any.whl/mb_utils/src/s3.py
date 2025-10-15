##file for s3 download and upload

import boto3
import os

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
        None
    """
    s3 = boto3.resource('s3')
    try:
        for root, dirs, files in os.walk(local_dir_name):
            for file in files:
                s3.Bucket(bucket_name).upload_file(os.path.join(root,file),bucket_name,dir_name)
    except Exception as e:
        if logger:
            logger.error('Error in uploading directory to s3')
            logger.error(e)
        raise e
    if logger:
        logger.info('Directory uploaded to s3')

def download_dir(bucket_name, dir_name, local_dir_name=None,logger=None):
    """
    download directory from s3
    Input:
        bucket_name: name of the bucket
        dir_name: name of the directory in s3
        local_dir_name: name of the directory in local
    Output:
        None
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    try:
        for obj in bucket.objects.filter(Prefix=local_dir_name):
            target = obj.key if local_dir_name is None \
                else os.path.join(local_dir_name, os.path.relpath(obj.key, dir_name))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            if obj.key[-1] == '/':
                continue
            bucket.download_file(obj.key, target)
    except Exception as e:
        if logger:
            logger.error('Error in downloading directory from s3')
            logger.error(e)
        raise e
    if logger:
        logger.info('Downloaded directory from s3')

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