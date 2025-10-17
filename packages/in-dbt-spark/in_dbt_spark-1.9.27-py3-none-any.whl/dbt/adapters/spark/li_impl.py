from dataclasses import dataclass
from contextlib import contextmanager
from dbt_common.events.functions import fire_event
from dbt.adapters.events.types import ListRelations
import agate
from dbt.adapters.cache import _make_ref_key_dict
from dbt.adapters.base import PythonJobHelper
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.spark.li_spark_utils import is_openhouse
from dbt.adapters.base import BaseRelation, available
from dbt_common.utils import AttrDict, cast_to_str
from dbt_common.dataclass_schema import dbtClassMixin, ValidationError
from dbt.adapters.spark.impl import SparkConfig
from dbt.adapters.spark import (
    ExtendedSparkConnectionManager,
    ExtendedSparkRelation,
    SparkColumn,
    SparkAdapter,
)
from dbt.adapters.spark import SparkRelation
from typing_extensions import TypeAlias
from dbt.adapters.contracts.relation import RelationType, RelationConfig
import dbt_common.exceptions
from dbt.adapters.spark.li_python_submissions import (
    ExtendedJobClusterPythonJobHelper,
    ExtendedAllPurposeClusterPythonJobHelper,
)
from dbt.adapters.setu.setu_python_submissions import SetuPythonJobHelper
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Type,
    Tuple,
    Callable,
    Iterable,
    Iterator,
    Set,
    DefaultDict,
)


LIST_SCHEMAS_MACRO_NAME = "list_schemas"
LIST_RELATIONS_MACRO_NAME = "list_relations_without_caching"
LIST_RELATIONS_SHOW_TABLES_MACRO_NAME = "list_relations_show_tables_without_caching"
CURRENT_CATALOG_MACRO_NAME = "current_catalog"
USE_CATALOG_MACRO_NAME = "use_catalog"
KEY_TABLE_TYPE = "Type"
KEY_TABLE_PROVIDER = "Provider"
DESCRIBE_TABLE_EXTENDED_MACRO_NAME = "describe_table_extended_without_caching"


logger = AdapterLogger("Spark")


@dataclass
class PartitionConfig(dbtClassMixin):
    field: str
    data_type: str
    granularity: Optional[str] = None

    @classmethod
    def parse(cls, partition_by) -> Optional["PartitionConfig"]:
        if partition_by is None:
            return None
        try:
            cls.validate(partition_by)
            return cls.from_dict(partition_by)
        except ValidationError as exc:
            raise dbt_common.exceptions.DbtConfigError("Could not parse partition config") from exc
        except TypeError:
            raise dbt_common.exceptions.CompilationError(
                f"Invalid partition_by config:\n"
                f"  Got: {partition_by}\n"
                f'  Expected a dictionary with "field" and "data_type" keys'
            )


@dataclass
class ExtendedSparkConfig(SparkConfig):
    file_format: str = "openhouse"
    partition_by: Optional[Union[List[Dict[str, str]], Dict[str, str]]] = None
    retention_period: Optional[str] = None


