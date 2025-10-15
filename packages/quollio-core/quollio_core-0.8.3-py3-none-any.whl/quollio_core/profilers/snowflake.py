import io
import logging
import os
from typing import Dict, List

from fastavro import writer

from quollio_core.helper.core import new_global_id
from quollio_core.models.avroasset import AvroAsset
from quollio_core.models.qdc import GetImportURLRequest
from quollio_core.profilers.lineage import (
    gen_column_avro_lineage_payload,
    gen_table_avro_lineage_payload,
    parse_snowflake_results,
)
from quollio_core.profilers.sqllineage import SQLLineage
from quollio_core.profilers.stats import gen_table_stats_avro_payload, get_is_target_stats_items, render_sql_for_stats
from quollio_core.repository import qdc, snowflake

logger = logging.getLogger(__name__)


def snowflake_table_to_table_lineage(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
    existing_global_ids: Dict[str, bool],
) -> None:
    with snowflake.SnowflakeQueryExecutor(conn) as sf_executor:
        results, err = sf_executor.get_query_results(
            query="""
            SELECT
                *
            FROM
               {db}.{schema}.QUOLLIO_LINEAGE_TABLE_LEVEL
            """.format(
                db=conn.account_database,
                schema=conn.account_schema,
            )
        )
        if err is not None:
            handle_error(err=err)
        if len(results) == 0:
            logger.warning(
                "No lineage data in ACCOUNT_USAGE.SNOWFLAKE. Please check the data in `QUOLLIO_LINEAGE_TABLE_LEVEL`."
            )
            return
        parsed_results = parse_snowflake_results(results=results)
        update_table_lineage_inputs = gen_table_avro_lineage_payload(
            tenant_id=tenant_id,
            endpoint=conn.account_id,
            tables=parsed_results,
            existing_global_ids=existing_global_ids,
        )
        stack_name = os.getenv("CF_STACK")
        import_req = GetImportURLRequest(
            service_name="snowflake",
            source_name=stack_name,
            file_name="{name}.avro".format(name=stack_name),
            override_logical_name="false",
            update_mode="partial",
        )
        datasource_id = new_global_id(
            tenant_id=tenant_id, cluster_id=conn.account_id, data_id="", data_type="data_source"
        )
        logger.debug("Datasource id: {dsrc_id}".format(dsrc_id=datasource_id))
        import_res = qdc_client.get_import_url(datasource_id=datasource_id, payload=import_req)
        if import_res is None:
            logger.error("get_import_url failed. Please retry `load_lineage` again")
            return
        logger.debug("ImportResponse: {res}".format(res=import_res))

        avro_schema = AvroAsset.avro_schema_to_python()

        buffer = io.BytesIO()
        writer(buffer, avro_schema, update_table_lineage_inputs)
        res = qdc_client.upload_file(
            url=import_res.location,
            metadata=import_res.datasource_metadata_response_body,
            buffer=buffer.getbuffer().tobytes(),
        )
        if res == 200:
            logger.info("Upload table lineage is finished.")
    return


