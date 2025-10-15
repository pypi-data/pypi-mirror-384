"""Store Task"""

from ast import literal_eval
from collections.abc import Sequence
from typing import Any

from cmem_plugin_base.dataintegration.context import ExecutionContext, ExecutionReport
from cmem_plugin_base.dataintegration.description import Icon, Plugin, PluginAction, PluginParameter
from cmem_plugin_base.dataintegration.entity import Entities, Entity, EntityPath
from cmem_plugin_base.dataintegration.parameter.password import Password
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.ports import (
    FixedNumberOfInputs,
    UnknownSchemaPort,
)
from langchain_postgres import PGVector

from cmem_plugin_pgvector.commons import (
    DatabaseConnectionError,
    DatabaseParams,
    check_database_connection,
)


class DataContainer:
    """Encapsulate the data to be added to the database."""

    def __init__(self):
        self.texts = []
        self.embeddings = []
        self.metadata = []

    def add(self, text: str, embedding: list[float], metadata: dict) -> None:
        """Add objects to the respective lists."""
        self.texts.append(text)
        self.embeddings.append(embedding)
        self.metadata.append(metadata)

    def clear(self) -> None:
        """Clear all three lists."""
        self.texts.clear()
        self.embeddings.clear()
        self.metadata.clear()

    def size(self) -> int:
        """Return the size of the lists (assuming all lists have the same length)."""
        return len(self.texts)


