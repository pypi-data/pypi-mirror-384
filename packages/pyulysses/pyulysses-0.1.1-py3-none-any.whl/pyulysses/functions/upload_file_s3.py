import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'src')
    ),
)

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from configs.env_loader import get_aws_config
from logger.logger_config import setup_logger

logger = setup_logger()


def upload_file_to_s3(file_path, s3_folder):
    if not os.path.exists(file_path):
        logger.error(f"File '{file_path}' does not exist.")
        raise FileNotFoundError(f'File not found: {file_path}')

    aws_config = get_aws_config()

    s3_key = f'{s3_folder}/{os.path.basename(file_path)}'
    logger.info(
        f"Preparing to upload file to s3://{aws_config['aws_bucket_name']}/{s3_key}"
    )

    try:
        session = boto3.session.Session(
            aws_access_key_id=aws_config['aws_access_key'],
            aws_secret_access_key=aws_config['aws_secret_key'],
            region_name=aws_config['aws_region'],
        )
        s3_client = session.client('s3')

        s3_client.upload_file(file_path, aws_config['aws_bucket_name'], s3_key)
        logger.info(
            f"Uploaded '{file_path}' to s3://{aws_config['aws_bucket_name']}/{s3_key}"
        )

    except (BotoCoreError, ClientError) as e:
        logger.error(f'Failed to upload file to S3: {e}')
        raise


"""
Sample running function

test_file_path = "wallace.log"
s3_folder = "workspace/commercial-analytics/pygalp-data-process/logs"
upload_file_to_s3(test_file_path, s3_folder)
"""
