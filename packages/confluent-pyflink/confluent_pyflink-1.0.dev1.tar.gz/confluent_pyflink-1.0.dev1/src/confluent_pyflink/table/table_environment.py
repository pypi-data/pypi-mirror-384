from pyflink.serializers import PickleSerializer

from typing import Union, List, Iterable

from pyflink.table.table_environment import TableEnvironment as FlinkTableEnvironment
from pyflink.common.configuration import Configuration
from pyflink.java_gateway import get_gateway
from pyflink.table.types import (
    _create_type_verifier,
    _infer_schema_from_data,
    _create_converter,
    _to_java_data_type,
)
from pyflink.table.utils import to_expression_jarray

from confluent_pyflink.table import Table, Expression, EnvironmentSettings
from confluent_pyflink.table.types import RowType, DataType
from confluent_pyflink.table.utils.confluent_settings import ConfluentSettings
from confluent_pyflink.context.context import CURRENT_CONTEXT
from confluent_pyflink.context.confluent_context import ConfluentContext


__all__ = ["TableEnvironment"]


class TableEnvironment(FlinkTableEnvironment):
    def __init__(self, j_tenv, serializer=PickleSerializer()):
        self._j_tenv = j_tenv
        self._serializer = serializer
        self._config_chaining_optimization()
        self._open()

    @staticmethod
    def create(
        environment_settings: Union[ConfluentSettings, EnvironmentSettings, Configuration],
    ) -> "TableEnvironment":
        """
        Creates a table environment that is the entry point and central context for creating Table
        and SQL API programs.

        :param environment_settings: The configuration or environment settings used to instantiate
            the :class:`~pyflink.table.TableEnvironment`, the name is for backward compatibility.
        :return: The :class:`~pyflink.table.TableEnvironment`.
        """
        gateway = get_gateway()
        current_context = CURRENT_CONTEXT.get()

        if isinstance(current_context, ConfluentContext):
            # When in ConfluentContext, only ConfluentSettings are allowed
            if not isinstance(environment_settings, ConfluentSettings):
                raise TypeError(
                    "When using ConfluentContext, environment_settings must be ConfluentSettings, "
                    f"but got: {type(environment_settings).__name__}"
                )
            else:
                _environment_settings = environment_settings._to_environment_settings()
        else:
            if isinstance(environment_settings, ConfluentSettings):
                # If ConfluentSettings are used outside of ConfluentContext,
                # we default to default streaming mode settings.
                _environment_settings = EnvironmentSettings.in_streaming_mode()
            elif isinstance(environment_settings, Configuration):
                _environment_settings = (
                    EnvironmentSettings.new_instance()
                    .with_configuration(environment_settings)
                    .build()
                )
            elif isinstance(environment_settings, EnvironmentSettings):
                _environment_settings = environment_settings
            else:
                raise TypeError(
                    "environment_settings must be an instance of ConfluentSettings, "
                    "Configuration, or EnvironmentSettings, but got: "
                    f"{type(environment_settings).__name__}"
                )

        j_tenv = gateway.jvm.TableEnvironment.create(_environment_settings._j_environment_settings)
        return TableEnvironment(j_tenv)

    def from_elements(
        self,
        elements: Iterable,
        schema: Union[DataType, List[str]] = None,
        verify_schema: bool = True,
    ) -> Table:
        """
        Creates a table from a collection of elements.
        The elements types must be acceptable atomic types or acceptable composite types.
        All elements must be of the same type.
        If the elements types are composite types, the composite types must be strictly equal,
        and its subtypes must also be acceptable types.
        e.g. if the elements are tuples, the length of the tuples must be equal, the element types
        of the tuples must be equal in order.

        The built-in acceptable atomic element types contains:

        **int**, **long**, **str**, **unicode**, **bool**,
        **float**, **bytearray**, **datetime.date**, **datetime.time**, **datetime.datetime**,
        **datetime.timedelta**, **decimal.Decimal**

        The built-in acceptable composite element types contains:

        **list**, **tuple**, **dict**, **array**, :class:`~pyflink.table.Row`

        If the element type is a composite type, it will be unboxed.
        e.g. table_env.from_elements([(1, 'Hi'), (2, 'Hello')]) will return a table like:

        +----+-------+
        | _1 |  _2   |
        +====+=======+
        | 1  |  Hi   |
        +----+-------+
        | 2  | Hello |
        +----+-------+

        "_1" and "_2" are generated field names.

        Example:
        ::

            # use the second parameter to specify custom field names
            >>> table_env.from_elements([(1, 'Hi'), (2, 'Hello')], ['a', 'b'])
            # use the second parameter to specify custom table schema
            >>> table_env.from_elements([(1, 'Hi'), (2, 'Hello')],
            ...                         DataTypes.ROW([DataTypes.FIELD("a", DataTypes.INT()),
            ...                                        DataTypes.FIELD("b", DataTypes.STRING())]))
            # use the third parameter to switch whether to verify the elements against the schema
            >>> table_env.from_elements([(1, 'Hi'), (2, 'Hello')],
            ...                         DataTypes.ROW([DataTypes.FIELD("a", DataTypes.INT()),
            ...                                        DataTypes.FIELD("b", DataTypes.STRING())]),
            ...                         False)
            # create Table from expressions
            >>> table_env.from_elements([row(1, 'abc', 2.0), row(2, 'def', 3.0)],
            ...                         DataTypes.ROW([DataTypes.FIELD("a", DataTypes.INT()),
            ...                                        DataTypes.FIELD("b", DataTypes.STRING()),
            ...                                        DataTypes.FIELD("c", DataTypes.FLOAT())]))

        :param elements: The elements to create a table from.
        :param schema: The schema of the table.
        :param verify_schema: Whether to verify the elements against the schema.
        :return: The result table.
        """

        # verifies the elements against the specified schema
        if isinstance(schema, RowType):
            verify_func = _create_type_verifier(schema) if verify_schema else lambda _: True

            def verify_obj(obj):
                verify_func(obj)
                return obj

        elif isinstance(schema, DataType):
            data_type = schema
            schema = RowType().add("value", schema)

            verify_func = (
                _create_type_verifier(data_type, name="field value")
                if verify_schema
                else lambda _: True
            )

            def verify_obj(obj):
                verify_func(obj)
                return obj

        else:

            def verify_obj(obj):
                return obj

        elements = list(elements)

        # in case all the elements are expressions
        if len(elements) > 0 and all(isinstance(elem, Expression) for elem in elements):
            if schema is None:
                return Table(self._j_tenv.fromValues(to_expression_jarray(elements)), self)
            else:
                return Table(
                    self._j_tenv.fromValues(
                        _to_java_data_type(schema), to_expression_jarray(elements)
                    ),
                    self,
                )
        elif any(isinstance(elem, Expression) for elem in elements):
            raise ValueError(
                "It doesn't support part of the elements are Expression, while the others are not."
            )

        # Confluent: this has been moved to allow usage of row Expressions without inferring the type
        # infers the schema if not specified
        if schema is None or isinstance(schema, (list, tuple)):
            schema = _infer_schema_from_data(elements, names=schema)
            converter = _create_converter(schema)
            elements = map(converter, elements)

        elif not isinstance(schema, RowType):
            raise TypeError("schema should be RowType, list, tuple or None, but got: %s" % schema)

        # verifies the elements against the specified schema
        elements = map(verify_obj, elements)
        # converts python data to sql data
        elements = [schema.to_sql_type(element) for element in elements]
        return self._from_elements(elements, schema)

    def _set_python_executable_for_local_executor(self):
        # Confluent modification - we want this function to be no-op.
        # In PyFlink it starts up a UDF side-car, which uses an internal
        # Environment, which isn't available to us.
        pass

    def _open(self):
        # Confluent modification - we want this function to be no-op.
        # In PyFlink it starts up a UDF side-car, which uses an internal
        # Environment, which isn't available to us.
        pass
