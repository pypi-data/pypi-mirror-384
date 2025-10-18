# Copyright 2024 Confluent Inc.
# ruff: noqa: E402

from __future__ import absolute_import

import pyflink.java_gateway
from ..context.context import get_gateway_of_current_context

pyflink.java_gateway.get_gateway = get_gateway_of_current_context

from confluent_pyflink.table.changelog_mode import ChangelogMode
from confluent_pyflink.table.data_view import DataView, ListView, MapView
from confluent_pyflink.table.environment_settings import EnvironmentSettings
from confluent_pyflink.table.explain_detail import ExplainDetail
from confluent_pyflink.table.expression import Expression
from confluent_pyflink.table.module import Module, ModuleEntry
from confluent_pyflink.table.result_kind import ResultKind
from confluent_pyflink.table.schema import Schema
from confluent_pyflink.table.sql_dialect import SqlDialect
from confluent_pyflink.table.statement_set import StatementSet
from confluent_pyflink.table.table import (
    GroupWindowedTable,
    GroupedTable,
    OverWindowedTable,
    Table,
    WindowGroupedTable,
)
from confluent_pyflink.table.table_config import TableConfig
from confluent_pyflink.table.table_descriptor import TableDescriptor, FormatDescriptor
from confluent_pyflink.table.table_environment import TableEnvironment
from confluent_pyflink.table.table_result import TableResult
from confluent_pyflink.table.table_schema import TableSchema
from confluent_pyflink.table.types import DataTypes, UserDefinedType, Row, RowKind
from confluent_pyflink.table.udf import (
    FunctionContext,
    ScalarFunction,
    TableFunction,
    AggregateFunction,
    TableAggregateFunction,
)

__all__ = [
    "TableEnvironment",
    "Table",
    "StatementSet",
    "EnvironmentSettings",
    "TableConfig",
    "GroupedTable",
    "GroupWindowedTable",
    "OverWindowedTable",
    "WindowGroupedTable",
    "ScalarFunction",
    "TableFunction",
    "AggregateFunction",
    "TableAggregateFunction",
    "FunctionContext",
    "DataView",
    "ListView",
    "MapView",
    "TableDescriptor",
    "FormatDescriptor",
    "Schema",
    "Module",
    "ModuleEntry",
    "SqlDialect",
    "DataTypes",
    "UserDefinedType",
    "Expression",
    "TableSchema",
    "TableResult",
    "Row",
    "RowKind",
    "ChangelogMode",
    "ExplainDetail",
    "ResultKind",
]