def snowflake_column_to_column_lineage(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
    existing_global_ids: Dict[str, bool],
) -> None:
    with snowflake.SnowflakeQueryExecutor(conn) as sf_executor:
        results, err = sf_executor.get_query_results(
            query="""
            SELECT
                *
            FROM
                {db}.{schema}.QUOLLIO_LINEAGE_COLUMN_LEVEL
            """.format(
                db=conn.account_database,
                schema=conn.account_schema,
            )
        )
        if err is not None:
            handle_error(err=err)
        if len(results) == 0:
            logger.warning(
                "No lineage data in ACCOUNT_USAGE.SNOWFLAKE. Please check the data in `QUOLLIO_LINEAGE_COLUMN_LEVEL`."
            )
            return
        update_column_lineage_inputs = gen_column_avro_lineage_payload(
            tenant_id=tenant_id, endpoint=conn.account_id, columns=results, existing_global_ids=existing_global_ids
        )

        stack_name = os.getenv("CF_STACK")
        import_req = GetImportURLRequest(
            service_name="snowflake",
            source_name=stack_name,
            file_name="{name}.avro".format(name=stack_name),
            override_logical_name="false",
            update_mode="partial",
        )
        datasource_id = new_global_id(
            tenant_id=tenant_id, cluster_id=conn.account_id, data_id="", data_type="data_source"
        )
        logger.debug("Datasource id: {dsrc_id}".format(dsrc_id=datasource_id))
        import_res = qdc_client.get_import_url(datasource_id=datasource_id, payload=import_req)
        if import_res is None:
            logger.error("get_import_url failed. Please retry load_lineage again")
            return
        logger.debug("ImportResponse: {res}".format(res=import_res))

        avro_schema = AvroAsset.avro_schema_to_python()

        buffer = io.BytesIO()
        writer(buffer, avro_schema, update_column_lineage_inputs)
        res = qdc_client.upload_file(
            url=import_res.location,
            metadata=import_res.datasource_metadata_response_body,
            buffer=buffer.getbuffer().tobytes(),
        )
        if res == 200:
            logger.info("Upload column lineage is finished.")
    return


def snowflake_table_level_sqllineage(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
) -> None:
    with snowflake.SnowflakeQueryExecutor(conn) as sf_executor:
        results, err = sf_executor.get_query_results(
            query="""
            SELECT
                database_name
                , schema_name
                , query_text
            FROM
               {db}.{schema}.QUOLLIO_SQLLINEAGE_SOURCES
            """.format(
                db=conn.account_database,
                schema=conn.account_schema,
            )
        )
        if err is not None:
            handle_error(err=err)
        if len(results) == 0:
            logger.warning(
                "No lineage data in ACCOUNT_USAGE.SNOWFLAKE. Please check the data in `QUOLLIO_SQLLINEAGE_SOURCES`."
            )
            return
        update_table_lineage_inputs_list = list()
        sql_lineage = SQLLineage()
        for result in results:
            src_tables, dest_table = sql_lineage.get_table_level_lineage_source(
                sql=result["QUERY_TEXT"],
                dialect="snowflake",
                dest_db=result["DATABASE_NAME"],
                dest_schema=result["SCHEMA_NAME"],
            )
            update_table_lineage_inputs = sql_lineage.gen_lineage_input(
                tenant_id=tenant_id, endpoint=conn.account_id, src_tables=src_tables, dest_table=dest_table
            )
            update_table_lineage_inputs_list.append(update_table_lineage_inputs)

        req_count = 0
        for update_table_lineage_input in update_table_lineage_inputs_list:
            logger.info(
                "Generating table lineage. downstream: {db} -> {schema} -> {table}".format(
                    db=update_table_lineage_input.downstream_database_name,
                    schema=update_table_lineage_input.downstream_schema_name,
                    table=update_table_lineage_input.downstream_table_name,
                )
            )
            status_code = qdc_client.update_lineage_by_id(
                global_id=update_table_lineage_input.downstream_global_id,
                payload=update_table_lineage_input.upstreams.as_dict(),
            )
            if status_code == 200:
                req_count += 1
        logger.info(f"Generating table lineage is finished. {req_count} lineages are ingested.")
    return


