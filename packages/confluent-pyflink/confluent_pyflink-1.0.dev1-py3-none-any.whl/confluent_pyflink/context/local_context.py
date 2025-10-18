from .context import Context, FlinkDirectories
import logging

logger = logging.getLogger(__name__)


class LocalContext(Context):
    """
    An implementation of the Context class for local Flink clusters.
    Loads classes/jars from the Open Source Flink distribution, and executes on a local cluster.

    Use it as a context manager::

    with LocalContext():
        settings = EnvironmentSettings.in_streaming_mode()
        env = TableEnvironment.create(settings)
        env.from_elements([row("Hello world!")]).execute().print()
    """

    def _get_flink_directories(self) -> FlinkDirectories:
        flink_home = self._find_flink_home()
        flink_dirs = FlinkDirectories.build_flink_dirs(home=flink_home)
        logger.debug(f"Using the following Flink directories:\n{flink_dirs}")
        return flink_dirs

    def _classes_to_load(self) -> set[str]:
        return {
            "org.apache.flink.table.api.*",
            "org.apache.flink.table.legacy.api.*",
            "org.apache.flink.table.api.config.*",
            "org.apache.flink.table.api.java.*",
            "org.apache.flink.table.api.bridge.java.*",
            "org.apache.flink.table.api.dataview.*",
            "org.apache.flink.table.catalog.*",
            "org.apache.flink.table.descriptors.*",
            "org.apache.flink.table.legacy.descriptors.*",
            "org.apache.flink.table.descriptors.python.*",
            "org.apache.flink.table.expressions.*",
            "org.apache.flink.table.sources.*",
            "org.apache.flink.table.legacy.sources.*",
            "org.apache.flink.table.sinks.*",
            "org.apache.flink.table.legacy.sinks.*",
            "org.apache.flink.table.types.*",
            "org.apache.flink.table.types.logical.*",
            "org.apache.flink.table.util.python.*",
            "org.apache.flink.api.common.python.*",
            "org.apache.flink.api.common.typeinfo.TypeInformation",
            "org.apache.flink.api.common.typeinfo.Types",
            "org.apache.flink.api.java.ExecutionEnvironment",
            "org.apache.flink.streaming.api.environment.StreamExecutionEnvironment",
            "org.apache.flink.python.util.PythonDependencyUtils",
            "org.apache.flink.python.PythonOptions",
            "org.apache.flink.client.python.PythonGatewayServer",
            "org.apache.flink.streaming.api.functions.python.*",
            "org.apache.flink.streaming.api.operators.python.process.*",
            "org.apache.flink.streaming.api.operators.python.embedded.*",
            "org.apache.flink.streaming.api.typeinfo.python.*",
        }
