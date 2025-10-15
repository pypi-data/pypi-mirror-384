import os
from collections import OrderedDict
from typing import Dict, List, Set, Tuple, Union

from sqlglot import ParseError

from quollio_core.helper.log_utils import error_handling_decorator, logger
from quollio_core.profilers.sqllineage import SQLLineage, Table
from quollio_core.repository import qdc
from quollio_core.repository import teradata as teradata_repo


@error_handling_decorator
def load_lineage(
    conn_config: teradata_repo.TeradataConfig,
    endpoint: str = None,
    tenant_id: str = None,
    qdc_client: qdc.QDCExternalAPIClient = None,
    page_size: int = None,
    system_database: str = None,
) -> None:
    page_size = page_size or int(os.environ.get("TERADATA_PAGE_SIZE", 1000))
    offset = 0
    all_lineage_results = []

    # Use system_database from config if not provided
    system_database = system_database or conn_config.system_database

    with teradata_repo.new_teradata_client(conn_config) as conn:
        while True:
            query = f"""
                SELECT
                    a.QueryID,
                    TRIM(a.SqlTextInfo) AS SqlTextInfo,
                    a.SqlRowNo,
                    TRIM(d.DatabaseName) AS DefaultDatabase
                FROM {system_database}.QryLogSQLV a
                JOIN {system_database}.QryLogV b
                    ON a.QueryID = b.QueryID
                JOIN {system_database}.DatabasesV d
                    ON b.DefaultDatabase = d.DatabaseName
                WHERE
                    UPPER(TRIM(SqlTextInfo)) LIKE 'CREATE TABLE%'
                    OR UPPER(TRIM(SqlTextInfo)) LIKE 'CREATE VIEW%'
                    OR UPPER(TRIM(SqlTextInfo)) LIKE 'INSERT%'
                    OR UPPER(TRIM(SqlTextInfo)) LIKE 'MERGE%'
                    OR UPPER(TRIM(SqlTextInfo)) LIKE 'UPDATE%'
                QUALIFY ROW_NUMBER() OVER (ORDER BY a.QueryID, a.SqlRowNo) > {offset}
                    AND ROW_NUMBER() OVER (ORDER BY a.QueryID, a.SqlRowNo) <= {offset + page_size}
            """

            rows = teradata_repo.execute_query(query, conn)
            if not rows:
                break

            logger.info(f"Concatenating split queries for page {offset // page_size + 1}...")
            concatenated_queries = concatenate_split_queries(rows)

            logger.info("Processing SQL statements and extracting lineage...")
            lineage_results = process_sql_statements(concatenated_queries)
            all_lineage_results.extend(lineage_results)

            if len(rows) < page_size:
                break

            offset += page_size

    logger.info(f"Lineage extraction complete. Found {len(all_lineage_results)} unique entries.")
    for entry in all_lineage_results:
        if len(entry) > 1:
            logger.debug(f"Destination table: {entry[1]}")
        else:
            logger.debug("Destination table: Not available (out of bounds)")

        if len(entry) > 0 and isinstance(entry[0], list):
            logger.debug("Source tables:")
            for src_table in entry[0]:
                logger.debug(f"  - {src_table}")
        else:
            logger.debug("Source tables: Not available (out of bounds or invalid type)")

        logger.debug("---")

    sql_lineage = SQLLineage()
    update_table_lineage_inputs = [
        sql_lineage.gen_lineage_input(
            tenant_id=tenant_id, endpoint=endpoint, src_tables=src_tables, dest_table=dest_table
        )
        for src_tables, dest_table in all_lineage_results
    ]

    table_req_count = 0
    logger.info(f"Starting to update lineage information for {len(update_table_lineage_inputs)} tables.")
    for update_table_lineage_input in update_table_lineage_inputs:
        logger.info(
            f"Generating table lineage. downstream: {update_table_lineage_input.downstream_database_name}"
            f" -> {update_table_lineage_input.downstream_table_name}"
        )
        try:
            status_code = qdc_client.update_lineage_by_id(
                global_id=update_table_lineage_input.downstream_global_id,
                payload=update_table_lineage_input.upstreams.as_dict(),
            )
            if status_code == 200:
                table_req_count += 1
            else:
                logger.error(
                    f"Failed to update lineage for {update_table_lineage_input.downstream_table_name}.\
                        Status code: {status_code}"
                )
        except Exception as e:
            logger.error(
                f"Exception occurred while updating lineage for {update_table_lineage_input.downstream_table_name}: {e}"
            )
    logger.info(f"Generating table lineage is finished. {table_req_count} lineages are ingested.")


@error_handling_decorator
def extract_lineage(sql_statement: str, default_database: str = None) -> Tuple[Set[Table], Table]:
    try:
        logger.debug(f"Parsing SQL: {sql_statement}")
        sql_lineage = SQLLineage()
        source_tables, dest_table = sql_lineage.get_table_level_lineage_source(sql=sql_statement, dialect="teradata")

        source_tables = {Table(db=t.db_schema or default_database, db_schema="", table=t.table) for t in source_tables}
        dest_table = Table(db=dest_table.db_schema or default_database, db_schema="", table=dest_table.table)

        return source_tables, dest_table
    except ParseError as e:
        logger.error(f"Error parsing SQL: {e}")
        logger.debug(f"Problematic SQL: {sql_statement}")
    except AttributeError as e:
        logger.error(f"Attribute error while extracting lineage: {e}")
        logger.debug(f"Problematic SQL: {sql_statement}")
    except Exception as e:
        logger.error(f"Unexpected error while extracting lineage: {e}")
        logger.debug(f"Problematic SQL: {sql_statement}")
    return set(), Table(db="", table="")


@error_handling_decorator
def process_sql_statements(queries: List[Union[str, Dict[str, Union[str, int]]]]) -> List[Tuple[Set[Table], Table]]:
    lineage_dict = OrderedDict()
    for query in queries:
        if isinstance(query, str):
            sql = query
            default_database = None
        else:
            sql = query["SqlTextInfo"]
            default_database = query.get("DefaultDatabase")

        source_tables, dest_table = extract_lineage(sql, default_database)
        if dest_table.table and source_tables:
            if dest_table in lineage_dict:
                logger.info(f"Merging duplicate entry for {dest_table}")
                # Merge source tables
                lineage_dict[dest_table] = lineage_dict[dest_table].union(source_tables)
            else:
                lineage_dict[dest_table] = source_tables
    return [(src_tables, dest_table) for dest_table, src_tables in lineage_dict.items()]


def concatenate_split_queries(rows: List[Dict[str, Union[str, int]]]) -> List[Dict[str, Union[str, int]]]:
    queries = {}
    for row in rows:
        query_id = row["QueryID"]
        sql_text = row["SqlTextInfo"]
        default_database = row["DefaultDatabase"]
        if query_id not in queries:
            queries[query_id] = {"SqlTextInfo": [], "DefaultDatabase": default_database}
        queries[query_id]["SqlTextInfo"].append(sql_text)

    return [
        {"SqlTextInfo": "".join(query["SqlTextInfo"]), "DefaultDatabase": query["DefaultDatabase"]}
        for query in queries.values()
    ]
