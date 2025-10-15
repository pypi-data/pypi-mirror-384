import logging
import os
from datetime import datetime

import duckdb
from dotenv import load_dotenv

load_dotenv()

aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_bucket_name = os.getenv('S3_BUCKET_NAME')
aws_region = os.getenv('AWS_REGION')
file_path = os.getenv('FILE_PATH_SAMPLE_FILE')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Start DuckDB connection
con = duckdb.connect()

# Install and load HTTPFS for S3 access
con.execute(
    """
    INSTALL httpfs;
    LOAD httpfs;
    """
)

con.execute(f"SET s3_region='{aws_region}'")
con.execute(f"SET s3_access_key_id='{aws_access_key}'")
con.execute(f"SET s3_secret_access_key='{aws_secret_key}'")

s3_path = f's3://{aws_bucket_name}/{file_path}'

try:
    query = f"""
        SELECT
            *
        FROM
            read_csv('{s3_path}', DELIM=';', HEADER=TRUE)
    """
    df = con.execute(query).fetchdf()
    logging.info('File read successfully from S3.')
    logging.info('Number of rows read: %d', len(df))

    # Add metadata column with current timestamp
    current_timestamp = datetime.utcnow().isoformat()
    df['last_processed_row_date'] = current_timestamp
    df['is_processed'] = 'yes'

    output_file_path = file_path.replace('.csv', '_processed.csv')
    s3_output_path = f's3://{aws_bucket_name}/{output_file_path}'

    # Write the modified DataFrame back to S3
    con.register('result', df)
    con.execute(
        f"""
        COPY result TO '{s3_output_path}'
        (FORMAT CSV, HEADER TRUE, DELIMITER ';')
        """
    )
    logging.info(
        'File with metadata written successfully to %s',
        s3_output_path,
    )

except Exception as e:
    logging.error('Error processing file: %s', e)
