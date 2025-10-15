import os
import sys

from tables import queries

from configs.env_loader import get_dremio_config
from functions.dremio_client import Client
from logger.logger_config import setup_logger

logger = setup_logger()


def get_dremio_client():
    config = get_dremio_config()
    return Client(**config)


def run_refresh_metadata(client, query_key):
    query = queries.get(query_key)
    if not query:
        logger.error(
            f"Query key '{query_key}' not found in queries dictionary."
        )
        raise ValueError(
            f"Query key '{query_key}' not found in queries dictionary."
        )
    try:
        df = client.query(query)
        logger.info(f"Query '{query_key}' executed successfully.")
        logger.info(df)
        return df
    except Exception as e:
        logger.exception(f"Failed to execute query '{query_key}': {e}")
        raise


if __name__ == '__main__':
    client = get_dremio_client()
    for key in queries:
        try:
            run_refresh_metadata(client, key)
        except Exception as e:
            logger.error(f"Error while refreshing metadata for '{key}': {e}")
