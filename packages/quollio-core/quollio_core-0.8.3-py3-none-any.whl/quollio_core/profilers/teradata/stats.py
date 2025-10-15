from typing import Any, Dict, List, Optional

from quollio_core.helper.log_utils import error_handling_decorator, logger
from quollio_core.profilers.stats import gen_table_stats_payload
from quollio_core.repository import qdc
from quollio_core.repository import teradata as teradata_repo

NUMERIC_TYPES = ["D", "F", "I1", "I2", "I8", "I", "N"]

# I, I1, I2, I8 - INT TYPES  INTEGER, BYTEINT, SMALLINT, BIGINT
# F - Float
# D - Decimal
# N - Number


def quote_identifier(identifier: str) -> str:
    return f'"{identifier}"'


@error_handling_decorator
def load_stats(
    conn_config: teradata_repo.TeradataConfig,
    sample_percent: Optional[float] = None,
    endpoint: Optional[str] = None,
    tenant_id: Optional[str] = None,
    qdc_client: Optional[qdc.QDCExternalAPIClient] = None,
    target_databases: Optional[List[str]] = None,
    target_databases_method: str = "DENYLIST",
    stats_items: Optional[List[str]] = None,
    system_database: Optional[str] = None,
) -> None:
    stats_list = []
    numerical_columns = 0
    non_numerical_columns = 0
    logger.info(
        f"Starting statistics collection. " f"Sample percent: {sample_percent if sample_percent is not None else 'N/A'}"
    )

    # Use system_database from config if not provided
    system_database = system_database or conn_config.system_database

    with teradata_repo.new_teradata_client(conn_config) as conn:
        try:
            tables = teradata_repo.get_table_list(conn, target_databases, target_databases_method, system_database)
            for table in tables:
                logger.debug(f"Processing table: {table}")
                database_name = table["DatabaseName"]
                table_name = table["TableName"]

                logger.info(f"Processing table {database_name}.{table_name}")
                columns = teradata_repo.get_column_list(
                    conn, database_name=database_name, table_name=table_name, system_database=system_database
                )
                logger.debug(f"Columns: {columns}")

                for column in columns:
                    column_name = column["ColumnName"]
                    column_type = column["ColumnType"]
                    if column_type is None:
                        column_type = ""
                    else:
                        column_type = column_type.strip()

                    is_numerical = column_type in NUMERIC_TYPES
                    if is_numerical:
                        numerical_columns += 1
                    else:
                        non_numerical_columns += 1

                    stats_sql = generate_column_statistics_sql(
                        database_name,
                        table_name,
                        column_name,
                        column_type,
                        sample_percent if is_numerical else None,
                        stats_items,
                    )
                    logger.debug(f"Generated SQL for column {column_name}: {stats_sql}")

                    try:
                        result = teradata_repo.execute_query(stats_sql, conn)
                        logger.debug(f"Query result for column {column_name}: {result}")
                        if result:
                            column_stats = parse_column_statistics_result(
                                result[0], database_name, table_name, column_name, stats_items, is_numerical
                            )
                            stats_list.append(column_stats)
                    except Exception as e:
                        logger.error(
                            f"Failed to collect statistics for {database_name}.{table_name}.{column_name}: {e}"
                        )

        except Exception as e:
            logger.error(f"Error during statistics collection: {e}")

        logger.info("Statistics collection completed successfully.")

    logger.debug(f"Stats list: {stats_list}")
    payloads = gen_table_stats_payload(stats=stats_list, tenant_id=tenant_id, endpoint=endpoint)
    logger.debug(f"Generated payloads: {payloads}")

    req_count = 0
    for payload in payloads:
        logger.info(f"Generating table stats. asset: {payload.db} -> {payload.table} -> {payload.column}")
        status_code = qdc_client.update_stats_by_id(
            global_id=payload.global_id,
            payload=payload.body.get_column_stats(),
        )
        if status_code == 200:
            req_count += 1

    logger.info(
        f"Loading statistics is finished. {req_count} statistics are ingested. "
        f"Numerical columns: {numerical_columns}, Non-numerical columns: {non_numerical_columns}"
    )


