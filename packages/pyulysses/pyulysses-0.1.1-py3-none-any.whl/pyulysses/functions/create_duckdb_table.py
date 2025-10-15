import os
import sys

import duckdb

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
    ),
)
from logger.logger_config import setup_logger

logger = setup_logger()


def create_duckdb_table(df, table_name='dremio_table'):
    """Creates a DuckDB table from the DataFrame using the provided table name."""
    try:
        conn = duckdb.connect()
        logger.info('Connected to DuckDB.')
    except Exception as e:
        logger.error(f'Error connecting to DuckDB: {e}')
        return None, None

    try:
        conn.register('dremio_data', df)
        conn.execute(f'CREATE TABLE {table_name} AS SELECT * FROM dremio_data')
        logger.info(f"Table '{table_name}' created in DuckDB.")
        return conn, table_name
    except Exception as e:
        logger.error(f'Error creating table in DuckDB: {e}')
        conn.close()
        return None, None
