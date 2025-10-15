import os

from dotenv import load_dotenv

load_dotenv()


def get_dremio_config():
    config = {
        'host': os.getenv('DREMIO_HOST'),
        'port': os.getenv('DREMIO_PORT'),
        'username': os.getenv('DREMIO_USERNAME'),
        'password': os.getenv('DREMIO_ACCESS_TOKEN'),
    }
    return config


def get_aws_config():
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    aws_bucket_name = os.getenv('S3_BUCKET_NAME')
    s3_path_file_tariff = os.getenv('S3_PATH_FILE_TARIFF')
    example_file_path = os.getenv('EXAMPLE_FILE_PATH')

    return {
        'aws_access_key': aws_access_key,
        'aws_secret_key': aws_secret_key,
        'aws_region': aws_region,
        'aws_bucket_name': aws_bucket_name,
        'example_file_path': example_file_path,
    }


def get_teams_config():
    return {'teams_webhook_url': os.getenv('TEAMS_WEBHOOK_URL')}
