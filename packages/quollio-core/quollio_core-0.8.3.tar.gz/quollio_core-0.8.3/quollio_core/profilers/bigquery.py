import io
import os
from typing import Dict, List

from fastavro import writer
from google.auth.credentials import Credentials

from quollio_core.helper.core import new_global_id
from quollio_core.helper.log_utils import error_handling_decorator, logger
from quollio_core.models.avroasset import AvroAsset
from quollio_core.models.qdc import GetImportURLRequest
from quollio_core.profilers.lineage import (
    gen_table_avro_lineage_payload,
    gen_table_lineage_payload,
    parse_bigquery_table_lineage,
)
from quollio_core.profilers.stats import gen_table_stats_avro_payload
from quollio_core.repository import qdc
from quollio_core.repository.bigquery import BigQueryClient, GCPLineageClient, get_entitiy_reference, get_search_request
from quollio_core.repository.cloud_resource_manager import CloudResourceManagerClient


def bigquery_table_lineage(
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
    project_id: str,
    regions: list,
    org_id: str,
    credentials: Credentials,
    existing_global_ids: Dict[str, bool],
    enable_multi_projects: str = "DISABLED",
) -> None:
    lineage_client = GCPLineageClient(credentials)
    crm_client = CloudResourceManagerClient(credentials)

    target_project_ids = []
    if enable_multi_projects == "ENABLED":
        try:
            target_projects = crm_client.list_projects()
        except Exception as e:
            raise Exception(f"ListProjects by cloud resource manager failed. Err. {str(e)}")

        for target_project in target_projects["projects"]:
            if target_project is None:
                logger.warning("projects.Projects returns None. Proceed to loop project value")
                continue

            target_project_id = target_project.get("projectId", "")
            if target_project_id == "":
                logger.warning("projects.Projects is empty string. Proceed to loop project value")
                continue

            target_project_ids.append(target_project_id)
    else:
        target_project_ids.append(project_id)

    update_table_lineage_inputs = []
    for target_project_id in target_project_ids:
        bq_client = BigQueryClient(credentials, target_project_id)
        datasets = bq_client.list_dataset_ids()
        all_tables = generate_table_list(bq_client, datasets)
        lineage_links = generate_lineage_links(all_tables, lineage_client, target_project_id, regions)
        lineage_links = parse_bigquery_table_lineage(lineage_links)
        logger.debug("The following resources will be ingested. %s", lineage_links)

        update_table_lineage_input = gen_table_lineage_payload(
            tenant_id=tenant_id, endpoint=org_id, tables=lineage_links
        )
        update_table_lineage_input = gen_table_avro_lineage_payload(
            tenant_id=tenant_id,
            endpoint=org_id,
            tables=lineage_links,
            existing_global_ids=existing_global_ids,
        )
        update_table_lineage_inputs.extend(update_table_lineage_input)

    stack_name = os.getenv("CF_STACK")
    import_req = GetImportURLRequest(
        service_name="bigquery",
        source_name=stack_name,
        file_name="{name}.avro".format(name=stack_name),
        override_logical_name="false",
        update_mode="partial",
    )
    datasource_id = new_global_id(tenant_id=tenant_id, cluster_id=org_id, data_id="", data_type="data_source")
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


