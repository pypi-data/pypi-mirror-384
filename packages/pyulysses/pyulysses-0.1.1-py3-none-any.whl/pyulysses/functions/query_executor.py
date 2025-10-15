import os
import sys

import pandas as pd
from pyarrow import flight

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
    ),
)

from logger.logger_config import setup_logger

logger = setup_logger()


def execute(client, headers, query: str) -> pd.DataFrame:
    flight_desc = flight.FlightDescriptor.for_command(query)
    options = flight.FlightCallOptions(headers=headers)

    flight_info = client.get_flight_info(flight_desc, options)
    reader = client.do_get(flight_info.endpoints[0].ticket, options)

    return reader.read_pandas()


def execute_query_in_dremio(dremio_client, query):
    """Executes the query and returns a DataFrame."""
    try:
        df = dremio_client.query(query)
        logger.info('Query executed successfully.')
        return df
    except Exception as e:
        logger.error(f'Error executing query: {e}')
        return None
