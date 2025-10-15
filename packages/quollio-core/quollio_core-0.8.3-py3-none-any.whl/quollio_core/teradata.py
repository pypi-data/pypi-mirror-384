import argparse
import json

from quollio_core.helper.core import is_valid_domain
from quollio_core.helper.env_default import env_default
from quollio_core.helper.log_utils import configure_logging, error_handling_decorator, logger
from quollio_core.profilers.stats import get_column_stats_items
from quollio_core.profilers.teradata.lineage import load_lineage
from quollio_core.profilers.teradata.stats import load_stats
from quollio_core.repository import qdc, ssm
from quollio_core.repository import teradata as teradata_repo

DEFAULT_SYSTEM_DATABASES = [
    "DBC",
    "GLOBAL_FUNCTIONS",
    "gs_tables_db",
    "modelops",
    "system",
    "tapidb",
    "TDaaS_BAR",
    "TDaaS_DB",
    "TDaaS_Maint",
    "TDaaS_Monitor",
    "TDaaS_Support",
    "TDaaS_TDBCMgmt1",
    "TDaaS_TDBCMgmt2",
    "TDBCMgmt",
    "Crashdumps",
    "dbcmngr",
    "DemoNow_Monitor",
    "External_AP",
    "LockLogShredder",
    "mldb",
    "SQLJ",
    "SysAdmin",
    "SYSBAR",
    "SYSJDBC",
    "SYSLIB",
    "SYSSPATIAL",
    "SystemFe",
    "SYSUDTLIB",
    "SYSUIF",
    "Sys_Calendar",
    "TDMaps",
    "TDPUSER",
    "TDQCD",
    "TDStats",
    "tdwm",
    "TD_ANALYTICS_DB",
    "TD_SERVER_DB",
    "TD_SYSFNLIB",
    "TD_SYSGPL",
    "TD_SYSXML",
    "val",
]


@error_handling_decorator
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Quollio Intelligence Agent for Teradata",
        description="Load lineage and stats to Quollio from Teradata",
        epilog="Copyright (c) 2024 Quollio Technologies, Inc.",
    )
    parser.add_argument(
        "commands",
        choices=["load_lineage", "load_stats"],
        type=str,
        nargs="+",
        help="""
        The command to execute.
        'load_lineage': Load lineage data from Teradata to Quollio,
        'load_stats': Load stats from Teradata to Quollio
        """,
    )
    parser.add_argument(
        "--log_level",
        type=str,
        choices=["debug", "info", "warn", "error", "none"],
        action=env_default("LOG_LEVEL"),
        default="info",
        required=False,
        help="The log level for commands. Default value is info",
    )
    parser.add_argument(
        "--tenant_id",
        type=str,
        action=env_default("TENANT_ID"),
        required=False,
        help="The tenant id (company id) where the lineage and stats are loaded",
    )
    parser.add_argument(
        "--teradata_host",
        type=str,
        action=env_default("TERADATA_HOST"),
        required=True,
        help="Teradata host",
    )
    parser.add_argument(
        "--teradata_port",
        type=str,
        action=env_default("TERADATA_PORT"),
        required=True,
        help="Teradata port",
    )
    parser.add_argument(
        "--teradata_user",
        type=str,
        action=env_default("TERADATA_USER_NAME"),
        required=True,
        help="Teradata username",
    )
    parser.add_argument(
        "--teradata_password",
        type=str,
        action=env_default("TERADATA_PASSWORD"),
        required=True,
        help="Teradata password",
    )
    parser.add_argument(
        "--teradata_connection_parameters",
        type=str,
        action=env_default("TERADATA_CONNECTION_PARAMETERS"),
        default="{}",
        help="Additional Teradata connection parameters as a JSON string",
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
        "--sample_percent",
        type=float,
        action=env_default("SAMPLE_PERCENT"),
        default=1,
        required=False,
        help="Percentage of data to sample when collecting statistics (e.g., 10 for 10%). Default is 1%.",
    )
    parser.add_argument(
        "--teradata_target_databases",
        type=str,
        action=env_default("TERADATA_TARGET_DATABASES"),
        required=False,
        default=None,
        help="Comma-separated list of Teradata target databases. If not provided,\
            DEFAULT_SYSTEM_DATABASES will be used.",
    )
    parser.add_argument(
        "--teradata_target_databases_method",
        type=str,
        choices=["ALLOWLIST", "DENYLIST"],
        action=env_default("TERADATA_TARGET_DATABASE_METHOD"),
        default="DENYLIST",
        help="Method to use for teradata_target_databases (allowlist or denylist)",
    )
    parser.add_argument(
        "--teradata_page_size",
        type=int,
        action=env_default("TERADATA_PAGE_SIZE"),
        default=1000,
        required=False,
        help="Page size for Teradata queries. Default is 1000.",
    )
    parser.add_argument(
        "--target_stats_items",
        type=str,
        nargs="*",
        choices=get_column_stats_items(),
        default=get_column_stats_items(),
        action=env_default("TERADATA_STATS_ITEMS"),
        required=False,
        help="The items for statistic values.\
              You can choose the items to be aggregated for stats.\
              Default is full stats.",
    )
    parser.add_argument(
        "--teradata_system_database",
        type=str,
        action=env_default("TERADATA_SYSTEM_DATABASE"),
        default="DBC",
        help="Name of the Teradata system database.\
              Default is DBC",
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

    configure_logging(args.log_level)

    logger.info("Starting Quollio Intelligence Agent for Teradata")

    credentials = {
        "username": args.teradata_user,
        "password": args.teradata_password,
    }

    # Parse additional connection parameters
    try:
        additional_params = json.loads(args.teradata_connection_parameters)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in TERADATA_CONNECTION_PARAMETERS. Using empty dict.")
        additional_params = {}

    logger.info("Initializing QDC client")
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
    qdc_client = qdc.initialize_qdc_client(api_url, args.client_id, args.client_secret)

    logger.info("Initializing Teradata client")
    config = teradata_repo.TeradataConfig.from_dict(
        credentials=credentials,
        host=args.teradata_host,
        port=args.teradata_port,
        additional_params=additional_params,
        system_database=args.teradata_system_database,
    )

    if "load_lineage" in args.commands:
        logger.info("Starting lineage loading process")
        load_lineage(
            conn_config=config,
            tenant_id=args.tenant_id,
            endpoint=args.teradata_host,
            qdc_client=qdc_client,
            page_size=args.teradata_page_size,
            system_database=args.teradata_system_database,
        )
        logger.info("Lineage loading process completed")

    if "load_stats" in args.commands:
        logger.info("Starting statistics loading process")
        logger.info(f"Selected stats items: {args.target_stats_items}")
        target_databases = (
            DEFAULT_SYSTEM_DATABASES
            if args.teradata_target_databases is None
            else args.teradata_target_databases.split(",")
        )
        load_stats(
            conn_config=config,
            sample_percent=args.sample_percent,
            tenant_id=args.tenant_id,
            endpoint=args.teradata_host,
            qdc_client=qdc_client,
            target_databases=target_databases,
            target_databases_method=args.teradata_target_databases_method.upper(),
            stats_items=args.target_stats_items,
            system_database=args.teradata_system_database,
        )
        logger.info("Statistics loading process completed")

    logger.info("Quollio Intelligence Agent for Teradata completed successfully")


if __name__ == "__main__":
    main()
