# Copyright 2024 Confluent Inc.

from __future__ import annotations

import datetime
import logging
from uuid import UUID
import json
import yaml
from importlib.metadata import version, PackageNotFoundError
from pydantic import Field, ValidationError, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union, Literal
from os import PathLike

from py4j.compat import long
from pyflink.java_gateway import get_gateway
from pyflink.util.java_utils import create_url_class_loader
from pyflink.table.environment_settings import EnvironmentSettings

__all__ = ["ConfluentSettings"]

_log = logging.getLogger(__name__)


def _default_http_user_agent() -> str:
    package_name = "confluent-flink-table-api-python-plugin"
    try:
        package_version = version(package_name)
    except PackageNotFoundError:
        _log.debug("Using default values as could not find package information: ", exc_info=True)
        package_version = "unknown"

    # Construct default User-Agent
    user_agent_value = f"{package_name}/{package_version}"
    _log.debug(f"Using default User-Agent: {user_agent_value}")
    return user_agent_value


class ConfluentSettingsValidationError(Exception):
    pass


class ConfluentSettings(BaseSettings):
    """
    Entrypoint for Confluent-specific settings. Settings are validated via Pydantic.

    Pass these settings into a :class:`~pyflink.table.TableEnvironment` via
    :func:`~pyflink.table.TableEnvironment.create` for talking to Confluent Cloud.
    """

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError as e:
            self._raise_friendly_error(e)

    def _raise_friendly_error(self, validation_error: ValidationError):
        missing_fields = []
        invalid_fields = []

        for error in validation_error.errors():
            field_name = ".".join(error.get("loc", ("unknown")))
            error_type = error.get("type")

            if error_type == "missing":
                missing_fields.append(field_name)
            else:
                invalid_fields.append(f"{field_name}: {error.get('msg')}")

        error_parts = []

        error_parts.append(
            f"{validation_error.error_count()} validation errors for ConfluentSettings"
        )

        if missing_fields:
            error_parts.append(
                f"Missing the following required configuration keys: {', '.join(missing_fields)}"
            )
            error_parts.append(
                "Please ensure all required Confluent Cloud settings are provided either as "
                "environment variables with a CONFLUENT_ prefix (e.g., CONFLUENT_ORG_ID) or as "
                "parameters passed directly to ConfluentSettings\n"
            )

        if invalid_fields:
            error_parts.append("The following configuration is invalid:")
            for field in invalid_fields:
                error_parts.append(f"  {field}")

        raise ConfluentSettingsValidationError("\n".join(error_parts)) from None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CONFLUENT_",
    )

    context: Optional[str] = Field(
        default=None, description="A name for this Table API session.", examples=["my_table_program"]
    )
    org_id: UUID = Field(
        description="ID of the organization.",
        examples=["b0b21724-4586-4a07-b787-d0bb5aacbf87"],
    )
    env_id: str = Field(description="ID of the environment.", examples=["env-z32x1"])
    flink_api_key: str = Field(description="API key for Flink access.")
    flink_api_secret: SecretStr = Field(description="API secret for Flink access.")

    artifact_api_key: Optional[str] = Field(default=None, description="")
    artifact_api_secret: Optional[SecretStr] = Field(default=None, description="")

    compute_pool_id: str = Field(description="ID of the compute pool. For example: lfcp-8m03rm.")
    principal_id: Optional[str] = Field(
        default=None,
        description="Principal that runs submitted statements. For example: `sa-23kgz4`",
    )

    cloud_provider: Literal["aws", "gcp", "azure"] = Field(
        description="Confluent identifier for a cloud provider.",
        examples=["aws", "gcp", "azure"],
    )
    cloud_region: str = Field(
        description="Confluent identifier for a cloud provider's region.", examples=["us-east-1"]
    )

    rest_endpoint: Optional[str] = Field(
        default=None, description="URL to the REST endpoint.", examples=["proxyto.confluent.cloud"]
    )

    artifact_endpoint_template: str = Field(
        default="https://api.confluent.cloud",
        description="A template for the endpoint URL.",
        examples=["https://flinkpls-dom123.{region}.{cloud}.confluent.cloud"],
    )
    endpoint_template: str = Field(
        default="https://flink.{region}.{cloud}.confluent.cloud",
        description="A template for the endpoint URL.",
        examples=["https://flinkpls-dom123.{region}.{cloud}.confluent.cloud"],
    )

    catalog_cache: datetime.timedelta = Field(
        default=datetime.timedelta(minutes=1),
        description="Expiration time for catalog objects. 0 disables the caching.",
    )

    @field_validator("catalog_cache", mode="after")
    @classmethod
    def _is_non_negative_timedelta(cls, value: datetime.timedelta) -> datetime.timedelta:
        if value < datetime.timedelta(0):
            msg = f"{value} is a negative timedelta"
            raise ValueError(msg)
        else:
            return value

    http_user_agent: str = Field(
        default_factory=_default_http_user_agent,
        description="Custom HTTP User-Agent header for API requests.",
    )

    @classmethod
    def from_file(cls, path: Union[str, PathLike], **overrides) -> ConfluentSettings:
        """
        Create an instance of ConfluentSettings from a given json or yaml file.

        Also accepts arbitrary key overrides, for example:

        .. code-block:: python

            ConfluentSettings.from_file(
                "my_configuration.json",
                cloud_provider="aws",
                cloud_region="us-east-1"
            )
        """

        with open(path, "r") as file:
            if path.endswith(".json"):
                file_data = json.load(file)
            elif path.endswith((".yml", ".yaml")):
                file_data = yaml.safe_load(file)
            else:
                msg = "Unsupported file format, only .json and .yaml are supported"
                raise ValueError(msg)

        file_data.update(overrides)
        return cls(**file_data)

    def _to_environment_settings(self) -> EnvironmentSettings:
        """
        Translates the Confluent Settings to a :class:`~pyflink.table.EnvironmentSettings` for use
        when creating the table environment.
        """
        gateway = get_gateway()

        j_duration_class = gateway.jvm.java.time.Duration
        j_catalog_cache_duration = j_duration_class.ofMillis(
            long(round(self.catalog_cache.total_seconds() * 1000))
        )

        j_builder = gateway.jvm.ConfluentSettings.newBuilder()

        # First, set all non-optional parameters
        j_builder.setOrganizationId(str(self.org_id))
        j_builder.setEnvironmentId(self.env_id)
        j_builder.setFlinkApiKey(self.flink_api_key)
        j_builder.setFlinkApiSecret(self.flink_api_secret.get_secret_value())
        j_builder.setHTTPUserAgent(self.http_user_agent)
        j_builder.setComputePoolId(self.compute_pool_id)
        j_builder.setCloud(self.cloud_provider)
        j_builder.setRegion(self.cloud_region)
        j_builder.setEndpointTemplate(self.endpoint_template)
        j_builder.setArtifactEndpointTemplate(self.artifact_endpoint_template)
        j_builder.setCatalogCache(j_catalog_cache_duration)
        if self.context is not None:
            j_builder.setContextName(self.context)
        if self.artifact_api_key is not None:
            j_builder.setArtifactApiKey(self.artifact_api_key)
        if self.artifact_api_secret is not None:
            j_builder.setArtifactApiSecret(self.artifact_api_secret.get_secret_value())
        if self.principal_id is not None:
            j_builder.setPrincipalId(self.principal_id)
        if self.rest_endpoint is not None:
            j_builder.setRestEndpoint(self.rest_endpoint)

        context_classloader = gateway.jvm.Thread.currentThread().getContextClassLoader()
        new_classloader = create_url_class_loader([], context_classloader)
        gateway.jvm.Thread.currentThread().setContextClassLoader(new_classloader)
        return EnvironmentSettings(j_environment_settings=j_builder.build())
