import argparse
import json

from google.auth.credentials import Credentials

from quollio_core.helper.core import is_valid_domain
from quollio_core.helper.env_default import env_default
from quollio_core.helper.log_utils import configure_logging, error_handling_decorator, logger
from quollio_core.profilers.bigquery import bigquery_table_lineage, bigquery_table_stats
from quollio_core.profilers.qdc import gen_existing_global_id_dict, get_avro_file_content
from quollio_core.repository import qdc, ssm
from quollio_core.repository.bigquery import BigQueryClient, get_credentials, get_org_id


def initialize_credentials(credentials_json: str) -> Credentials:
    return get_credentials(json.loads(credentials_json))


def initialize_org_id(credentials_json: str) -> str:
    return get_org_id(json.loads(credentials_json))


def initialize_bq_client(credentials: Credentials, project_id: str) -> BigQueryClient:
    return BigQueryClient(credentials=credentials, project_id=project_id)


@error_handling_decorator
def load_lineage(
    tenant_id: str,
    project_id: str,
    regions: list,
    org_id: str,
    credentials: Credentials,
    qdc_client: qdc.QDCExternalAPIClient,
    enable_multi_projects: str,
) -> None:
    logger.info("Loading lineage data.")
    file_content = get_avro_file_content(
        tenant_id=tenant_id,
        account_id=org_id,
        qdc_client=qdc_client,
    )
    existing_global_ids = gen_existing_global_id_dict(avro_content=file_content)
    bigquery_table_lineage(
        qdc_client=qdc_client,
        tenant_id=tenant_id,
        project_id=project_id,
        regions=regions,
        credentials=credentials,
        org_id=org_id,
        existing_global_ids=existing_global_ids,
        enable_multi_projects=enable_multi_projects,
    )
    logger.info("Lineage data loaded successfully.")


