import shutil
import signal
import struct
import platform
import tempfile
from threading import RLock
from dataclasses import dataclass
import time
from py4j.java_gateway import (
    CallbackServerParameters,
    GatewayParameters,
    JavaGateway,
    java_import,
    logger as py4jlogger,
)
from typing import Optional, Any
from subprocess import PIPE, Popen
import os
import logging
import getpass
from pyflink.java_gateway import Watchdog, PythonFunctionFactory
from pyflink.util.exceptions import install_exception_handler, install_py4j_hooks
from pathlib import Path
import yaml as pyyaml
from typing import Self

import socket

KEY_ENV_LOG_DIR = "env.log.dir"
KEY_ENV_YARN_CONF_DIR = "env.yarn.conf.dir"
KEY_ENV_HADOOP_CONF_DIR = "env.hadoop.conf.dir"
KEY_ENV_HBASE_CONF_DIR = "env.hbase.conf.dir"
KEY_ENV_JAVA_HOME = "env.java.home"
KEY_ENV_JAVA_OPTS = "env.java.opts.all"
KEY_ENV_JAVA_OPTS_DEPRECATED = "env.java.opts"
KEY_ENV_JAVA_DEFAULT_OPTS = "env.java.default-opts.all"

logger = logging.getLogger(__name__)


@dataclass
class FlinkDirectories:
    home: Path
    conf: Path
    lib: Path
    opt: Path
    plugins: Path
    bin: Path

    @staticmethod
    def build_flink_dirs(home: Path, default_lib: Optional[Path] = None) -> Self:
        """
        Builds the flink directories to use from a common home, with an optional
        override for libraries.
        """
        return FlinkDirectories(
            home=home,
            conf=os.environ.get("FLINK_CONF_DIR", home / "conf"),
            lib=os.environ.get("FLINK_LIB_DIR", default_lib or home / "lib"),
            opt=os.environ.get("FLINK_OPT_DIR", home / "opt"),
            plugins=os.environ.get("FLINK_PLUGINS_DIR", home / "plugins"),
            bin=os.environ.get("FLINK_BIN_DIR", home / "bin"),
        )


class NoFlinkLibraryJarsException(Exception):
    pass


class JavaGatewayException(Exception):
    pass


