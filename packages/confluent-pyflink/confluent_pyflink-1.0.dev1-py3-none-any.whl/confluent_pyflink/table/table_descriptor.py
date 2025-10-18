# Copyright 2024 Confluent Inc.

from pyflink.table import TableDescriptor as PyFlinkTableDescriptor, FormatDescriptor
from pyflink.java_gateway import get_gateway
from pyflink.util.java_utils import to_jarray

__all__ = ["TableDescriptor"]


class TableDescriptor(PyFlinkTableDescriptor):
    # A :class:`~pyflink.table.TableDescriptor` for creating tables located in
    # Confluent Cloud programmatically.
    #
    # Compared to :class:`~pyflink.table.TableDescriptor`, this class adds
    # support for Confluent's system columns and convenience methods for working
    # with Confluent tables.

    def __init__(self, j_table_descriptor):
        self._j_table_descriptor = j_table_descriptor
        super(TableDescriptor, self).__init__(self._j_table_descriptor)

    @staticmethod
    def for_managed() -> "TableDescriptor.Builder":
        # Creates a :class:`~pyflink.table.TableDescriptor` for a Confluent-managed
        # table.
        #
        # The descriptor is pre-configured with "'connector' = 'confluent'".
        # Use the returned :class:`~pyflink.table.confluent.ConfluentTableDescriptor.Builder`
        # to further customize the table.

        gateway = get_gateway()
        j_builder = gateway.jvm.ConfluentTableDescriptor.forManaged()
        return TableDescriptor.Builder(j_builder)

    @staticmethod
    def for_connector(connector_identifier: str) -> "TableDescriptor.Builder":
        # Creates a :class:`~pyflink.table.TableDescriptor` for a table in Confluent Cloud.
        #
        # The descriptor is pre-configured with given "'connector'".
        # Use the returned :class:`~pyflink.table.confluent.ConfluentTableDescriptor.Builder`
        # to further customize the table.

        gateway = get_gateway()
        j_builder = gateway.jvm.ConfluentTableDescriptor.forConnector(connector_identifier)
        return TableDescriptor.Builder(j_builder)

    def to_builder(self):
        return TableDescriptor.Builder(self._j_table_descriptor.toBuilder())

    class Builder(PyFlinkTableDescriptor.Builder):
        """
        Builder for :class:`~pyflink.table.confluent.ConfluentTableDescriptor`.
        """

        def __init__(self, j_builder):
            self._j_builder = j_builder
            super(TableDescriptor.Builder, self).__init__(self._j_builder)

        def key_format(self, format_descriptor: FormatDescriptor) -> "TableDescriptor.Builder":
            """
      Defines the key format for Kafka-based tables.

      Options of the provided formatDescriptor are automatically prefixed.

      Example:
      ::
        >>> descriptor_builder.key_format( \
              FormatDescriptor.for_format("json") \
                .option("validate-writes", "true") \
                .build() \
            )

      will result in the options

      'key.format' = 'json'
      'key.json.validate-writes' = 'true'

      Options that affect which columns belong to the format, can be set with
      :func:`~pyflink.table.confluent.ConfluentTableDescriptor.option`
      Example:
      ::

        >>> table_descriptor.option("key.fields-prefix", "k_")
      """
            _j_builder = self._j_builder.keyFormat(format_descriptor._j_format_descriptor)
            return TableDescriptor.Builder(_j_builder)

        def value_format(self, format_descriptor: FormatDescriptor) -> "TableDescriptor.Builder":
            """
      Defines the value format for Kafka-based tables.

      Options of the provided formatDescriptor are automatically prefixed.

      Example:
      ::
        >>> descriptor_builder.value_format( \
              FormatDescriptor.for_format("json") \
                .option("validate-writes", "true") \
                .build() \
            )

      will result in the options

      'value.format' = 'json'
      'value.json.validate-writes' = 'true'

      Options that affect which columns belong to the format, can be set with
      :func:`~pyflink.table.confluent.ConfluentTableDescriptor.option`
      Example:
      ::

        >>> table_descriptor.option("value.fields-include", "all")
      """
            _j_builder = self._j_builder.valueFormat(format_descriptor._j_format_descriptor)
            return TableDescriptor.Builder(_j_builder)

        def distributed_by_hash(self, *bucket_keys: str) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into buckets using a hash algorithm over the
            given columns. The number of buckets is connector-defined.
            """
            gateway = get_gateway()
            j_array = to_jarray(gateway.jvm.java.lang.String, bucket_keys)
            j_builder = self._j_builder.distributedByHash(j_array)
            return TableDescriptor.Builder(j_builder)

        def distributed_by_hash_into_buckets(
            self, number_of_buckets: int, *bucket_keys: str
        ) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into the given number of buckets using a
            hash algorithm over the given columns.
            """
            gateway = get_gateway()
            j_array = to_jarray(gateway.jvm.java.lang.String, bucket_keys)
            j_builder = self._j_builder.distributedByHash(number_of_buckets, j_array)
            return TableDescriptor.Builder(j_builder)

        def distributed_by_range(self, *bucket_keys: str) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into buckets using a range algorithm over
            the given columns. The number of buckets is connector-defined.
            """
            gateway = get_gateway()
            j_array = to_jarray(gateway.jvm.java.lang.String, bucket_keys)
            j_builder = self._j_builder.distributedByRange(j_array)
            return TableDescriptor.Builder(j_builder)

        def distributed_by_range_into_buckets(
            self, number_of_buckets: int, *bucket_keys: str
        ) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into the given number of buckets using a
            range algorithm over the given columns.
            """
            gateway = get_gateway()
            j_array = to_jarray(gateway.jvm.java.lang.String, bucket_keys)
            j_builder = self._j_builder.distributedByRange(number_of_buckets, j_array)
            return TableDescriptor.Builder(j_builder)

        def distributed_by(self, *bucket_keys: str) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into buckets over the given columns. The
            number of buckets and used algorithm are connector-defined.
            """
            gateway = get_gateway()
            j_array = to_jarray(gateway.jvm.java.lang.String, bucket_keys)
            j_builder = self._j_builder.distributedBy(j_array)
            return TableDescriptor.Builder(j_builder)

        def distributed_by_into_buckets(
            self, number_of_buckets: int, *bucket_keys: str
        ) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into the given number of buckets by the
            given columns. The used algorithm is connector-defined.
            """
            gateway = get_gateway()
            j_array = to_jarray(gateway.jvm.java.lang.String, bucket_keys)
            j_builder = self._j_builder.distributedBy(number_of_buckets, j_array)
            return TableDescriptor.Builder(j_builder)

        def distributed_into(self, number_of_buckets: int) -> "TableDescriptor.Builder":
            """
            Defines that the table should be distributed into the given number of buckets. The
            algorithm is connector-defined.
            """
            j_builder = self._j_builder.distributedInto(number_of_buckets)
            return TableDescriptor.Builder(j_builder)

        def build(self) -> "TableDescriptor":
            return TableDescriptor(self._j_builder.build())