class ExtendedSparkAdapter(SparkAdapter):
    RelationInfo = Tuple[str, str, str, str]

    Relation: TypeAlias = ExtendedSparkRelation
    ConnectionManager: TypeAlias = ExtendedSparkConnectionManager
    AdapterSpecificConfigs: TypeAlias = ExtendedSparkConfig

    def _get_relation_information(
        self, schema_relation: BaseRelation, row: agate.Row
    ) -> RelationInfo:
        """relation info was fetched with SHOW TABLES EXTENDED"""
        try:
            _schema = row[0]
            name = row[1]
            _ = row[2]
            information = row[3]
        except ValueError:
            raise dbt_common.exceptions.DbtRuntimeError(
                f'Invalid value from "show tables extended ...", got {len(row)} values, expected 4'
            )

        return schema_relation.database, _schema, name, information

    def parse_describe_extended(
        self, relation: BaseRelation, raw_rows: AttrDict
    ) -> List[SparkColumn]:
        result = super().parse_describe_extended(relation, raw_rows)
        for spark_column in result:
            spark_column.table_database = relation.database
        return result

    def parse_columns_from_information(self, relation: BaseRelation) -> List[SparkColumn]:
        result = super().parse_columns_from_information(relation)
        for spark_column in result:
            spark_column.table_database = relation.database
        return result
    
    # overriding this method to optimize the performance of list_relations_without_caching
    def _get_cache_schemas(self, relation_configs: Iterable[RelationConfig]) -> Set[BaseRelation]:
        """Get the set of schema relations that the cache logic needs to
        populate. This means only executable nodes are included.
        """
        relation_map = self._get_relation_map(relation_configs)

        schemas = [
            self.Relation.create(
                schema=schema,
                identifier=(
                    "|".join(r.identifier for r in relations if r.identifier)
                    if len(relations) < 100
                    else "*"
                ),
            )
            for schema, relations in relation_map.items()
        ]
        return set(schemas)

    def _get_columns_for_catalog(self, relation: BaseRelation) -> Iterable[Dict[str, Any]]:
        columns = self.parse_columns_from_information(relation)
        if not columns:
            # Columns are empty for openhouse, since it's trying to parse using spark logic
            logger.info(
                "parse_columns_from_information doesn't return any columns, format may be openhouse"
                "Trying to fetch and parse using openhouse format"
            )

            # Fetching columns data from openhouse
            columns = self.get_columns_in_relation(relation)
        for column in columns:
            # convert SparkColumns into catalog dicts
            as_dict = column.to_column_dict()
            as_dict["column_name"] = as_dict.pop("column", None)
            as_dict["column_type"] = as_dict.pop("dtype")
            as_dict["table_database"] = relation.database
            yield as_dict

    def _get_relation_information_using_describe(
        self, schema_relation: BaseRelation, row: agate.Row
    ) -> RelationInfo:
        """Relation info fetched using SHOW TABLES and an auxiliary DESCRIBE statement"""
        try:
            _schema = row[0]
            name = row[1]
        except ValueError:
            raise dbt_common.exceptions.DbtRuntimeError(
                f'Invalid value from "show tables ...", got {len(row)} values, expected 2'
            )

        # database is needed where relations can exist in different catalogs
        table_name = f"{_schema}.{name}"
        if is_openhouse(schema_relation.database, schema_relation.schema):
            if not table_name.startswith("openhouse."):
                table_name = "openhouse." + table_name
            _schema = "openhouse." + _schema

        try:
            table_results = self.execute_macro(
                DESCRIBE_TABLE_EXTENDED_MACRO_NAME, kwargs={"table_name": table_name}
            )
        except dbt_common.exceptions.DbtRuntimeError as e:
            logger.debug(f"Error while retrieving information about {table_name}: {e.msg}")
            table_results = AttrDict()

        information = ""
        for info_row in table_results:
            info_type, info_value, _ = info_row
            if not info_type.startswith("#"):
                information += f"{info_type}: {info_value}\n"

        return schema_relation.database, _schema, name, information
    
    def _get_relation_map(
        self, relation_configs: Iterable[RelationConfig]
    ) -> DefaultDict[Optional[str], List[SparkRelation]]:
        """Relations compiled together based on schema"""
        relations = [
            self.Relation.create_from(self.config, node)  # keep the identifier
            for node in relation_configs
            if (node.is_relational and not node.is_ephemeral_model)
        ]
        sources = [
            self.Relation.create_from(self.config, node)  # keep the identifier
            for node in relation_configs
        ]

        import collections

        relation_map = collections.defaultdict(list)
        for r in relations:
            relation_map[r.schema].append(r)
        for s in sources:
            if s.database == "openhouse" and "." not in str(s.schema):
                relation_map[f"{s.database}.{s.schema}"].append(s)
            else:
                relation_map[s.schema].append(s)

        return relation_map

    def _build_spark_relation_list(
        self,
        schema_relation: BaseRelation,
        row_list: agate.Table,
        relation_info_func: Callable[[BaseRelation, agate.Row], RelationInfo],
    ) -> List[BaseRelation]:
        """Aggregate relations with format metadata included."""
        relations = []
        for row in row_list:
            database, _schema, name, information = relation_info_func(schema_relation, row)

            rel_type: RelationType = (
                RelationType.View if "Type: VIEW" in information else RelationType.Table
            )
            is_delta: bool = "Provider: delta" in information
            is_hudi: bool = "Provider: hudi" in information
            is_iceberg: bool = "Provider: iceberg" in information
            is_openhouse: bool = "Provider: openhouse" in information

            relation: BaseRelation = self.Relation.create(
                database=database if database and not _schema.startswith("openhouse.") else None,
                schema=_schema,
                identifier=name,
                type=rel_type,
                information=information,
                is_delta=is_delta,
                is_iceberg=is_iceberg,
                is_hudi=is_hudi,
                is_openhouse=is_openhouse,
            )
            relations.append(relation)

        return relations

    def list_relations_without_caching(self, schema_relation: BaseRelation) -> List[BaseRelation]:
        """Distinct Spark compute engines may not support the same SQL featureset. Thus, we must
        try different methods to fetch relation information."""

        kwargs = {"schema_relation": schema_relation}

        logger.info(f"schema_relation.database: {schema_relation.database}")
        logger.info(f"schema_relation.schema: {schema_relation.schema}")
        logger.info(f"schema_relation.identifier: {schema_relation.identifier}")

        try:
            if is_openhouse(schema_relation.database, schema_relation.schema):
                # Iceberg behavior: 3-row result of relations obtained
                logger.info(f"Schema relation: {schema_relation.schema}")
                show_table_rows = self.execute_macro(
                    LIST_RELATIONS_SHOW_TABLES_MACRO_NAME, kwargs=kwargs
                )
                return self._build_spark_relation_list(
                    schema_relation=schema_relation,
                    row_list=show_table_rows,
                    relation_info_func=self._get_relation_information_using_describe,
                )
            else:
                with self._catalog(schema_relation.database):
                    show_table_extended_rows = self.execute_macro(
                        LIST_RELATIONS_MACRO_NAME, kwargs=kwargs
                    )
                    return self._build_spark_relation_list(
                        schema_relation=schema_relation,
                        row_list=show_table_extended_rows,
                        relation_info_func=self._get_relation_information,
                    )
        except dbt_common.exceptions.DbtRuntimeError as e:
            errmsg = getattr(e, "msg", "")
            print(errmsg)
            if f"Database '{schema_relation}' not found" in errmsg:
                return []
            # Iceberg compute engine behavior: show table
            elif "SHOW TABLE EXTENDED is not supported for v2 tables" in errmsg:
                # this happens with spark-iceberg with v2 iceberg tables
                # https://issues.apache.org/jira/browse/SPARK-33393
                try:
                    # Iceberg behavior: 3-row result of relations obtained
                    show_table_rows = self.execute_macro(
                        LIST_RELATIONS_SHOW_TABLES_MACRO_NAME, kwargs=kwargs
                    )
                    return self._build_spark_relation_list(
                        schema_relation=schema_relation,
                        row_list=show_table_rows,
                        relation_info_func=self._get_relation_information_using_describe,
                    )
                except dbt_common.exceptions.DbtRuntimeError as e:
                    description = "Error while retrieving information about"
                    logger.debug(f"{description} {schema_relation}: {e.msg}")
                    return []
            else:
                logger.debug(
                    f"Error while retrieving information about {schema_relation}: {errmsg}"
                )
                return []

    def get_relation(self, database: str, schema: str, identifier: str) -> Optional[BaseRelation]:
        if not self.Relation.get_default_include_policy().database:
            database = None  # type: ignore
        else:
            database = database if database else None  # type: ignore

        return super().get_relation(database, schema, identifier)

    @property
    def python_submission_helpers(self) -> Dict[str, Type[PythonJobHelper]]:
        return {
            "job_cluster": ExtendedJobClusterPythonJobHelper,
            "all_purpose_cluster": ExtendedAllPurposeClusterPythonJobHelper,
            "setu": SetuPythonJobHelper,
        }

    @property
    def default_python_submission_method(self) -> str:
        return "setu"

    def _get_one_catalog(
        self,
        information_schema,
        schemas,
        manifest,
    ) -> agate.Table:
        if len(schemas) != 1:
            raise dbt.exceptions.CompilationError(
                f"Expected only one schema in spark _get_one_catalog, found " f"{schemas}"
            )

        database = information_schema.database
        schema = list(schemas)[0]

        relation_map = self._get_relation_map(manifest)

        columns: List[Dict[str, Any]] = []
        for relation in self.list_relations(database, schema, relation_map=relation_map):
            logger.debug("Getting table schema for relation {}", str(relation))
            columns.extend(self._get_columns_for_catalog(relation))
        return agate.Table.from_object(columns, column_types=DEFAULT_TYPE_TESTER)

    def list_schemas(self, database: str) -> List[str]:
        connection = self.connections.get_if_exists()
        if connection is not None:
            database = connection.credentials.database
            schema = connection.credentials.schema

        # in case the user is using "openhouse" as a catalog, the format of schema will be 'openhouse.db'.
        # so derive the catalog/database value from schema until we support `openhouse` catalog natively.
        if schema is not None and "." in schema:
            tokens = schema.split(".")
            database = tokens[0]
            schema = tokens[1]

        # The catalog for `show table extended` needs to match the current catalog.
        with self._catalog(database):
            results = self.execute_macro(LIST_SCHEMAS_MACRO_NAME, kwargs={"database": schema})
        schema_list = [row[0] for row in results]
        return schema_list

    def list_relations(self, database: Optional[str], schema: str, **kwargs) -> List[BaseRelation]:
        if self._schema_is_cached(database, schema):
            return self.cache.get_relations(database, schema)

        relation_map = kwargs.get("relation_map", None)

        if relation_map:
            if database == "openhouse" and "." not in schema:
                schema = f"{database}.{schema}"

        schema_relation = self.Relation.create(
            database=database,
            schema=schema,
            identifier=(
                "|".join(r.identifier for r in relation_map[schema]) if relation_map else ""
            ),
            quote_policy=self.config.quoting,
        )

        # we can't build the relations cache because we don't have a
        # manifest so we can't run any operations.
        relations = self.list_relations_without_caching(schema_relation)

        # if the cache is already populated, add this schema in
        # otherwise, skip updating the cache and just ignore
        if self.cache:
            for relation in relations:
                self.cache.add(relation)
            if not relations:
                # it's possible that there were no relations in some schemas. We want
                # to insert the schemas we query into the cache's `.schemas` attribute
                # so we can check it later
                self.cache.update_schemas([(database, schema)])

        fire_event(
            ListRelations(
                database=cast_to_str(database),
                schema=schema,
                relations=[_make_ref_key_dict(x) for x in relations],
            )
        )

        return relations

    def check_schema_exists(self, database, schema):
        # in case the user is using "openhouse" as a catalog, the format of schema will be 'openhouse.db'.
        # so derive the catalog/database value from schema until we support `openhouse` catalog natively.
        if schema is not None and "." in schema:
            tokens = schema.split(".")
            database = tokens[0]
            schema = tokens[1]
        # The catalog for `show table extended` needs to match the current catalog.
        with self._catalog(database):
            results = self.execute_macro(LIST_SCHEMAS_MACRO_NAME, kwargs={"database": schema})
        exists = True if schema in [row[0] for row in results] else False
        return exists

    def standardize_grants_dict(
        self, grants_table: agate.Table, schema_relation: BaseRelation
    ) -> dict:
        grants_dict: Dict[str, List[str]] = {}
        if is_openhouse(schema_relation.database, schema_relation.schema):
            for row in grants_table:
                grantee = row["principal"]
                privilege = row["privilege"]

                # we don't want to consider the ALTER privilege in OpenHouse
                if privilege != "ALTER":
                    if privilege in grants_dict.keys():
                        grants_dict[privilege].append(grantee)
                    else:
                        grants_dict.update({privilege: [grantee]})
        else:
            for row in grants_table:
                grantee = row["Principal"]
                privilege = row["ActionType"]
                object_type = row["ObjectType"]

                # we only want to consider grants on this object
                # (view or table both appear as 'TABLE')
                # and we don't want to consider the OWN privilege
                if object_type == "TABLE" and privilege != "OWN":
                    if privilege in grants_dict.keys():
                        grants_dict[privilege].append(grantee)
                    else:
                        grants_dict.update({privilege: [grantee]})
        return grants_dict

    @contextmanager
    def _catalog(self, catalog: Optional[str]) -> Iterator[None]:
        """
        A context manager to make the operation work in the specified catalog,
        and move back to the current catalog after the operation.
        If `catalog` is None, the operation works in the current catalog.
        """
        current_catalog: Optional[str] = None
        try:
            if catalog is not None:
                current_catalog = self.execute_macro(CURRENT_CATALOG_MACRO_NAME)[0][0]
                if current_catalog is not None:
                    if current_catalog != catalog:
                        self.execute_macro(USE_CATALOG_MACRO_NAME, kwargs=dict(catalog=catalog))
                    else:
                        current_catalog = None
            yield
        finally:
            if current_catalog is not None:
                self.execute_macro(USE_CATALOG_MACRO_NAME, kwargs=dict(catalog=current_catalog))

    @available
    def parse_partition_by(self, raw_partition_by: Any):
        partition_by_list = []
        if raw_partition_by is None:
            return None
        if isinstance(raw_partition_by, dict):
            raw_partition_by = [raw_partition_by]
        for partition_by in raw_partition_by:
            partition_by_list.append(PartitionConfig.parse(partition_by))
        return partition_by_list
