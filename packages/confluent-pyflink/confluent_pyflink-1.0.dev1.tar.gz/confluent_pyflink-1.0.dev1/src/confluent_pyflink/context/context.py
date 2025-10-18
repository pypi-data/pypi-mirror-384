from abc import ABC, abstractmethod
from typing import Optional
import os
from pathlib import Path
import logging
from py4j.java_gateway import JavaGateway
import pyflink
from contextvars import ContextVar

from .java_gateway_manager import JavaGatewayManager, FlinkDirectories

CURRENT_CONTEXT: ContextVar[Optional["Context"]] = ContextVar("CURRENT_CONTEXT", default=None)
logger = logging.getLogger(__name__)


def get_gateway_of_current_context():
    """
    Get the Java gateway of the current context.

    Returns the Java gateway from the current active context. If no context is set,
    creates a ConfluentContext as the default for backward compatibility.
    """
    context = CURRENT_CONTEXT.get()
    if context is None:
        # Inline import to avoid circular import.
        from .confluent_context import ConfluentContext

        context = ConfluentContext()
    return context.get_gateway()


class InvalidFlinkHomeException(Exception):
    pass


class Context(ABC):
    """
    Abstract base class for Confluent PyFlink execution contexts.
    """

    def __init__(self):
        self._manager = JavaGatewayManager(self._get_flink_directories(), self._classes_to_load())
        self._parent_context = None
        context = CURRENT_CONTEXT.get()
        if context is not None:
            self._parent_context = context
        CURRENT_CONTEXT.set(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._manager.close_gateway()
        CURRENT_CONTEXT.set(self._parent_context)

    def get_gateway(self) -> JavaGateway:
        """
        Get the Java gateway for this context.
        """
        return self._manager.get_gateway()

    @staticmethod
    def _is_flink_home(path: Path) -> bool:
        """
        Check if the given path is a valid Flink home directory.
        """
        flink_script_file = path / "bin" / "flink"
        return flink_script_file.exists()

    @classmethod
    def _find_flink_home(cls) -> Path:
        """
        Find and return the Flink home directory.

        Searches for Flink home in the following order:
        1. FLINK_HOME environment variable
        3. PyFlink module path
        """
        # If the environment has set FLINK_HOME, trust it.
        if "FLINK_HOME" in os.environ:
            return Path(os.environ["FLINK_HOME"])
        else:
            try:
                FLINK_HOME = None
                for module_home in pyflink.__path__:
                    module_path = Path(module_home)
                    if cls._is_flink_home(module_path):
                        FLINK_HOME = module_path

                if FLINK_HOME is not None:
                    return FLINK_HOME
                else:
                    raise InvalidFlinkHomeException(
                        "Could not find valid FLINK_HOME (Flink distribution directory) "
                        "in current environment."
                    )
            except Exception as exception:
                raise InvalidFlinkHomeException(
                    "Unable to find FLINK_HOME (Flink distribution directory) due to:"
                ) from exception

    @abstractmethod
    def _get_flink_directories(self) -> FlinkDirectories:
        """
        Get the Flink directories configuration for this context.

        Abstract method that must be implemented by subclasses to specify
        the Flink directory structure to use.
        """
        pass

    @abstractmethod
    def _classes_to_load(self) -> set[str]:
        """
        Get the set of Java classes to load for this context.

        Abstract method that must be implemented by subclasses to specify
        which Java classes should be loaded into the gateway.
        """
        pass
