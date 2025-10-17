from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from semantic_model_generator.relationships.discovery import (
    discover_relationships_from_schema,
)


class _FakeResult:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def to_pandas(self) -> pd.DataFrame:
        return self._df.copy()


class _FakeSession:
    def __init__(self, tables: List[str], columns_df: pd.DataFrame):
        self.tables = tables
        self.columns_df = columns_df

    def sql(self, query: str):
        normalized = query.upper()
        if "SHOW CATALOGS" in normalized:
            return _FakeResult(
                pd.DataFrame(
                    {
                        "CATALOG_NAME": ["CLICKZETTA_SAMPLE_DATA"],
                        "CATEGORY": ["MANAGED"],
                    }
                )
            )
        if "FROM INFORMATION_SCHEMA.TABLES" in normalized:
            data = {"TABLE_SCHEMA": ["TPCH_100G"] * len(self.tables), "TABLE_NAME": self.tables}
            return _FakeResult(pd.DataFrame(data))
        if "FROM INFORMATION_SCHEMA.COLUMNS" in normalized:
            return _FakeResult(self.columns_df)
        if "SELECT DISTINCT" in normalized:
            # Return single column of sample values
            return _FakeResult(pd.DataFrame({"VALUE": [1, 2, 3]}))
        raise AssertionError(f"Unexpected query: {query}")


def _build_columns_df() -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    # Orders table
    records.extend(
        [
            {
                "TABLE_SCHEMA": "TPCH_100G",
                "TABLE_NAME": "ORDERS",
                "COLUMN_NAME": "ORDER_ID",
                "DATA_TYPE": "NUMBER",
                "IS_PRIMARY_KEY": True,
            },
            {
                "TABLE_SCHEMA": "TPCH_100G",
                "TABLE_NAME": "ORDERS",
                "COLUMN_NAME": "CUSTOMER_ID",
                "DATA_TYPE": "NUMBER",
                "IS_PRIMARY_KEY": False,
            },
        ]
    )
    # Customer table
    records.extend(
        [
            {
                "TABLE_SCHEMA": "TPCH_100G",
                "TABLE_NAME": "CUSTOMER",
                "COLUMN_NAME": "CUSTOMER_ID",
                "DATA_TYPE": "NUMBER",
                "IS_PRIMARY_KEY": True,
            },
            {
                "TABLE_SCHEMA": "TPCH_100G",
                "TABLE_NAME": "CUSTOMER",
                "COLUMN_NAME": "NAME",
                "DATA_TYPE": "STRING",
                "IS_PRIMARY_KEY": False,
            },
        ]
    )
    return pd.DataFrame.from_records(records)


def test_discover_relationships_from_schema_builds_relationships():
    tables = ["ORDERS", "CUSTOMER"]
    columns_df = _build_columns_df()
    session = _FakeSession(tables, columns_df)

    result = discover_relationships_from_schema(
        session=session,
        workspace="CLICKZETTA_SAMPLE_DATA",
        schema="TPCH_100G",
        strict_join_inference=False,
    )

    assert result.summary.total_tables == 2
    assert result.summary.total_relationships_found >= 1

    names = {rel.name for rel in result.relationships}
    assert any("ORDERS" in name and "CUSTOMER" in name for name in names)

    left_tables = {rel.left_table for rel in result.relationships}
    right_tables = {rel.right_table for rel in result.relationships}
    assert "ORDERS" in left_tables
    assert "CUSTOMER" in right_tables