@Plugin(
    label="Store Vector Embeddings",
    description="Store embeddings into Postgres Vector Store (PGVector).",
    documentation="""
This plugin workflow store embeddings into Postgres Vector Store.

The vector embeddings and its respective metadata are going to be stored into a collection inside
the Postgres Vector Store.
It is possible to specify either the name of the attributes containing the vectors as well as the
metadata.
""",
    icon=Icon(package=__package__, file_name="postgresql.svg"),
    plugin_id="cmem_plugin_pgvector-Store",
    actions=[
        PluginAction(
            name="test_connection",
            label="Test Connection",
            description="Test database connectivity",
        )
    ],
    parameters=[
        *DatabaseParams().as_list(),
        PluginParameter(
            name="pre_delete_collection",
            label="Pre Delete Collection",
            description="If set to true, then the collection will removed at the beginning.",
            default_value=True,
        ),
        PluginParameter(
            name="source_path",
            label="Source Path",
            description="The name of the path to use for reading the embedding source.",
            default_value="_embedding_source",
            advanced=True,
        ),
        PluginParameter(
            name="embedding_path",
            label="Embedding Path",
            description="The name of the path to use for reading the embeddings.",
            default_value="_embedding",
            advanced=True,
        ),
        PluginParameter(
            name="metadata_paths",
            label="Metadata Paths",
            description="The comma separated list path names to be used as metadata. "
            "Empty name means all paths "
            "(except embedding source and embedding) will be used",
            default_value="",
            advanced=True,
        ),
        PluginParameter(
            name="batch_processing_size",
            label="Batch Processing Size",
            description="The number of entries to be processed in batch.",
            default_value=100,
            advanced=True,
        ),
    ],
)
class PGVectorStorePlugin(WorkflowPlugin):
    """PGVectorStorePlugin: Enable the storage of vectors into Postgres Vector Store."""

    connection_string: str
    user: str
    password: str
    host: str
    port: int
    database: str
    collection_name: str
    source_path: str
    embedding_path: str
    metadata_paths: str
    batch_processing_size: int
    inputs: Sequence[Entities]
    db: PGVector
    report: ExecutionReport

    def __init__(  # noqa: PLR0913
        self,
        host: str = DatabaseParams.host.default_value,
        port: int = DatabaseParams.port.default_value,
        user: str = DatabaseParams.user.default_value,
        password: Password | str = "",
        database: str = DatabaseParams.database.default_value,
        collection_name: str = DatabaseParams.collection_name.default_value,
        pre_delete_collection: bool = True,
        source_path: str = "_embedding_source",
        embedding_path: str = "_embedding",
        metadata_paths: str = "metadata",
        batch_processing_size: int = 1000,
    ) -> None:
        self.batch_processing_size = batch_processing_size
        self.collection_name = collection_name
        self.user = user
        self.host = host
        self.port = port
        self.database = database
        self.embedding_path = embedding_path
        self.metadata_paths = metadata_paths
        self.source_path = source_path
        self.pre_delete_collection = pre_delete_collection

        self.output_port = None
        self.input_ports = FixedNumberOfInputs([UnknownSchemaPort()])
        str_password = self.password = password if isinstance(password, str) else password.decrypt()
        self.connection_string = (
            f"postgresql+psycopg://{user}:{str_password}@{host}:{port}/{database}"
        )

        self.report = ExecutionReport()
        self.report.operation = "store"
        self.report.operation_desc = "vectors stored"

    def test_connection(self) -> str:
        """Plugin Action to test database connection"""
        try:
            return check_database_connection(
                dbname=self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
        except DatabaseConnectionError as e:
            raise ValueError(f"Connection test failed: {e!s}") from e

    def _update_report(self, count: int) -> None:
        self.report.entity_count = count
        self.execution_context.report.update(self.report)

    def _paths_to_metadata(
        self, paths: list[str], entity: Entity, schema_paths: list[EntityPath]
    ) -> dict[str, Any]:
        metadata_paths = [path for path in schema_paths if path.path in paths]
        return self._metadata(entity, metadata_paths)

    def _index_of(self, path_name: str, paths: list[EntityPath]) -> int:
        for path in paths:
            if path.path == path_name:
                return paths.index(path)
        return -1

    def _metadata(self, entity: Entity, schema_paths: list[EntityPath]) -> dict[str, Any]:
        entity_dict: dict[str, Any] = {}
        for path, values in zip(schema_paths, entity.values, strict=False):
            if path.path not in (self.embedding_path, self.source_path):
                entity_dict[path.path] = list(values)
        return entity_dict

    def _cancel_workflow(self) -> bool:
        """Cancel workflow"""
        try:
            if self.execution_context.workflow.status() == "Canceling":
                self.log.info("End task (Cancelled Workflow).")
                return True
        except AttributeError:
            pass
        return False

    def _process_entities(self, entities: Entities) -> None:
        schema_paths: list[EntityPath] = list(entities.schema.paths)
        text_path_idx: int = self._index_of(self.source_path, schema_paths)
        embedding_path_idx: int = self._index_of(self.embedding_path, schema_paths)

        if text_path_idx == -1 or embedding_path_idx == -1:
            raise ValueError("The data does not have a text or embedding paths defined.")

        n_processed_entries: int = 0
        container: DataContainer = DataContainer()
        self._update_report(n_processed_entries)
        for entity in entities.entities:
            container.add(
                entity.values[text_path_idx][0],
                literal_eval(entity.values[embedding_path_idx][0]),
                self._paths_to_metadata(self.metadata_paths.split(","), entity, schema_paths)
                if self.metadata_paths
                else self._metadata(entity, schema_paths),
            )
            if container.size() == self.batch_processing_size:
                self.db.add_embeddings(container.texts, container.embeddings, container.metadata)
                n_processed_entries += container.size()
                self._update_report(n_processed_entries)
                container.clear()
            if self._cancel_workflow():
                return
        if container.size() > 0:
            self.db.add_embeddings(container.texts, container.embeddings, container.metadata)
            n_processed_entries += container.size()
            self._update_report(n_processed_entries)

    def execute(
        self,
        inputs: Sequence[Entities],
        context: ExecutionContext,
    ) -> None:
        """Run the workflow operator."""
        self.log.info("Start storing vectors.")
        self.db = PGVector(
            collection_name=self.collection_name,
            connection=self.connection_string,
            embeddings=None,  # type: ignore  # noqa: PGH003
            use_jsonb=True,
            pre_delete_collection=self.pre_delete_collection,
        )
        self.inputs = inputs
        self.execution_context = context
        try:
            first_input: Entities = self.inputs[0]
        except IndexError as error:
            raise ValueError("Input port not connected.") from error
        self._process_entities(first_input)
        self.log.info("Vectors stored successfuly.")
