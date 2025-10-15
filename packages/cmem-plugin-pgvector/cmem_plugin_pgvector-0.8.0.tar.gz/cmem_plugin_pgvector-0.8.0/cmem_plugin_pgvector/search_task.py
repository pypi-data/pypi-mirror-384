"""Search Task"""

import json
from ast import literal_eval
from collections.abc import Generator, Sequence

from cmem_plugin_base.dataintegration.context import ExecutionContext, ExecutionReport
from cmem_plugin_base.dataintegration.description import Icon, Plugin, PluginAction, PluginParameter
from cmem_plugin_base.dataintegration.entity import Entities, Entity, EntityPath, EntitySchema
from cmem_plugin_base.dataintegration.parameter.password import Password
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.ports import (
    FixedNumberOfInputs,
    FixedSchemaPort,
)
from cmem_plugin_base.dataintegration.types import EnumParameterType, IntParameterType
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from cmem_plugin_pgvector.commons import (
    DatabaseConnectionError,
    DatabaseParams,
    check_database_connection,
)


class DummyEmbeddings(Embeddings):
    """Dummy embedding model"""

    def embed_query(self, text: str) -> list[float]:
        """Embed a query"""
        raise NotImplementedError

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents"""
        raise NotImplementedError


@Plugin(
    label="Search Vector Embeddings",
    description="Search for top-k metadata stored in Postgres Vector Store (PGVector).",
    documentation="""
This workflow task search for the top-k metadata stored into Postgres Vector Store.

The incoming embedding entities are used to retrieve the nearest top-k
vectors in the collection stored in the Postgres Vector Store.
It is possible to specify which paths are going to be used for searching as well as which Postgres
Vector Store and collection name.

The task uses the embeddings from the path configured with the Embedding Query Path
parameter (`embedding_query_path`, default value: `_embedding`) to search over the collection.
The results are provided in the output path configured with the Search Result Path parameter
(`search_result_path`, default value: `_search_result`).

The results in this output are structured like this:

