# Copyright 2024 Confluent Inc.

from pyflink.common.types import Row, RowKind
from pyflink.java_gateway import get_gateway
from pyflink.table.table import Table
from pyflink.table.table_result import TableResult
from pyflink.table.utils import pickled_bytes_to_python_converter
from typing import List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pyflink.table.table_environment import TableEnvironment


__all__ = ["ConfluentTools"]


class ConfluentTools(object):
    """
    Various tools that help developing and testing
    Table API programs on Confluent Cloud.
    """

    @staticmethod
    def collect_changelog(table: Table) -> List[Row]:
        """
        Executes the given table transformations on Confluent Cloud and returns the results locally
        as a list of changelog rows.

        Note: The method assumes that all input tables are finite. If the pipeline is potentially
        unbounded, use :func:`pyflink.table.confluent.ConfluentTools.collect_changelog_limit` for
        stop fetching after the desired amount of rows has been reached.
        """
        return ConfluentTools.collect_changelog_limit(table, -1)

    @staticmethod
    def collect_changelog_limit(table: Union[Table, TableResult], stop_after: int) -> List[Row]:
        """
        Executes the given table transformations on Confluent Cloud and returns the results locally
        as a list of changelog rows.

        Note: The method can work on both finite and infinite input tables. If the pipeline is
        potentially unbounded, it will stop fetching after the desired amount of rows has been
        reached.
        """
        gateway = get_gateway()
        if isinstance(table, Table):
            table_schema = table.get_schema()
            j_object = table._j_table
        else:
            table_schema = table.get_table_schema()
            j_object = table._j_table_result

        j_results = gateway.jvm.ConfluentTools.collectChangelog(j_object, stop_after)
        return _to_python_row_list(j_results, table_schema)

    @staticmethod
    def collect_materialized(table: Union[Table, TableResult]) -> List[Row]:
        """
        Executes the given table transformations on Confluent Cloud and returns the results locally
        as a materialized changelog. In other words: Changes are applied to an in-memory table and
        returned as a list of insert-only rows.

        Note: The method assumes that all input tables are finite. If the pipeline is potentially
        unbounded, use :func:`pyflink.table.confluent.ConfluentTools.collect_materialized_limit`
        for stop fetching after the desired amount of rows has been reached.
        """
        return ConfluentTools.collect_materialized_limit(table, -1)

    @staticmethod
    def collect_materialized_limit(table: Union[Table, TableResult], stop_after: int) -> List[Row]:
        """
        Executes the given table transformations on Confluent Cloud and returns the results locally
        as a materialized changelog. In other words: Changes are applied to an in-memory table and
        returned as a list of insert-only rows.

        Note: The method can work on both finite and infinite input tables. If the pipeline is
        potentially unbounded, it will stop fetching after the desired amount of rows has been
        reached.
        """
        gateway = get_gateway()
        if isinstance(table, Table):
            table_schema = table.get_schema()
            j_object = table._j_table
        else:
            table_schema = table.get_table_schema()
            j_object = table._j_table_result

        j_results = gateway.jvm.ConfluentTools.collectMaterialized(j_object, stop_after)
        return _to_python_row_list(j_results, table_schema)

    @staticmethod
    def print_changelog(table: Union[Table, TableResult]) -> None:
        """
        Executes the given table transformations on Confluent Cloud and prints the results locally as
        a table prefixed with a change flag column.

        Note: The method assumes that all input tables are finite. If the pipeline is potentially
        unbounded, use :func:`pyflink.table.confluent.ConfluentTools.print_changelog_limit`
        for stop fetching after the desired amount of rows has been reached.
        """
        ConfluentTools.print_changelog_limit(table, -1)

    @staticmethod
    def print_changelog_limit(table: Union[Table, TableResult], stop_after: int) -> None:
        """
        Executes the given table transformations on Confluent Cloud and prints the results locally as
        a table prefixed with a change flag column.

        Note: The method can work on both finite and infinite input tables. If the pipeline is
        potentially unbounded, it will stop fetching after the desired amount of rows has been
        reached.
        """
        gateway = get_gateway()
        if isinstance(table, Table):
            j_object = table._j_table
        else:
            j_object = table._j_table_result
        gateway.jvm.ConfluentTools.printChangelog(j_object, stop_after)

    @staticmethod
    def print_materialized(table: Union[Table, TableResult]) -> None:
        """
        Executes the given table transformations on Confluent Cloud and prints the results locally as
        a materialized changelog. In other words: Changes are applied to an in-memory table and
        printed.

        Note: The method assumes that all input tables are finite. If the pipeline is potentially
        unbounded, use :func:`pyflink.table.confluent.ConfluentTools.print_materialized_limit`
        for stop fetching after the desired amount of rows has been reached.
        """
        ConfluentTools.print_materialized_limit(table, -1)

    @staticmethod
    def print_materialized_limit(table: Union[Table, TableResult], stop_after: int) -> None:
        """
        Executes the given table transformations on Confluent Cloud and prints the results locally as
        a materialized changelog. In other words: Changes are applied to an in-memory table and
        printed.

        Note: The method can work on both finite and infinite input tables. If the pipeline is
        potentially unbounded, it will stop fetching after the desired amount of rows has been
        reached.
        """
        gateway = get_gateway()
        if isinstance(table, Table):
            j_object = table._j_table
        else:
            j_object = table._j_table_result
        gateway.jvm.ConfluentTools.printMaterialized(j_object, stop_after)

    @staticmethod
    def get_statement_name(table_result: TableResult) -> str:
        """
        Returns the statement name behind the given table result.
        """
        gateway = get_gateway()
        j_table_result = table_result._j_table_result
        return gateway.jvm.ConfluentTools.getStatementName(j_table_result)

    @staticmethod
    def stop_statement(table_result: TableResult) -> None:
        """
        Stops the statement behind the given table result.
        """
        gateway = get_gateway()
        j_table_result = table_result._j_table_result
        gateway.jvm.ConfluentTools.stopStatement(j_table_result)

    @staticmethod
    def stop_statement_by_name(env: "TableEnvironment", statement_name: str) -> None:
        """
        Stops the statement behind the given statement name.
        """
        gateway = get_gateway()
        j_env = env._j_tenv
        gateway.jvm.ConfluentTools.stopStatement(j_env, statement_name)

    @staticmethod
    def delete_statement(env: "TableEnvironment", statement_name: str) -> None:
        """
        Deletes the statement behind the given statement name.
        """
        gateway = get_gateway()
        gateway.jvm.ConfluentTools.deleteStatement(env._j_tenv, statement_name)


def _to_python_row_list(_j_list_row, table_schema) -> List[Row]:
    return [_to_python_row(r, table_schema) for r in _j_list_row]


def _to_python_row(_j_row, table_schema) -> Row:
    gateway = get_gateway()
    _j_field_data_types = table_schema._j_table_schema.getFieldDataTypes()
    pickle_bytes = gateway.jvm.PythonBridgeUtils.getPickledBytesFromRow(_j_row, _j_field_data_types)
    row_kind = RowKind(int.from_bytes(pickle_bytes[0], byteorder="big", signed=False))
    pickle_bytes = list(pickle_bytes[1:])
    field_data = zip(pickle_bytes, table_schema.get_field_data_types())
    fields = []
    for data, field_type in field_data:
        if len(data) == 0:
            fields.append(None)
        else:
            fields.append(pickled_bytes_to_python_converter(data, field_type))
    result_row = Row(*fields)
    result_row.set_row_kind(row_kind)
    return result_row
