"""Configuration builder for :mod:`dtpyfw.db` utilities."""

from typing import Any

__all__ = ("DatabaseConfig",)


class DatabaseConfig:
    """Simple builder for SQLAlchemy connection settings."""

    def __init__(self) -> None:
        self._config_data: dict[str, Any] = {
            "db_backend": "postgresql",
            "db_driver_async": "asyncpg",
            "connect_args": None,
        }

    def set_db_backend(self, db_backend: str) -> "DatabaseConfig":
        self._config_data["db_backend"] = db_backend
        return self

    def set_db_driver_sync(self, db_driver_sync: str) -> "DatabaseConfig":
        self._config_data["db_driver_sync"] = db_driver_sync
        return self

    def set_db_driver_async(self, db_driver_async: str) -> "DatabaseConfig":
        self._config_data["db_driver_async"] = db_driver_async
        return self

    def set_connect_args(self, connect_args: dict) -> "DatabaseConfig":
        self._config_data["connect_args"] = connect_args
        return self

    def set_db_url(self, db_url: str) -> "DatabaseConfig":
        """Set full database URL for both read and write operations."""
        self._config_data["db_url"] = db_url
        return self

    def set_db_url_read(self, db_url_read: str) -> "DatabaseConfig":
        """Set a read-only database URL."""
        self._config_data["db_url_read"] = db_url_read
        return self

    def set_db_user(self, db_user: str) -> "DatabaseConfig":
        self._config_data["db_user"] = db_user
        return self

    def set_db_password(self, db_password: str) -> "DatabaseConfig":
        self._config_data["db_password"] = db_password
        return self

    def set_db_host(self, db_host: str) -> "DatabaseConfig":
        self._config_data["db_host"] = db_host
        return self

    def set_db_host_read(self, db_host_read: str) -> "DatabaseConfig":
        self._config_data["db_host_read"] = db_host_read
        return self

    def set_db_port(self, db_port: int) -> "DatabaseConfig":
        self._config_data["db_port"] = db_port
        return self

    def set_db_name(self, db_name: str) -> "DatabaseConfig":
        self._config_data["db_name"] = db_name
        return self

    def set_db_ssl(self, db_ssl: bool) -> "DatabaseConfig":
        self._config_data["db_ssl"] = db_ssl
        return self

    def set_db_pool_size(self, db_pool_size: int) -> "DatabaseConfig":
        self._config_data["db_pool_size"] = db_pool_size
        return self

    def set_db_max_overflow(self, db_max_overflow: int) -> "DatabaseConfig":
        self._config_data["db_max_overflow"] = db_max_overflow
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value."""

        return self._config_data.get(key, default)