@error_handling_decorator
def bigquery_table_stats(
    qdc_client: qdc.QDCExternalAPIClient,
    bq_client: BigQueryClient,
    tenant_id: str,
    org_id: str,
    dataplex_stats_tables: list,
    existing_global_ids: dict,
) -> None:
    profiling_results = []
    for table in dataplex_stats_tables:
        logger.info("Profiling columns using Dataplex stats table: %s", table)

        profiling_results.extend(column_stats_from_dataplex(bq_client, table))

    latest_results = {}
    for result in profiling_results:
        key = (result.get("DB_NAME"), result.get("SCHEMA_NAME"), result.get("TABLE_NAME"), result.get("COLUMN_NAME"))
        if key not in latest_results:
            latest_results[key] = result
        else:
            existing_created_on = latest_results[key].get("created_on")
            current_created_on = result.get("created_on")

            if current_created_on and (not existing_created_on or current_created_on > existing_created_on):
                latest_results[key] = result

    filtered_results = []
    for result in latest_results.values():
        result_copy = result.copy()
        result_copy.pop("created_on", None)
        filtered_results.append(result_copy)

    update_stats_inputs = gen_table_stats_avro_payload(tenant_id, org_id, filtered_results, existing_global_ids)

    stack_name = os.getenv("CF_STACK")
    import_req = GetImportURLRequest(
        service_name="bigquery",
        source_name=stack_name,
        file_name="{name}.avro".format(name=stack_name),
        override_logical_name="false",
        update_mode="partial",
    )
    datasource_id = new_global_id(tenant_id=tenant_id, cluster_id=org_id, data_id="", data_type="data_source")

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


def generate_table_list(bq_client: BigQueryClient, datasets: List[str]) -> List[str]:
    all_tables = []
    for dataset in datasets:
        all_tables.extend(
            [
                table
                for table in bq_client.list_tables(dataset)
                if table["table_type"] in ["TABLE", "VIEW", "MATERIALIZED_VIEW"]
            ],
        )

    all_table_names = []
    for table in all_tables:
        all_table_names.append(f"{bq_client.client.project}.{table['dataset_id']}.{table['table_id']}")

    return all_table_names


def generate_lineage_links(
    all_tables: List[str],
    lineage_client: GCPLineageClient,
    project_id: str,
    regions: List[str],
) -> Dict[str, List[str]]:
    lineage_links = {}
    for table in all_tables:
        if "quollio" in table.lower():
            continue
        downstream = get_entitiy_reference()
        downstream.fully_qualified_name = f"bigquery:{table}"

        for region in regions:
            request = get_search_request(downstream_table=downstream, project_id=project_id, region=region)
            response = lineage_client.get_links(request=request)
            for lineage in response:
                target_table = str(lineage.target.fully_qualified_name).replace("bigquery:", "")
                source_table = str(lineage.source.fully_qualified_name).replace("bigquery:", "")
                if target_table not in lineage_links:
                    lineage_links[target_table] = []
                if source_table not in lineage_links[target_table]:
                    lineage_links[target_table].append(source_table)

    return lineage_links


def column_stats_from_dataplex(bq_client: BigQueryClient, profiling_table: str) -> List[Dict]:
    query = f"""
    WITH ranked_data AS (
        SELECT
            data_source.table_project_id AS DB_NAME,
            data_source.dataset_id AS SCHEMA_NAME,
            data_source.table_id AS TABLE_NAME,
            column_name AS COLUMN_NAME,
            min_value AS MIN_VALUE,
            max_value AS MAX_VALUE,
            average_value AS AVG_VALUE,
            quartile_median AS MEDIAN_VALUE,
            standard_deviation AS STDDEV_VALUE,
            top_n[SAFE_OFFSET(0)][SAFE_OFFSET(0)] AS MODE_VALUE,
            CAST((percent_null / 100) * job_rows_scanned AS INT) as NULL_COUNT,
            CAST((percent_unique / 100) * job_rows_scanned AS INT) as CARDINALITY,
            created_on,
            ROW_NUMBER() OVER (
              PARTITION BY
                data_source.table_project_id,
                data_source.dataset_id,
                data_source.table_id,
                column_name
              ORDER BY created_on DESC) AS rank
        FROM `{profiling_table}`
    )
    SELECT * except(rank)
    FROM ranked_data
    WHERE rank = 1
    """
    logger.debug(f"Executing Query: {query}")
    results = bq_client.client.query(query).result()

    # Convert RowIterator to a list of dictionaries
    return [dict(row) for row in results]
