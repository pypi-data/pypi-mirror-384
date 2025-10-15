import os
import sys

import pytest

from configs.env_loader import get_dremio_config
from functions.dremio_client import Client


@pytest.fixture(scope='module')
def dremio_client():
    config = get_dremio_config()
    return Client(**config)


QUERY_SOURCE = """
SELECT * FROM wuwks."commercial-analytics"."commercial-analytics"."internal_projects"."example_files"."developers.csv"
"""

QUERY_TARGET = """
SELECT * FROM wuwks."commercial-analytics"."commercial-analytics"."internal_projects"."example_files"."developers_processed.csv"
"""


@pytest.fixture(scope='module')
def dfs(dremio_client):
    df_source = dremio_client.query(QUERY_SOURCE)
    df_target = dremio_client.query(QUERY_TARGET)
    return df_source, df_target


def test_name_count_equal(dfs):
    df_source, df_target = dfs
    source_count = df_source['name'].nunique()
    target_count = df_target['name'].nunique()
    assert (
        source_count == target_count
    ), f'Different STATION_ID count: source={source_count}, target={target_count}'