@error_handling_decorator
def parse_column_statistics_result(
    result: Dict[str, Any],
    database_name: str,
    table_name: str,
    column_name: str,
    stats_items: Optional[List[str]] = None,
    is_numerical: bool = False,
) -> Dict[str, Any]:
    stats_dict = {
        "DB_NAME": database_name,
        "SCHEMA_NAME": "",
        "TABLE_NAME": table_name,
        "COLUMN_NAME": column_name,
    }

    if stats_items:
        for item in stats_items:
            if item == "cardinality" and "num_uniques" in result:
                stats_dict["CARDINALITY"] = result["num_uniques"]
            elif item == "number_of_null" and "num_nulls" in result:
                stats_dict["NULL_COUNT"] = result["num_nulls"]  # Changed from NUM_NULLS to NULL_COUNT

            if is_numerical:
                if item == "min" and "min_value" in result:
                    stats_dict["MIN_VALUE"] = str(result["min_value"])
                elif item == "max" and "max_value" in result:
                    stats_dict["MAX_VALUE"] = str(result["max_value"])
                elif item == "median" and "median_value" in result:
                    stats_dict["MEDIAN_VALUE"] = str(result["median_value"])
                elif item == "mean" and "avg_value" in result:
                    stats_dict["AVG_VALUE"] = str(result["avg_value"])
                elif item == "stddev" and "stddev_value" in result:
                    stats_dict["STDDEV_VALUE"] = str(result["stddev_value"])
                elif item == "mode" and "mode_value" in result and is_numerical:
                    stats_dict["MODE_VALUE"] = str(result["mode_value"])

    return stats_dict


@error_handling_decorator
def generate_column_statistics_sql(
    database_name: str,
    table_name: str,
    column_name: str,
    column_type: str,
    sample_percent: Optional[float] = None,
    stats_items: Optional[List[str]] = None,
) -> str:
    quoted_column = quote_identifier(column_name)
    quoted_database = quote_identifier(database_name)

    # Handle the case where table_name might include a database
    if "." in table_name:
        schema, table = table_name.split(".", 1)
        quoted_table = f"{quote_identifier(schema)}.{quote_identifier(table)}"
    else:
        quoted_table = quote_identifier(table_name)

    stats_clauses = []
    mode_query = ""

    if stats_items:
        if "cardinality" in stats_items:
            stats_clauses.append(f"COUNT(DISTINCT {quoted_column}) AS num_uniques")
        if "number_of_null" in stats_items:
            stats_clauses.append(f"SUM(CASE WHEN {quoted_column} IS NULL THEN 1 ELSE 0 END) AS num_nulls")

        if column_type in NUMERIC_TYPES:
            if "min" in stats_items:
                stats_clauses.append(f"MIN(CAST({quoted_column} AS FLOAT)) AS min_value")
            if "max" in stats_items:
                stats_clauses.append(f"MAX(CAST({quoted_column} AS FLOAT)) AS max_value")
            if "median" in stats_items:
                stats_clauses.append(f"MEDIAN(CAST({quoted_column} AS FLOAT)) AS median_value")
            if "mean" in stats_items:
                stats_clauses.append(f"AVG(CAST({quoted_column} AS FLOAT)) AS avg_value")
            if "stddev" in stats_items:
                stats_clauses.append(f"STDDEV_SAMP(CAST({quoted_column} AS FLOAT)) AS stddev_value")
            if "mode" in stats_items:
                mode_query = (
                    f"WITH MODE_VALUE AS ("
                    f"    SELECT {quoted_column}, COUNT(*) as freq "
                    f"    FROM {quoted_database}.{quoted_table} "
                )

                if sample_percent is not None and 0 < sample_percent <= 99:
                    sample_fraction = sample_percent / 100
                    mode_query += f" SAMPLE {sample_fraction} "

                mode_query += (
                    f"    GROUP BY {quoted_column} " f" QUALIFY ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) = 1" f") "
                )
                stats_clauses.append(f"(SELECT {quoted_column} FROM MODE_VALUE) AS mode_value")

    if not stats_clauses:
        logger.warning(f"No statistics selected for column {column_name}. Skipping this column.")
        return ""

    query = f"{mode_query}" f"SELECT {', '.join(stats_clauses)} " f"FROM {quoted_database}.{quoted_table}"

    if sample_percent is not None and 0 < sample_percent <= 99:
        sample_fraction = sample_percent / 100
        query += f" SAMPLE {sample_fraction}"

    logger.debug(f"Generated SQL query for {quoted_database}.{quoted_table}.{quoted_column}: {query}")
    return query
