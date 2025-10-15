import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.connector import DictCursor, connect, errors
from snowflake.connector.connection import SnowflakeConnection

logger = logging.getLogger(__name__)


@dataclass
class SnowflakeConnectionConfig:
    account_id: str
    account_user: str
    account_build_role: str
    account_query_role: str
    account_warehouse: str
    account_database: str
    account_schema: str
    account_password: str = None
    private_key: str = None
    threads: int = 3

    def as_dict(self) -> Dict[str, str]:
        """Convert config to dictionary, handling both auth methods for DBT."""
        base_params = {
            "account_id": self.account_id,
            "account_user": self.account_user,
            "account_build_role": self.account_build_role,
            "account_query_role": self.account_query_role,
            "account_warehouse": self.account_warehouse,
            "account_database": self.account_database,
            "account_schema": self.account_schema,
            "threads": self.threads,
        }

        # Add auth parameters based on method
        if self.private_key:
            # Keep private key as is, template will handle formatting
            base_params["private_key"] = self.private_key
        elif self.account_password:
            base_params["account_password"] = self.account_password

        return {k: v for k, v in base_params.items() if v is not None}

    def get_connection_params(self) -> Dict[str, str]:
        """Get the appropriate connection parameters based on authentication method."""
        params = {
            "user": self.account_user,
            "account": self.account_id,
            "warehouse": self.account_warehouse,
            "database": self.account_database,
            "schema": self.account_schema,
            "role": self.account_query_role,
        }

        # Add authentication parameters based on method
        if self.private_key:
            try:
                # Parse private key content into RSA key object
                pkey = serialization.load_pem_private_key(
                    self.private_key.encode("utf-8"),
                    password=None,
                    backend=default_backend(),
                )
                params["private_key"] = pkey
            except Exception as e:
                logger.error(f"Failed to parse private key: {str(e)}")
                raise
        elif self.account_password:
            params["password"] = self.account_password
        else:
            raise ValueError("Either password or private key authentication must be configured")

        return params


class SnowflakeQueryExecutor:
    def __init__(self, config: SnowflakeConnectionConfig) -> None:
        self.conn = self.__initialize(config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def __initialize(self, config: SnowflakeConnectionConfig) -> SnowflakeConnection:
        try:
            conn: SnowflakeConnection = connect(**config.get_connection_params())
            return conn
        except Exception as e:
            logger.error(f"Failed to initialize Snowflake connection: {str(e)}")
            raise

    def get_query_results(self, query: str) -> Tuple[List[Dict[str, str]], Exception]:
        with self.conn.cursor(DictCursor) as cur:
            try:
                cur.execute(query)
                result: List[Dict[str, str]] = cur.fetchall()
                return (result, None)
            except errors.ProgrammingError as e:
                return ([], e)
            except Exception as e:
                return ([], e)
