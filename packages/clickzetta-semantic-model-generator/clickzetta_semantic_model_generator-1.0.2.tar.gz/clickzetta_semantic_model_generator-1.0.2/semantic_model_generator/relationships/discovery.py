from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
from loguru import logger

from semantic_model_generator.clickzetta_utils.clickzetta_connector import (
    _TABLE_NAME_COL,
    _TABLE_SCHEMA_COL,
    get_table_representation,
    get_valid_schemas_tables_columns_df,
)
from semantic_model_generator.data_processing import data_types
from semantic_model_generator.data_processing.data_types import FQNParts, Table
from semantic_model_generator.generate_model import (
    _DEFAULT_N_SAMPLE_VALUES_PER_COL,
    _infer_relationships,
)
from semantic_model_generator.protos import semantic_model_pb2

try:  # pragma: no cover - optional dependency for type checking
    from clickzetta.zettapark.session import Session
except Exception:  # pragma: no cover
    Session = Any  # type: ignore

DEFAULT_MAX_WORKERS = 4


@dataclass
class RelationshipSummary:
    total_tables: int
    total_columns: int
    total_relationships_found: int
    processing_time_ms: int


@dataclass
class RelationshipDiscoveryResult:
    relationships: List[semantic_model_pb2.Relationship]
    tables: List[Table]
    summary: RelationshipSummary


def _normalize_table_names(table_names: Optional[Iterable[str]]) -> Optional[List[str]]:
    if table_names is None:
        return None
    return [name.upper() for name in table_names]


def _build_tables_from_dataframe(
    session: Session,
    workspace: str,
    schema: str,
    columns_df: pd.DataFrame,
    sample_values_per_column: int,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> List[Tuple[FQNParts, Table]]:
    if columns_df.empty:
        return []

    if _TABLE_NAME_COL not in columns_df.columns:
        raise KeyError(
            f"Expected '{_TABLE_NAME_COL}' column in metadata dataframe. "
            "Ensure information_schema query returned table names."
        )

    table_order = (
        columns_df[_TABLE_NAME_COL]
        .astype(str)
        .str.upper()
        .drop_duplicates()
        .tolist()
    )

    tables: List[Tuple[FQNParts, Table]] = []
    for idx, table_name in enumerate(table_order):
        table_columns_df = columns_df[columns_df[_TABLE_NAME_COL] == table_name]
        if table_columns_df.empty:
            continue

        max_workers_for_table = min(max_workers, len(table_columns_df.index) or 1)
        table_proto = get_table_representation(
            session=session,
            workspace=workspace,
            schema_name=schema,
            table_name=table_name,
            table_index=idx,
            ndv_per_column=sample_values_per_column,
            columns_df=table_columns_df,
            max_workers=max_workers_for_table,
        )
        tables.append(
            (
                FQNParts(database=workspace, schema_name=schema, table=table_name),
                table_proto,
            )
        )

    return tables


def _discover_relationships(
    raw_tables: List[Tuple[FQNParts, Table]],
    strict_join_inference: bool,
    session: Optional[Session],
) -> List[semantic_model_pb2.Relationship]:
    if not raw_tables:
        return []

    relationships = _infer_relationships(
        raw_tables,
        session=session if strict_join_inference else None,
        strict_join_inference=strict_join_inference,
    )
    return relationships


def discover_relationships_from_tables(
    tables: Sequence[Tuple[FQNParts, Table]],
    *,
    strict_join_inference: bool = False,
    session: Optional[Session] = None,
) -> RelationshipDiscoveryResult:
    """
    Run relationship inference using pre-constructed table metadata.
    """
    start = time.perf_counter()
    relationships = _discover_relationships(
        list(tables),
        strict_join_inference=strict_join_inference,
        session=session,
    )
    end = time.perf_counter()

    all_columns = sum(len(table.columns) for _, table in tables)
    summary = RelationshipSummary(
        total_tables=len(tables),
        total_columns=all_columns,
        total_relationships_found=len(relationships),
        processing_time_ms=int((end - start) * 1000),
    )

    return RelationshipDiscoveryResult(
        relationships=relationships,
        tables=[table for _, table in tables],
        summary=summary,
    )


def discover_relationships_from_schema(
    session: Session,
    workspace: str,
    schema: str,
    *,
    table_names: Optional[Sequence[str]] = None,
    sample_values_per_column: int = _DEFAULT_N_SAMPLE_VALUES_PER_COL,
    strict_join_inference: bool = False,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> RelationshipDiscoveryResult:
    """
    Discover table relationships for all tables in a ClickZetta schema.
    """
    normalized_tables = _normalize_table_names(table_names)

    metadata_df = get_valid_schemas_tables_columns_df(
        session=session,
        workspace=workspace,
        table_schema=schema,
        table_names=normalized_tables,
    )
    metadata_df.columns = [str(col).upper() for col in metadata_df.columns]

    if metadata_df.empty:
        logger.warning(
            "No column metadata found for workspace=%s schema=%s tables=%s",
            workspace,
            schema,
            table_names,
        )
        return RelationshipDiscoveryResult(
            relationships=[],
            tables=[],
            summary=RelationshipSummary(
                total_tables=0,
                total_columns=0,
                total_relationships_found=0,
                processing_time_ms=0,
            ),
        )

    raw_tables = _build_tables_from_dataframe(
        session=session,
        workspace=workspace,
        schema=schema,
        columns_df=metadata_df,
        sample_values_per_column=sample_values_per_column,
        max_workers=max_workers,
    )

    return discover_relationships_from_tables(
        raw_tables,
        strict_join_inference=strict_join_inference,
        session=session,
    )
