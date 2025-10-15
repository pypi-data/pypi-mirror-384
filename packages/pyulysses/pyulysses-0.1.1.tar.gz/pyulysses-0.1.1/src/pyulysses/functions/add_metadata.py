import os
import sys
from datetime import datetime

from logger.logger_config import setup_logger

logger = setup_logger()


def add_metadata_last_processed_data(df):
    """Adds a UTC timestamp column to the DataFrame."""

    df['last_processed_row_date'] = datetime.utcnow().strftime(
        '%Y-%m-%d %H:%M:%S'
    )
    logger.info('last_processed_row_date column added.')
    return df
