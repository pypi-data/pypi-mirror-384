import io
import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
    ),
)

import boto3
import pandas as pd

from configs.env_loader import get_aws_config
from logger.logger_config import setup_logger

aws_config = get_aws_config()
logger = setup_logger()


class S3:
    def __init__(self) -> None:
        self.client = boto3.client(
            's3',
            aws_access_key_id=aws_config['aws_access_key'],
            aws_secret_access_key=aws_config['aws_secret_key'],
        )
        self.bucket = aws_config['aws_bucket_name']

    def upload_df_s3(
        self,
        df: pd.DataFrame,
        filename: str,
        file_format: str,
        s3_path: str,
        **kwargs: dict,
    ) -> None:
        """
        Converts the supplied DataFrame to a file and uploads it to S3.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to upload.
        filename : str
            Name of the file to store in S3 (e.g. 'data.parquet').
        file_format : str
            Format of the file: 'parquet', 'excel', or 'csv'.
        s3_path : str
            Path inside the S3 bucket (e.g. 'folder/subfolder').
        """

        file_key = f'{s3_path}/{filename}'

        try:
            handler = io.BytesIO()
            if file_format == 'parquet':
                df.to_parquet(handler, compression='snappy', index=False)
            elif file_format == 'excel':
                df.to_excel(handler, index=False, **kwargs)
            elif file_format == 'csv':
                df.to_csv(handler, index=False, **kwargs)
            else:
                logger.error(f"File format '{file_format}' not recognized")
                return

            self.client.put_object(
                Bucket=self.bucket, Key=file_key, Body=handler.getvalue()
            )
            logger.info(f'Uploaded file to s3://{self.bucket}/{file_key}')

        except Exception as e:
            logger.error(
                f'Failed to upload to s3://{self.bucket}/{file_key}: {e}'
            )
            raise