class JavaGatewayManager:
    """Manages the Java gateway connection and process.

    This class handles the lifecycle of a Py4J gateway that allows Python code
    to interact with the Flink Java runtime. It manages launching the Java
    gateway server process, establishing the connection, and cleaning up resources.

    Functions that need access to the gateway should call get_gateway().
    """

    def __init__(self, flink_directories: FlinkDirectories, classes_to_load: set[str]):
        self.java_gateway: Optional[JavaGateway] = None
        self.python_gateway_process: Optional[Popen] = None
        self.lock = RLock()
        self.flink_directories = flink_directories
        self.classes_to_load = classes_to_load
        self.config = self._load_and_flatten_config(flink_directories)

    def _load_and_flatten_config(self, flink_directories: FlinkDirectories) -> dict[str, Any]:
        """Load and flatten the Flink configuration file once at initialization."""
        config_file = flink_directories.conf / "config.yaml"

        def flatten_config(config, parent_key=""):
            items = []
            sep = "."
            for k, v in config.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_config(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        if config_file.is_file():
            try:
                with open(config_file.resolve(), "r") as f:
                    config = pyyaml.safe_load(f)
                    return flatten_config(config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
                return {}
        return {}

    def get_gateway(self) -> JavaGateway:
        """Get the Java gateway, creating it if it doesn't exist.

        This method is thread-safe and will only create one gateway instance.
        If a gateway port is specified via PYFLINK_GATEWAY_PORT environment
        variable, it will connect to an existing gateway. Otherwise, it will
        launch a new gateway server process.
        """
        with self.lock:
            if self.java_gateway is None:
                py4jlogger.level = logging.WARN
                if "PYFLINK_GATEWAY_PORT" in os.environ:
                    gateway_port = int(os.environ["PYFLINK_GATEWAY_PORT"])
                    logger.debug(f"Connecting to existing PyFlink gateway on port {gateway_port}")
                    gateway_param = GatewayParameters(port=gateway_port, auto_convert=True)
                    self.java_gateway = JavaGateway(
                        gateway_parameters=gateway_param,
                        callback_server_parameters=CallbackServerParameters(
                            port=0, daemonize=True, daemonize_connections=True
                        ),
                    )
                else:
                    logger.debug("Launching new PyFlink gateway")
                    self.java_gateway = self._launch_gateway()

                callback_server = self.java_gateway.get_callback_server()
                callback_server_listening_address = callback_server.get_listening_address()
                callback_server_listening_port = callback_server.get_listening_port()
                self.java_gateway.jvm.org.apache.flink.client.python.PythonEnvUtils.resetCallbackClient(
                    self.java_gateway.java_gateway_server,
                    callback_server_listening_address,
                    callback_server_listening_port,
                )

                self.import_flink_classes()
                install_exception_handler()
                install_py4j_hooks()

                self.java_gateway.entry_point.put("PythonFunctionFactory", PythonFunctionFactory())
                self.java_gateway.entry_point.put("Watchdog", Watchdog())
        return self.java_gateway

    def import_flink_classes(self) -> None:
        """Import specified Java classes into the gateway JVM."""
        for class_name in self.classes_to_load:
            java_import(self.java_gateway.jvm, class_name)

    def find_java_executable(self) -> str:
        """Find the Java executable to use for launching the gateway.

        Searches for Java in the following order:
        1. KEY_ENV_JAVA_HOME from the Flink configuration file
        2. JAVA_HOME environment variable
        3. System PATH (default java/java.exe)
        """
        java_executable = "java.exe" if self._on_windows() else "java"
        java_home = self.config.get(KEY_ENV_JAVA_HOME)

        if java_home is None and "JAVA_HOME" in os.environ:
            java_home = Path(os.environ["JAVA_HOME"])
        elif java_home is not None:
            java_home = Path(java_home)

        if java_home is not None:
            java_executable = java_home / "bin" / java_executable

        return str(java_executable)

    @staticmethod
    def _on_windows() -> bool:
        """Check if running on Windows platform."""
        return platform.system() == "Windows"

    @classmethod
    def _construct_flink_classpath(cls, flink_directories: FlinkDirectories) -> str:
        """Construct the classpath for Flink JAR files.

        Builds a classpath string containing all Flink library JARs and
        the Python integration JAR if available.
        """
        if cls._on_windows():
            # The command length is limited on Windows. To avoid the problem we should shorten the
            # command length as much as possible.
            lib_jars = str(flink_directories.lib / "*")
        else:
            lib_jar_paths = flink_directories.lib.glob("*.jar")
            lib_jars = os.pathsep.join(str(jar) for jar in lib_jar_paths)

        flink_python_jars = list(flink_directories.opt.glob("flink-python*.jar"))

        if not lib_jars:
            raise NoFlinkLibraryJarsException(
                f"Unable to find any Flink library jars in {flink_directories.lib}. "
                "Please verify the path to the Flink library directory or specify it via the "
                "FLINK_LIB_DIR environment variable."
            )
        else:
            if not flink_python_jars:
                return lib_jars
            else:
                return os.pathsep.join([lib_jars, str(flink_python_jars[0])])

    def _construct_log_settings(self) -> list[str]:
        """Construct JVM logging configuration arguments.

        Creates JVM arguments for configuring Log4j and Logback logging
        frameworks.
        """
        flink_home = self.flink_directories.home.resolve()
        flink_conf_dir = self.flink_directories.conf

        flink_log_dir = os.getenv(
            "FLINK_LOG_DIR",
            self.config.get(KEY_ENV_LOG_DIR, str(flink_home / "log")),
        )

        log4j_properties = os.getenv(
            "LOG4J_PROPERTIES", str(flink_conf_dir / "log4j-cli.properties")
        )

        logback_xml = os.getenv("LOGBACK_XML", str(flink_conf_dir / "logback.xml"))

        flink_ident_string = os.getenv("FLINK_IDENT_STRING", getpass.getuser())

        hostname = socket.gethostname()

        return [
            f"-Dlog.file=${flink_log_dir}/flink-${flink_ident_string}-python-${hostname}.log",
            f"-Dlog4j.configuration=${log4j_properties}",
            f"-Dlog4j.configurationFile=${log4j_properties}",
            f"-Dlogback.configurationFile=${logback_xml}",
        ]

    def _construct_jvm_opts(self) -> list[str]:
        """Construct JVM options from environment and configuration.

        Reads JVM options from FLINK_ENV_JAVA_OPTS environment variable
        or from Flink configuration files.
        """
        jvm_opts = os.environ.get("FLINK_ENV_JAVA_OPTS")
        if jvm_opts is None:
            default_jvm_opts = self.config.get(KEY_ENV_JAVA_DEFAULT_OPTS, "")
            extra_jvm_opts = self.config.get(
                KEY_ENV_JAVA_OPTS,
                self.config.get(KEY_ENV_JAVA_OPTS_DEPRECATED, ""),
            )
            jvm_opts = f"{default_jvm_opts} {extra_jvm_opts}"

        # Remove leading and trailing double quotes (if present) of value
        jvm_opts = jvm_opts.strip('"')
        return jvm_opts.split()

    def _construct_hadoop_classpath(self) -> str:
        """Construct classpath for Hadoop and HBase integration.

        Builds a classpath containing Hadoop, YARN, and HBase configuration
        directories. Falls back to common default locations if environment
        variables are not set.
        """
        env = os.environ
        hadoop_conf_dir = ""
        if "HADOOP_CONF_DIR" not in env and "HADOOP_CLASSPATH" not in env:
            hadoop_conf_path = Path("/etc/hadoop/conf")
            if hadoop_conf_path.is_dir():
                print(
                    "Setting HADOOP_CONF_DIR=/etc/hadoop/conf because no HADOOP_CONF_DIR or"
                    "HADOOP_CLASSPATH was set."
                )
                hadoop_conf_dir = hadoop_conf_path

        hbase_conf_dir = ""
        if "HBASE_CONF_DIR" not in env:
            hbase_conf_path = Path("/etc/hbase/conf")
            if hbase_conf_path.is_dir():
                print("Setting HBASE_CONF_DIR=/etc/hbase/conf because no HBASE_CONF_DIR was set.")
                hbase_conf_dir = hbase_conf_path

        return os.pathsep.join(
            [
                env.get("HADOOP_CLASSPATH", ""),
                env.get(
                    "YARN_CONF_DIR",
                    self.config.get(KEY_ENV_YARN_CONF_DIR, ""),
                ),
                env.get(
                    "HADOOP_CONF_DIR",
                    self.config.get(KEY_ENV_HADOOP_CONF_DIR, hadoop_conf_dir),
                ),
                env.get(
                    "HBASE_CONF_DIR",
                    self.config.get(KEY_ENV_HBASE_CONF_DIR, hbase_conf_dir),
                ),
            ]
        )

    def _launch_gateway(self) -> JavaGateway:
        """Launch a new Java gateway server and connect to it.

        Creates a temporary directory for connection information exchange,
        launches the Java gateway server process, waits for it to write
        its port number, then establishes a connection.
        """
        # Create a temporary directory where the gateway server should write the connection
        # information.
        conn_info_dir = tempfile.mkdtemp()
        try:
            fd, conn_info_file = tempfile.mkstemp(dir=conn_info_dir)
            os.close(fd)
            os.unlink(conn_info_file)

            self.python_gateway_process = self._launch_gateway_server_process(
                "org.apache.flink.client.python.PythonGatewayServer", conn_info_file
            )

            while not self.python_gateway_process.poll() and not os.path.isfile(conn_info_file):
                time.sleep(0.1)

            if not os.path.isfile(conn_info_file):
                stderr_info = self.python_gateway_process.stderr.read().decode("utf-8")
                raise JavaGatewayException(
                    "Java gateway process exited before sending its port number.\n"
                    f"Stderr:\n{stderr_info}"
                )

            with open(conn_info_file, "rb") as info:
                gateway_port = struct.unpack("!I", info.read(4))[0]
        finally:
            shutil.rmtree(conn_info_dir)

        # Connect to the gateway
        logger.debug(f"Connecting to PyFlink gateway on port {gateway_port}")
        return JavaGateway(
            gateway_parameters=GatewayParameters(port=gateway_port, auto_convert=True),
            callback_server_parameters=CallbackServerParameters(
                port=0, daemonize=True, daemonize_connections=True
            ),
        )

    def _launch_gateway_server_process(self, main_class: str, temp_path: str) -> Popen:
        """Launch the Java gateway server process.

        Constructs the complete Java command with classpath, JVM options,
        and logging configuration, then starts and returns the process.
        """
        java_executable = self.find_java_executable()
        log_settings = self._construct_log_settings()
        jvm_args = os.environ.get("JVM_ARGS", "").split()
        jvm_opts = self._construct_jvm_opts()
        classpath = os.pathsep.join(
            [
                self._construct_flink_classpath(self.flink_directories),
                self._construct_hadoop_classpath(),
            ]
        )

        command = [
            java_executable,
            *jvm_args,
            "-XX:+IgnoreUnrecognizedVMOptions",
            "--add-opens=jdk.proxy2/jdk.proxy2=ALL-UNNAMED",
            *jvm_opts,
            *log_settings,
            "-cp",
            classpath,
            main_class,
        ]
        preexec_fn = None
        if not self._on_windows():

            def preexec_func():
                # ignore ctrl-c / SIGINT
                signal.signal(signal.SIGINT, signal.SIG_IGN)

            preexec_fn = preexec_func

        env = dict(os.environ)
        env["_PYFLINK_CONN_INFO_PATH"] = temp_path

        logger.debug(f"Launching Java gateway server process with command: {' '.join(command)}")
        logger.debug(f"Using connection info path: {temp_path}")

        return Popen(
            [c for c in command if c],
            stdin=PIPE,
            stderr=PIPE,
            preexec_fn=preexec_fn,
            env=env,
        )

    def close_gateway(self) -> None:
        """Close the Java gateway and terminate the server process.

        Performs cleanup by shutting down the gateway connection and
        terminating the Java server process if they exist.
        """
        if self.java_gateway is not None:
            self.java_gateway.shutdown()
            self.java_gateway = None
        if self.python_gateway_process is not None:
            self.python_gateway_process.terminate()
            self.python_gateway_process = None