def snowflake_table_stats(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
    stats_items: List[str],
    existing_global_ids: Dict[str, bool],
) -> None:
    with snowflake.SnowflakeQueryExecutor(conn) as sf_executor:
        get_stats_view_query = _gen_get_stats_views_query(
            db=conn.account_database,
            schema=conn.account_schema,
        )
        stats_views, err = sf_executor.get_query_results(query=get_stats_view_query)
        if err is not None:
            handle_error(err=err)
        if len(stats_views) == 0:
            logger.warning(
                f"No target table for stats aggregation. Please see the error message above \
and fix it or grant usage permission to both `{conn.account_database}` and `{conn.account_schema}` \
and select permissions to views begins with `QUOLLIO_STATS_COLUMNS_`."
            )
            return
        is_aggregate_items = get_is_target_stats_items(stats_items=stats_items)
        update_stats_inputs = list()
        for stats_view in stats_views:
            table_fqn = '"{catalog}"."{schema}"."{table}"'.format(
                catalog=stats_view["TABLE_CATALOG"], schema=stats_view["TABLE_SCHEMA"], table=stats_view["TABLE_NAME"]
            )
            stats_query = render_sql_for_stats(is_aggregate_items=is_aggregate_items, table_fqn=table_fqn)
            logger.debug(f"The following sql will be fetched to retrieve stats values. {stats_query}")
            stats_result, err = sf_executor.get_query_results(query=stats_query)
            if err is not None:
                handle_error(err=err, force_skip=True)
            if len(stats_result) == 0:
                logger.warning(
                    f"No stats value. Please query {table_fqn} to check the value exists in it \
or user has select permission to it."
                )
                continue
            payloads = gen_table_stats_avro_payload(
                tenant_id=tenant_id,
                endpoint=conn.account_id,
                stats=stats_result,
                existing_global_ids=existing_global_ids,
            )
            update_stats_inputs += payloads

        stack_name = os.getenv("CF_STACK")
        import_req = GetImportURLRequest(
            service_name="snowflake",
            source_name=stack_name,
            file_name="{name}.avro".format(name=stack_name),
            override_logical_name="false",
            update_mode="partial",
        )
        datasource_id = new_global_id(
            tenant_id=tenant_id, cluster_id=conn.account_id, data_id="", data_type="data_source"
        )
        logger.debug("Datasource id: {dsrc_id}".format(dsrc_id=datasource_id))
        import_res = qdc_client.get_import_url(datasource_id=datasource_id, payload=import_req)
        if import_res is None:
            logger.error("get_import_url failed. Please retry load_stats again")
            return
        logger.debug("ImportResponse: {res}".format(res=import_res))

        avro_schema = AvroAsset.avro_schema_to_python()

        buffer = io.BytesIO()
        writer(buffer, avro_schema, update_stats_inputs)
        res = qdc_client.upload_file(
            url=import_res.location,
            metadata=import_res.datasource_metadata_response_body,
            buffer=buffer.getbuffer().tobytes(),
        )
        if res == 200:
            logger.info("Generating table stats is finished.")
    return


def _gen_get_stats_views_query(db: str, schema: str) -> str:
    query = """
        SELECT
            DISTINCT
            TABLE_CATALOG
            , TABLE_SCHEMA
            , TABLE_NAME
        FROM
            {db}.INFORMATION_SCHEMA.TABLES
        WHERE
            startswith(TABLE_NAME, 'QUOLLIO_STATS_COLUMNS_')
            AND TABLE_SCHEMA = UPPER('{schema}')
        """.format(
        db=db, schema=schema
    )
    return query


def handle_error(err: Exception, force_skip: bool = False):
    if err.errno == 2037:
        logger.warning(
            "snowflake get_query_results failed. The table you query exists but user doesn't have permission to select.\
Please check a user has select or ownership permissions. ErrorNo: {0} SQLState: {1} Message: {2} SfqID: {3}".format(
                err.errno, err.sqlstate, err.msg, err.sfqid
            )
        )
        return
    elif err.errno == 2003:
        logger.warning(
            "snowflake get_query_results failed. User doesn't have select permission to the object \
or the object you query doesn't exist.\
Please check a user has select or ownership permissions and whether the object exists or not. \
ErrorNo: {0} SQLState: {1} Message: {2} SfqID: {3}".format(
                err.errno, err.sqlstate, err.msg, err.sfqid
            )
        )
        return
    else:
        logger.error(
            "snowflake get_query_results failed.\
Please check ErrNo and message. ErrorNo: {0} SQLState: {1} Message: {2} SfqID: {3}".format(
                err.errno, err.sqlstate, err.msg, err.sfqid
            )
        )
        if not force_skip:
            raise Exception
        return
