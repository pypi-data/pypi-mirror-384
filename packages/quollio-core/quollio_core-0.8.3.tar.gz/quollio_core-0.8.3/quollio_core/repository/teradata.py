from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import teradatasql

from quollio_core.helper.log_utils import error_handling_decorator, logger


@dataclass
class TeradataConfig:
    host: str
    port: int
    username: str
    password: str
    database: str = "DBC"
    system_database: str = "DBC"
    encrypt_data: bool = True
    additional_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        credentials: Dict[str, str],
        host: str,
        port: str,
        additional_params: Dict[str, Any] = None,
        system_database: str = "DBC",
    ) -> "TeradataConfig":
        return cls(
            host=host,
            port=int(port),
            username=credentials["username"],
            password=credentials["password"],
            system_database=system_database,
            additional_params=additional_params or {},
        )

    def get_connection_params(self) -> Dict[str, Any]:
        params = {
            "host": self.host,
            "user": self.username,
            "password": self.password,
            "database": self.database,
            "dbs_port": self.port,
            "encryptdata": str(self.encrypt_data).lower(),
        }
        params.update(self.additional_params)
        return params


@error_handling_decorator
def new_teradata_client(config: TeradataConfig) -> teradatasql.connect:
    conn = teradatasql.connect(**config.get_connection_params())
    return conn


@error_handling_decorator
def get_table_list(
    conn: teradatasql.connect,
    target_databases: Optional[List[str]] = None,
    target_databases_method: str = "DENYLIST",
    system_database: str = "DBC",
) -> List[Dict[str, str]]:
    if target_databases_method == "DENYLIST":
        operator = "NOT"
    else:
        operator = ""

    query_tables = f"""
    SELECT DatabaseName, TableName
    FROM {system_database}.TablesV
    WHERE TableKind IN ('T', 'O', 'Q')
        AND DatabaseName {operator} IN ({','.join("'" + db + "'" for db in target_databases)})
    """
    logger.debug("Executing query to retrieve table names.")
    logger.debug(f"Query: {query_tables}")
    tables = execute_query(query_tables, conn)
    return tables


@error_handling_decorator
def get_column_list(
    conn: teradatasql.connect, database_name: str, table_name: str, system_database: str = "DBC"
) -> List[Dict[str, str]]:
    query_columns = f"""
    SELECT ColumnName, ColumnType
    FROM {system_database}.ColumnsV
    WHERE DatabaseName = '{database_name}'
        AND TableName = '{table_name}'
    """
    logger.debug(f"Executing query to retrieve columns for {database_name}.{table_name}.")
    logger.debug(f"Query: {query_columns}")
    columns = execute_query(query_columns, conn)
    logger.debug(f"Retrieved columns: {columns}")
    return columns


@error_handling_decorator
def execute_query(query: str, con: teradatasql.connect) -> List[Dict[str, Any]]:
    try:
        with con.cursor() as cur:
            logger.debug(f"Executing SQL query: {query}")
            cur.execute(query)
            logger.debug(f"Column descriptions: {cur.description}")
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            logger.debug(f"Fetched {len(rows)} rows from Teradata.")
            return rows
    except teradatasql.OperationalError as e:
        logger.error(f"Teradata Operational Error: {e}")
        raise
    except teradatasql.ProgrammingError as e:
        logger.error(f"Teradata Programming Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching data from Teradata: {e}")
        raise