@error_handling_decorator
def load_stats(
    conn: BigQueryClient,
    tenant_id: str,
    org_id: str,
    qdc_client: qdc.QDCExternalAPIClient,
    dataplex_stats_tables: list,
) -> None:
    logger.info("Loading statistics data.")
    file_content = get_avro_file_content(
        tenant_id=tenant_id,
        account_id=org_id,
        qdc_client=qdc_client,
    )
    existing_global_ids = gen_existing_global_id_dict(avro_content=file_content)
    bigquery_table_stats(
        bq_client=conn,
        qdc_client=qdc_client,
        tenant_id=tenant_id,
        org_id=org_id,
        dataplex_stats_tables=dataplex_stats_tables,
        existing_global_ids=existing_global_ids,
    )
    logger.info("Statistics data loaded successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Quollio Intelligence Agent for BigQuery",
        description="Load lineage and stats to Quollio from BigQuery using Dataplex and BigQuery APIs",
        epilog="Copyright (c) 2024 Quollio Technologies, Inc.",
    )
    parser.add_argument(
        "commands",
        choices=["load_lineage", "load_stats"],
        type=str,
        nargs="+",
        help="""
        The command to execute.
        'load_lineage': Load lineage data from created views to Quollio,
        'load_stats': Load stats from created views to Quollio,
        """,
    )
    parser.add_argument(
        "--log_level",
        type=str,
        choices=["debug", "info", "warn", "error", "none"],
        action=env_default("LOG_LEVEL"),
        default="info",
        required=False,
        help="The log level for dbt commands. Default value is info",
    )
    parser.add_argument(
        "--tenant_id",
        type=str,
        action=env_default("TENANT_ID"),
        required=False,
        help="The tenant id (company id) where the lineage and stats are loaded",
    )
    parser.add_argument(
        "--project_id",
        type=str,
        default=None,
        required=False,
        help="Project ID of the BigQuery project to load lineage and stats from (default is loaded from credentials)",
    )
    parser.add_argument(
        "--regions",
        type=str,
        action=env_default("GCP_REGIONS"),
        required=True,
        help="Comma-separated list of regions BigQuery data is in",
    )
    parser.add_argument(
        "--credentials_json",
        type=str,
        action=env_default("GOOGLE_APPLICATION_CREDENTIALS"),
        required=True,
        help="Credentials JSON",
    )
    parser.add_argument(
        "--api_url",
        type=str,
        action=env_default("QDC_API_URL"),
        required=False,
        help="The base URL of Quollio External API",
    )
    parser.add_argument(
        "--client_id",
        type=str,
        action=env_default("QDC_CLIENT_ID"),
        required=False,
        help="The client id that is created on Quollio console to let clients access Quollio External API",
    )
    parser.add_argument(
        "--client_secret",
        type=str,
        action=env_default("QDC_CLIENT_SECRET"),
        required=False,
        help="The client secret that is created on Quollio console to let clients access Quollio External API",
    )

    parser.add_argument(
        "--dataplex_stats_tables",
        type=str,
        action=env_default("DATAPLEX_STATS_TABLES"),
        required=False,
        help="Comma-separated list of dataplex stats tables - <project_id>.<dataset_id>.<table_id>",
    )

    parser.add_argument(
        "--enable_multi_projects",
        type=str,
        choices=["ENABLED", "DISABLED"],
        action=env_default("ENABLE_MULTI_PROJECTS"),
        default="DISABLED",
        required=False,
        help="Whether to enable multi-projects support. If set to 'true', \
        the script will load lineage and stats from all projects accessible by the credentials. Default is 'false'.",
    )
    parser.add_argument(
        "--external_api_access",
        type=str,
        choices=["PUBLIC", "VPC_ENDPOINT"],
        action=env_default("EXTERNAL_API_ACCESS"),
        default="PUBLIC",
        required=False,
        help="Access method to Quollio API. Default 'PUBLIC'. Choose 'VPC_ENDPOINT'\
             if you use API Gateway VPC Endpoint, DefaultValue is set to PUBLIC.",
    )

    args = parser.parse_args()

    # Validate that dataplex_stats_tables is provided if load_stats is in commands
    if "load_stats" in args.commands and not args.dataplex_stats_tables:
        parser.error("--dataplex_stats_tables is required when 'load_stats' command is used")

    configure_logging(args.log_level)

    api_url = args.api_url
    if args.external_api_access == "VPC_ENDPOINT":
        logger.debug("Using VPC Endpoint for Quollio API access")
        api_url, err = ssm.get_parameter_by_assume_role(args.api_url)
        if err is not None:
            logger.error("Fail to ssm.get_parameter_by_assume_role. {err}".format(err=err))
            raise Exception("Fail to ssm.get_parameter_by_assume_role. {err}".format(err=err))
    is_domain_valid = is_valid_domain(domain=api_url, domain_type=args.external_api_access)
    if not is_domain_valid:
        raise ValueError("The format of quollio API URL is invalid. The URL must end with `.com` or /api.")
    logger.debug("API URL: %s", api_url)

    credentials = initialize_credentials(args.credentials_json)
    org_id = initialize_org_id(args.credentials_json)
    qdc_client = qdc.initialize_qdc_client(api_url, args.client_id, args.client_secret)
    bq_client = initialize_bq_client(credentials, args.project_id)
    if args.project_id is None:
        args.project_id = json.loads(args.credentials_json)["project_id"]
    regions = args.regions.split(",")

    if "load_lineage" in args.commands:
        load_lineage(
            tenant_id=args.tenant_id,
            project_id=args.project_id,
            regions=regions,
            org_id=org_id,
            credentials=credentials,
            qdc_client=qdc_client,
            enable_multi_projects=args.enable_multi_projects,
        )

    if "load_stats" in args.commands:
        tables = args.dataplex_stats_tables.split(",")
        load_stats(
            conn=bq_client,
            tenant_id=args.tenant_id,
            org_id=org_id,
            qdc_client=qdc_client,
            dataplex_stats_tables=tables,
        )
