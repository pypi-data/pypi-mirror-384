import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
    ),
)

from functions.dremio_client import dremio_client
from logger.logger_config import setup_logger

logger = setup_logger()


def export_parquet_local(conn, table_name, local_parquet_file):
    """Exports a DuckDB table to a local Parquet file."""
    if conn is None or table_name is None:
        logger.error('Invalid connection or table name. Export aborted.')
        return None

    try:
        conn.execute(
            f"COPY {table_name} TO '{local_parquet_file}' (FORMAT 'parquet')"
        )
        logger.info(f'Parquet file saved locally: {local_parquet_file}')
        return local_parquet_file
    except Exception as e:
        logger.error(f'Error exporting to local Parquet: {e}')
        return None
    finally:
        conn.close()
        logger.info('Connection closed.')
