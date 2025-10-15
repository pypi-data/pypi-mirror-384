import os
import sys

import duckdb
import pytest

from configs.env_loader import get_dremio_config
from functions.dremio_client import Client


@pytest.fixture(scope='module')
def dremio_client():
    config = get_dremio_config()
    return Client(**config)


@pytest.fixture(scope='module')
def dremio_table(dremio_client):
    try:
        df = dremio_client.query(
            """
            SELECT * FROM wuwks."commercial-analytics"."commercial-analytics"."internal_projects"."example_files"."developers_processed.csv"
        """
        )
        conn = duckdb.connect()
        conn.register('dremio_data', df)
        conn.execute('CREATE TABLE dremio_table AS SELECT * FROM dremio_data')
        return conn
    except Exception as e:
        pytest.fail(f'Failed to prepare DuckDB table from Dremio: {str(e)}')


def test_table_has_5_columns(dremio_table):
    try:
        result = dremio_table.execute(
            'SELECT * FROM dremio_table LIMIT 1'
        ).fetchdf()
        assert (
            result.shape[1] == 5
        ), f'Expected 5 columns, but got {result.shape[1]}'
    except Exception as e:
        pytest.fail(f'Failed to validate column count: {str(e)}')


def test_table_has_required_columns(dremio_table):
    required_columns = ['name', 'role', 'email', 'last_processed_row_date']

    try:
        columns = (
            dremio_table.execute("PRAGMA table_info('dremio_table')")
            .fetchdf()['name']
            .tolist()
        )

        for col in required_columns:
            assert col in columns, f'Column {col} is missing'
    except Exception as e:
        pytest.fail(f'Failed to check required columns: {str(e)}')


def test_table_is_not_empty(dremio_table):
    try:
        result = dremio_table.execute(
            'SELECT COUNT(*) AS row_count FROM dremio_table'
        ).fetchdf()
        row_count = result['row_count'][0]
        assert row_count > 0, 'Table is empty'
    except Exception as e:
        pytest.fail(f'Failed to verify that the table is not empty: {str(e)}')
