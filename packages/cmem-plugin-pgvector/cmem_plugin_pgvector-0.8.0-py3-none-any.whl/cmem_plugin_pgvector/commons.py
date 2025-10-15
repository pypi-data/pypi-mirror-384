"""PGVector commons"""

from typing import Any, ClassVar

import psycopg
from cmem_plugin_base.dataintegration.context import (
    PluginContext,
)
from cmem_plugin_base.dataintegration.description import PluginParameter
from cmem_plugin_base.dataintegration.parameter.password import PasswordParameterType
from cmem_plugin_base.dataintegration.types import (
    Autocompletion,
    IntParameterType,
    StringParameterType,
)


class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""


def check_database_connection(dbname: str, user: str, password: str, host: str, port: int) -> str:
    """Test database connection and return success message or raise exception on failure"""
    try:
        with (
            psycopg.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=10,
            ) as conn,
            conn.cursor() as cursor,
        ):
            # Test basic connectivity
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]  # type: ignore[index]
            return f"Connection successful. PostgreSQL version: {version[:50]}..."

    except psycopg.OperationalError as e:
        raise DatabaseConnectionError(f"Connection failed: {e!s}") from e
    except psycopg.Error as e:
        raise DatabaseConnectionError(f"Database error: {e!s}") from e
    except Exception as e:
        raise DatabaseConnectionError(f"Unexpected error: {e!s}") from e


def get_collection_names(
    dbname: str, user: str, password: str, host: str = "localhost", port: int = 5432
) -> list[str]:
    """Return list of collection names"""
    # Create a connection to the database
    with (
        psycopg.connect(dbname=dbname, user=user, password=password, host=host, port=port) as conn,
        conn.cursor() as cursor,
    ):
        # Execute query
        cursor.execute("SELECT name FROM public.langchain_pg_collection;")
        return [row[0] for row in cursor.fetchall()]  # Fetch all names


class PGVectorCollection(StringParameterType):
    """PGVector Collection Type"""

    autocompletion_depends_on_parameters: ClassVar[list[str]] = [
        "host",
        "port",
        "database",
        "user",
        "password",
    ]

    # auto complete for values
    allow_only_autocompleted_values: bool = False
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Return all results that match ALL provided query terms."""
        _ = context
        host = depend_on_parameter_values[0]
        port = depend_on_parameter_values[1]
        dbname = depend_on_parameter_values[2]
        user = depend_on_parameter_values[3]
        password = depend_on_parameter_values[4]
        password = password if isinstance(password, str) else password.decrypt()
        result: list[Autocompletion] = []
        try:
            collections = get_collection_names(
                host=host, port=port, dbname=dbname, user=user, password=password
            )
        except psycopg.Error:
            return result
        filtered_collections = set()
        for term in query_terms:
            for collection in collections:
                if term in collection:
                    filtered_collections.add(collection)
        result = [Autocompletion(value=f"{_}", label=f"{_}") for _ in filtered_collections]
        result.sort(key=lambda x: x.label)
        return result


class DatabaseParams:
    """Common Plugin parameters"""

    host = PluginParameter(
        name="host",
        label="Database Host",
        description="The hostname of the postgres database service.",
        default_value="pgvector",
    )
    port = PluginParameter(
        name="port",
        label="Database Port",
        param_type=IntParameterType(),
        description="The port number of the postgres database service.",
        default_value=5432,
    )
    user = PluginParameter(
        name="user",
        label="Database User",
        description="The account name used to login to the postgres database service.",
        default_value="pgvector",
    )
    password = PluginParameter(
        name="password",
        label="Database Password",
        param_type=PasswordParameterType(),
        description="The password of the database account.",
    )
    database = PluginParameter(
        name="database",
        label="Database Name",
        description="The database name.",
        default_value="pgvector",
    )
    collection_name = PluginParameter(
        name="collection_name",
        label="Collection Name",
        description="The name of the collection that will be used for search.",
        param_type=PGVectorCollection(),
    )

    def as_list(self) -> list[PluginParameter]:
        """Provide all parameters as list"""
        return [
            getattr(self, attr)
            for attr in dir(self)
            if not callable(getattr(self, attr)) and not attr.startswith("__")
        ]