``` json
[
{
   "id": "...",
   "metadata": "..",
   "_embedding_source": "..",
   "distance": ".."
}
...
]
```
""",
    icon=Icon(package=__package__, file_name="postgresql.svg"),
    plugin_id="cmem_plugin_pgvector-Search",
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
            name="embedding_query_path",
            label="Embedding Query Path",
            description="""The path containing the embedding to be used for searching.""",
            default_value="_embedding",
        ),
        PluginParameter(
            name="search_result_path",
            label="Search Result Path",
            description="""The path containing the search result in the output entities.""",
            default_value="_search_result",
        ),
        PluginParameter(
            name="top_k",
            label="Top-k",
            description="The number of entries to be returned in the search result.",
            default_value=10,
            param_type=IntParameterType(),
        ),
        PluginParameter(
            name="distance_strategy",
            label="Distance Strategy",
            description="The distance strategy to use. (default: COSINE)",
            param_type=EnumParameterType(enum_type=DistanceStrategy),
            default_value=DistanceStrategy.COSINE,
            advanced=True,
        ),
    ],
)
class PGVectorSearchPlugin(WorkflowPlugin):
    """PGVectorSearchPlugin: Enable the search of vectors in a Postgres Vector Store."""

    connection_string: str
    user: str
    password: str
    host: str
    port: int
    database: str
    collection_name: str
    embedding_query_path: str
    inputs: Sequence[Entities]
    db: PGVector
    execution_context: ExecutionContext
    report: ExecutionReport
    search_result_path: str
    top_k: int
    distance_strategy: DistanceStrategy

    def __init__(  # noqa: PLR0913
        self,
        host: str = DatabaseParams.host.default_value,
        port: int = DatabaseParams.port.default_value,
        user: str = DatabaseParams.user.default_value,
        password: Password | str = "",
        database: str = DatabaseParams.database.default_value,
        collection_name: str = DatabaseParams.collection_name.default_value,
        search_result_path: str = "_search_result",
        embedding_query_path: str = "_embedding",
        top_k: int = 10,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
    ) -> None:
        self.collection_name = collection_name
        self.user = user
        self.host = host
        self.port = port
        self.database = database
        self.embedding_query_path = embedding_query_path
        self.search_result_path = search_result_path
        self.top_k = top_k
        self.distance_strategy = distance_strategy

        str_password = self.password = password if isinstance(password, str) else password.decrypt()
        self.connection_string = (
            f"postgresql+psycopg://{user}:{str_password}@{host}:{port}/{database}"
        )

        self.report = ExecutionReport()
        self.report.operation = "search"
        self.report.operation_desc = "searches"
        self._setup_ports()

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

    def _setup_ports(self) -> None:
        """Configure input and output ports depending on the configuration"""
        input_paths = [EntityPath(path=self.embedding_query_path)]
        input_schema = EntitySchema(type_uri="entity", paths=input_paths)
        self.input_ports = FixedNumberOfInputs(ports=[FixedSchemaPort(schema=input_schema)])

        output_schema = self._generate_output_schema(input_schema=input_schema)
        self.output_port = FixedSchemaPort(schema=output_schema)

    def _generate_output_schema(self, input_schema: EntitySchema) -> EntitySchema:
        """Get output schema"""
        paths = list(input_schema.paths).copy()
        paths.append(EntityPath(self.search_result_path))
        return EntitySchema(type_uri=input_schema.type_uri, paths=paths)

    @staticmethod
    def _entity_to_dict(paths: Sequence[EntityPath], entity: Entity) -> dict[str, list[str]]:
        """Create a dict representation of an entity"""
        entity_dic = {}
        for key, value in zip(paths, entity.values, strict=False):
            entity_dic[key.path] = list(value)
        return entity_dic

    def _update_report(self, count: int) -> None:
        """Update the report"""
        self.report.entity_count = count
        self.execution_context.report.update(self.report)

    def _cancel_workflow(self) -> bool:
        """Cancel workflow"""
        try:
            if self.execution_context.workflow.status() == "Canceling":
                self.log.info("End task (Cancelled Workflow).")
                return True
        except AttributeError:
            pass
        return False

    @staticmethod
    def _docs_to_json(docs: list[tuple[Document, float]]) -> list:
        """Convert a list of Documents to a list of metadata"""
        doc_list: list = []
        for doc_tuple in docs:
            json_entity = {
                "id": doc_tuple[0].id,
                "metadata": doc_tuple[0].metadata,
                "_embedding_source": doc_tuple[0].page_content,
                "distance": str(doc_tuple[1]),
            }
            doc_list.append(json_entity)
        return doc_list

    def _process_entities(self, entities: Entities) -> Generator[Entity]:
        """Process incoming entities' embeddings in vector search"""
        schema_paths: list[EntityPath] = list(entities.schema.paths)
        n_processed_entries: int = 0
        self._update_report(n_processed_entries)
        for entity in entities.entities:
            if self._cancel_workflow():
                return
            entity_dict = self._entity_to_dict(schema_paths, entity)
            embedding: list[float] = literal_eval(entity_dict[self.embedding_query_path][0])
            result: list[tuple[Document, float]] = self.db.similarity_search_with_score_by_vector(
                embedding=embedding, k=self.top_k
            )
            json_result = self._docs_to_json(result)
            entity_dict[self.search_result_path] = [json.dumps(json_result)]
            values = list(entity_dict.values())
            n_processed_entries += 1
            self._update_report(n_processed_entries)
            yield Entity(uri=entity.uri, values=values)

    def execute(
        self,
        inputs: Sequence[Entities],
        context: ExecutionContext,
    ) -> Entities:
        """Run the workflow operator."""
        self.log.info("Start searching collection.")
        self.db = PGVector(
            collection_name=self.collection_name,
            connection=self.connection_string,
            embeddings=DummyEmbeddings(),
            use_jsonb=True,
            pre_delete_collection=False,
            distance_strategy=self.distance_strategy,
        )
        self.inputs = inputs
        self.execution_context = context
        try:
            first_input: Entities = self.inputs[0]
        except IndexError as error:
            raise ValueError("Input port not connected.") from error
        entities = self._process_entities(first_input)
        schema = self._generate_output_schema(first_input.schema)
        self.log.info("End")
        return Entities(entities=entities, schema=schema)
