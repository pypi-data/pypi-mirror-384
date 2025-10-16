from typing import override

from sqlalchemy import URL
from sqlalchemy.exc import SQLAlchemyError

from archipy.adapters.base.sqlalchemy.session_managers import (
    AsyncBaseSQLAlchemySessionManager,
    BaseSQLAlchemySessionManager,
)
from archipy.configs.base_config import BaseConfig
from archipy.configs.config_template import StarRocksSQLAlchemyConfig
from archipy.helpers.metaclasses.singleton import Singleton
from archipy.models.errors import DatabaseConnectionError


class StarRocksSQlAlchemySessionManager(BaseSQLAlchemySessionManager[StarRocksSQLAlchemyConfig], metaclass=Singleton):
    """Synchronous SQLAlchemy session manager for StarRocks.

    Inherits from BaseSQLAlchemySessionManager to provide StarRocks-specific session
    management, including connection URL creation and engine configuration.

    Args:
        orm_config: StarRocks-specific configuration. If None, uses global config.
    """

    def __init__(self, orm_config: StarRocksSQLAlchemyConfig | None = None) -> None:
        """Initialize the StarRocks session manager.

        Args:
            orm_config: StarRocks-specific configuration. If None, uses global config.
        """
        configs = BaseConfig.global_config().STARROCKS_SQLALCHEMY if orm_config is None else orm_config
        super().__init__(configs)

    @override
    def _expected_config_type(self) -> type[StarRocksSQLAlchemyConfig]:
        """Return the expected configuration type for StarRocks.

        Returns:
            The StarRocksSQLAlchemyConfig class.
        """
        return StarRocksSQLAlchemyConfig

    @override
    def _get_database_name(self) -> str:
        """Return the name of the database being used.

        Returns:
            str: The name of the database ('starrocks').
        """
        return "starrocks"

    @override
    def _create_url(self, configs: StarRocksSQLAlchemyConfig) -> URL:
        """Create a StarRocks connection URL.

        Args:
            configs: StarRocks configuration.

        Returns:
            A SQLAlchemy URL object for StarRocks.

        Raises:
            DatabaseConnectionError: If there's an error creating the URL.
        """
        try:
            return URL.create(
                drivername=configs.DRIVER_NAME,
                username=configs.USERNAME,
                password=configs.PASSWORD,
                host=configs.HOST,
                port=configs.PORT,
                database=configs.DATABASE,
            )
        except SQLAlchemyError as e:
            raise DatabaseConnectionError(
                database=self._get_database_name(),
            ) from e


class AsyncStarRocksSQlAlchemySessionManager(
    AsyncBaseSQLAlchemySessionManager[StarRocksSQLAlchemyConfig],
    metaclass=Singleton,
):
    """Asynchronous SQLAlchemy session manager for StarRocks.

    Inherits from AsyncBaseSQLAlchemySessionManager to provide async StarRocks-specific
    session management, including connection URL creation and async engine configuration.

    Args:
        orm_config: StarRocks-specific configuration. If None, uses global config.
    """

    def __init__(self, orm_config: StarRocksSQLAlchemyConfig | None = None) -> None:
        """Initialize the async StarRocks session manager.

        Args:
            orm_config: StarRocks-specific configuration. If None, uses global config.
        """
        configs = BaseConfig.global_config().STARROCKS_SQLALCHEMY if orm_config is None else orm_config
        super().__init__(configs)

    @override
    def _expected_config_type(self) -> type[StarRocksSQLAlchemyConfig]:
        """Return the expected configuration type for StarRocks.

        Returns:
            The StarRocksSQLAlchemyConfig class.
        """
        return StarRocksSQLAlchemyConfig

    @override
    def _get_database_name(self) -> str:
        """Return the name of the database being used.

        Returns:
            str: The name of the database ('starrocks').
        """
        return "starrocks"

    @override
    def _create_url(self, configs: StarRocksSQLAlchemyConfig) -> URL:
        """Create an async StarRocks connection URL.

        Args:
            configs: StarRocks configuration.

        Returns:
            A SQLAlchemy URL object for StarRocks.

        Raises:
            DatabaseConnectionError: If there's an error creating the URL.
        """
        try:
            return URL.create(
                drivername=configs.DRIVER_NAME,
                username=configs.USERNAME,
                password=configs.PASSWORD,
                host=configs.HOST,
                port=configs.PORT,
                database=configs.DATABASE,
            )
        except SQLAlchemyError as e:
            raise DatabaseConnectionError(
                database=self._get_database_name(),
            ) from e
