import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'src')
    ),
)

from dotenv import load_dotenv

from logger.logger_config import setup_logger

logger = setup_logger()
load_dotenv()

from plugins.s3 import S3

# Instance with credentials from env
s3_client = S3()


def upload_parquet_to_s3(df, filename: str, s3_path: str):
    try:
        s3_client.upload_df_s3(
            df, filename=filename, file_format='parquet', s3_path=s3_path
        )
        logger.info(
            f'Parquet file uploaded successfully to S3: {s3_path}/{filename}'
        )
    except Exception as e:
        logger.error(f'Error uploading Parquet file to S3: {e}')


def upload_excel_to_s3(df, filename: str, s3_path: str):
    try:
        s3_client.upload_df_s3(
            df, filename=filename, file_format='excel', s3_path=s3_path
        )
        logger.info(
            f'Excel file uploaded successfully to S3: {s3_path}/{filename}'
        )
    except Exception as e:
        logger.error(f'Error uploading Excel file to S3: {e}')


def upload_csv_to_s3(df, filename: str, s3_path: str):
    try:
        s3_client.upload_df_s3(
            df, filename=filename, file_format='csv', s3_path=s3_path
        )
        logger.info(
            f'CSV file uploaded successfully to S3: {s3_path}/{filename}'
        )
    except Exception as e:
        logger.error(f'Error uploading CSV file to S3: {e}')
