from .context import Context, FlinkDirectories, InvalidFlinkHomeException
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfluentContext(Context):
    """
    An implementation of the Context class for Confluent PyFlink applications.
    Loads classes and jars from the Confluent Flink distribution, for use with Confluent Cloud.

    Use it as a context manager::

        with ConfluentContext():
            settings = ConfluentSettings(...)
            env = TableEnvironment.create(settings)
            env.from_elements([row("Hello world!")]).execute().print()
    """

    def _find_confluent_flink_home(self) -> Path:
        """
        Find and return the Confluent Flink home directory.

        Searches for Confluent Flink home in the following order:
        1. CONFLUENT_FLINK_HOME environment variable
        2. PyFlink module path
        """
        # If the environment has set CONFLUENT_FLINK_HOME, trust it.
        if "CONFLUENT_FLINK_HOME" in os.environ:
            return Path(os.environ["CONFLUENT_FLINK_HOME"])
        else:
            try:
                CONFLUENT_FLINK_HOME = None
                for module_home in __import__("confluent_pyflink").__path__:
                    CONFLUENT_FLINK_HOME = module_home
                if CONFLUENT_FLINK_HOME is not None:
                    return Path(CONFLUENT_FLINK_HOME)
                else:
                    raise InvalidFlinkHomeException(
                        "Could not find valid CONFLUENT_FLINK_HOME (Flink distribution directory) "
                        "in current environment."
                    )
            except Exception as exception:
                raise InvalidFlinkHomeException(
                    "Unable to find CONFLUENT_FLINK_HOME (Flink distribution directory) due to:"
                ) from exception

    def _get_flink_directories(self) -> FlinkDirectories:
        flink_home = self._find_flink_home()
        confluent_flink_home = self._find_confluent_flink_home()
        flink_dirs = FlinkDirectories.build_flink_dirs(
            home=flink_home, default_lib=confluent_flink_home / "lib"
        )
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
            "io.confluent.flink.plugin.*",
        }
