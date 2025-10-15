import argparse
import logging
import os
import shutil

from quollio_core.helper.core import is_valid_domain, setup_dbt_profile
from quollio_core.helper.env_default import env_default
from quollio_core.helper.log import set_log_level
from quollio_core.profilers.qdc import gen_existing_global_id_dict, get_avro_file_content
from quollio_core.profilers.snowflake import (
    snowflake_column_to_column_lineage,
    snowflake_table_level_sqllineage,
    snowflake_table_stats,
    snowflake_table_to_table_lineage,
)
from quollio_core.profilers.stats import get_column_stats_items
from quollio_core.repository import dbt, qdc, snowflake, ssm

logger = logging.getLogger(__name__)


def build_view(
    conn: snowflake.SnowflakeConnectionConfig,
    stats_sample_method: str,
    target_imported_databases: str,
    target_tables: str = "",
    log_level: str = "info",
    dbt_macro_source: str = "hub",
    target_databases_method: str = "DENYLIST",
    target_databases: list[str] = [],
) -> None:
    logger.info("Build profiler views using dbt")
    # set parameters
    dbt_client = dbt.DBTClient()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_path = f"{current_dir}/dbt_projects/snowflake"
    template_path = f"{current_dir}/dbt_projects/snowflake/profiles"
    template_name = "profiles_template.yml"

    options = '{{"query_role": "{query_role}", "sample_method": "{sample_method}",\
          "target_databases_method": "{target_databases_method}",\
              "target_databases": {target_databases},\
              "target_imported_databases": "{target_imported_databases}"}}'.format(
        query_role=conn.account_query_role,
        sample_method=stats_sample_method,
        target_databases_method=target_databases_method,
        target_databases=target_databases,
        target_imported_databases=target_imported_databases,
    )

    new_package_file = f"{project_path}/packages.yml"
    if dbt_macro_source == "local":
        shutil.copyfile(f"{project_path}/packages_local.yml", new_package_file)
        logger.info("Will install dbt macro defined in packages_local.yml")
    else:
        shutil.copyfile(f"{project_path}/packages_hub.yml", new_package_file)
        logger.info("Will install dbt macro defined in packages_hub.yml")

    # build views using dbt
    setup_dbt_profile(
        connections_json=conn.as_dict(),
        template_path=template_path,
        template_name=template_name,
    )
    # FIXME: when executing some of the commands, directory changes due to the library bug.
    # https://github.com/dbt-labs/dbt-core/issues/8997
    dbt_client.invoke(
        cmd="deps",
        project_dir=project_path,
        profile_dir=template_path,
        options=["--no-use-colors", "--log-level", log_level, "--vars", options, "--source", dbt_macro_source],
    )
    run_options = ["--no-use-colors", "--log-level", log_level, "--vars", options]
    if target_tables is not None:
        if "quollio_stats_columns" in target_tables:
            target_tables.append("quollio_stats_profiling_columns")
        target_tables_str = " ".join(target_tables)
        run_options.append("--select")
        run_options.append(target_tables_str)

    dbt_client.invoke(
        cmd="run",
        project_dir=project_path,
        profile_dir=template_path,
        options=run_options,
    )

    logger.info("Profiler views are successfully built.")
    return


def load_lineage(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
    enable_column_lineage: bool = False,
) -> None:
    logger.info("Generate Snowflake table to table lineage.")

    file_content = get_avro_file_content(
        tenant_id=tenant_id,
        account_id=conn.account_id,
        qdc_client=qdc_client,
    )
    existing_global_ids = gen_existing_global_id_dict(avro_content=file_content)

    snowflake_table_to_table_lineage(
        conn=conn, qdc_client=qdc_client, tenant_id=tenant_id, existing_global_ids=existing_global_ids
    )

    if enable_column_lineage:
        logger.info(
            f"enable_column_lineage is set to {enable_column_lineage}.Generate Snowflake column to column lineage."
        )
        snowflake_column_to_column_lineage(
            conn=conn, qdc_client=qdc_client, tenant_id=tenant_id, existing_global_ids=existing_global_ids
        )
    else:
        logger.info("Skip column lineage ingestion. Set enable_column_lineage to True if you ingest column lineage.")

    logger.info("Lineage data is successfully finished.")

    return


def load_stats(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
    stats_items: str,
) -> None:
    logger.info("Generate Snowflake stats.")

    file_content = get_avro_file_content(
        tenant_id=tenant_id,
        account_id=conn.account_id,
        qdc_client=qdc_client,
    )
    existing_global_ids = gen_existing_global_id_dict(avro_content=file_content)

    if stats_items is None:
        raise ValueError("No stats items are not selected. Please specify any value to `stats_items` param.")

    logger.info("The following values will be aggregated. {stats_items}".format(stats_items=stats_items))
    snowflake_table_stats(
        conn=conn,
        qdc_client=qdc_client,
        tenant_id=tenant_id,
        stats_items=stats_items,
        existing_global_ids=existing_global_ids,
    )

    logger.info("Stats data is successfully finished.")

    return


def load_sqllineage(
    conn: snowflake.SnowflakeConnectionConfig,
    qdc_client: qdc.QDCExternalAPIClient,
    tenant_id: str,
) -> None:
    logger.info("Generate Snowflake sqllineage.")
    snowflake_table_level_sqllineage(
        conn=conn,
        qdc_client=qdc_client,
        tenant_id=tenant_id,
    )

    logger.info("sqllineage data is successfully finished.")

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Quollio Intelligence Agent for Snowflake",
        description="Build views and load lineage and stats to Quollio from Snowflake using dbt.",
        epilog="Copyright (c) 2024 Quollio Technologies, Inc.",
    )
    parser.add_argument(
        "commands",
        choices=["build_view", "load_lineage", "load_stats", "load_sqllineage"],
        type=str,
        nargs="+",
        help="""
        The command to execute.
        'build_view': Build views using dbt,
        'load_lineage': Load lineage data from created views to Quollio,
        'load_stats': Load stats from created views to Quollio,
        'load_sqllineage': Load lineage data from sql parse result(alpha),
        """,
    )
    parser.add_argument(
        "--account_id",
        type=str,
        action=env_default("SNOWFLAKE_ACCOUNT_ID"),
        required=False,
        help="The target account ID of Snowflake",
    )
    parser.add_argument(
        "--user",
        type=str,
        action=env_default("SNOWFLAKE_USER"),
        required=False,
        help="User name to connect to the database",
    )
    parser.add_argument(
        "--password",
        type=str,
        action=env_default("SNOWFLAKE_PASSWORD"),
        required=False,
        help="User password to connect to the database",
    )
    parser.add_argument(
        "--build_role",
        type=str,
        action=env_default("SNOWFLAKE_BUILD_ROLE"),
        required=False,
        help="The role in Snowflake that is used to build views by dbt",
    )
    parser.add_argument(
        "--query_role",
        type=str,
        action=env_default("SNOWFLAKE_QUERY_ROLE"),
        required=False,
        help="The role in Snowflake that is used to query views",
    )
    parser.add_argument(
        "--warehouse",
        type=str,
        action=env_default("SNOWFLAKE_WAREHOUSE"),
        required=False,
        help="The warehouse in Snowflake that is used to execute statements",
    )
    parser.add_argument(
        "--database",
        type=str,
        action=env_default("SNOWFLAKE_TARGET_DATABASE"),
        required=False,
        help="Target database name where the views are built by dbt",
    )
    parser.add_argument(
        "--schema",
        type=str,
        action=env_default("SNOWFLAKE_TARGET_SCHEMA"),
        default="public",
        required=False,
        help="Target schema name where the views are built by dbt",
    )
    parser.add_argument(
        "--target_tables",
        type=str,
        nargs="*",
        choices=[
            "quollio_lineage_column_level",
            "quollio_lineage_table_level",
            "quollio_stats_columns",
            "quollio_stats_profiling_columns",
        ],
        action=env_default("SNOWFLAKE_TARGET_TABLES"),
        required=False,
        help="Target table name if you want to create only specific tables. \
              You need to specify this parameter if you want to specify tables, not all ones. \
              Please specify table name with blank delimiter like tableA tableB \
              if you want to create two or more tables.",
    )
    parser.add_argument(
        "--target_databases_method",
        type=str,
        choices=["ALLOWLIST", "DENYLIST"],
        action=env_default("SNOWFLAKE_TARGET_DATABASE_METHOD"),
        required=False,
        help="Method to filter databases. 'ALLOWLIST' to only include listed databases,\
              'DENNYLIST' to exclude listed databases",
    )
    parser.add_argument(
        "--target_databases",
        type=str,
        nargs="*",
        action=env_default("SNOWFLAKE_TARGET_DATABASES"),
        required=False,
        help='List of databases to allow or deny based on target_database_method\
            please specify database names with blank space as delimiter\
            wildcards (%) are supported "DATABASE%" ',
    )
    parser.add_argument(
        "--target_imported_databases",
        type=str,
        choices=["ENABLED", "DISABLED"],
        action=env_default("SNOWFLAKE_TARGET_IMPORT_DATABASES"),
        required=False,
        help="Whether to get stats for import databases or not(ENABLED or DISABLED).",
    )
    parser.add_argument(
        "--sample_method",
        type=str,
        action=env_default("SNOWFLAKE_SAMPLE_METHOD"),
        default="SAMPLE(0.0001)",
        required=False,
        help="The method to sample data for stats",
    )
    parser.add_argument(
        "--tenant_id",
        type=str,
        action=env_default("TENANT_ID"),
        required=False,
        help="The tenant id (company id) where the lineage and stats are loaded",
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
        "--dbt_macro_source",
        type=str,
        choices=["hub", "local"],
        action=env_default("DBT_MACRO_SOURCE"),
        default="hub",
        required=False,
        help="The dbt macro source",
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
        help="The client secrete that is created on Quollio console to let clients access Quollio External API",
    )
    parser.add_argument(
        "--enable_column_lineage",
        type=bool,
        action=env_default("ENABLE_COLUMN_LINEAGE", store_true=True),
        default=False,
        required=False,
        help="Whether to ingest column lineage into QDIC or not. Default value is False",
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
    parser.add_argument(
        "--auth_type",
        type=str,
        choices=["PASSWORD", "KEYPAIR"],
        action=env_default("SNOWFLAKE_AUTH_TYPE"),
        default="PASSWORD",
        required=False,
        help="Authentication method to use (PASSWORD or KEYPAIR)",
    )
    parser.add_argument(
        "--private_key",
        type=str,
        action=env_default("SNOWFLAKE_PRIVATE_KEY"),
        required=False,
        help="Private key content for keypair authentication",
    )

    stats_items = get_column_stats_items()
    parser.add_argument(
        "--target_stats_items",
        type=str,
        nargs="*",
        choices=stats_items,
        default=stats_items,
        action=env_default("SNOWFLAKE_STATS_ITEMS"),
        required=False,
        help="The items for statistic values.\
              You can choose the items to be aggregated for stats. All items are selected by default.",
    )
    args = parser.parse_args()
    set_log_level(level=args.log_level)

    # Update authentication handling
    auth_params = {
        "account_id": args.account_id,
        "account_user": args.user,
        "account_build_role": args.build_role,
        "account_query_role": args.query_role,
        "account_warehouse": args.warehouse,
        "account_database": args.database,
        "account_schema": args.schema,
    }

    # Add authentication specific parameters based on method
    if args.auth_type == "KEYPAIR":
        if not args.private_key:
            raise ValueError("private_key is required when using keypair authentication")
        auth_params["private_key"] = args.private_key
        logger.info("Using keypair authentication")
    else:
        if not args.password:
            raise ValueError("password is required when using password authentication")
        auth_params["account_password"] = args.password
        logger.info("Using password authentication")
        logger.warning("Password authentication is being deprecated. Please consider using keypair authentication.")

    conn = snowflake.SnowflakeConnectionConfig(**auth_params)

    if len(args.commands) == 0:
        raise ValueError("No command is provided")

    if "build_view" in args.commands:
        if args.target_databases:
            target_databases = ["'" + db + "'" for db in args.target_databases[0].split(",")]
        else:
            target_databases = []

        build_view(
            conn=conn,
            stats_sample_method=args.sample_method,
            target_imported_databases=args.target_imported_databases,
            target_tables=args.target_tables,
            log_level=args.log_level,
            dbt_macro_source=args.dbt_macro_source,
            target_databases_method=args.target_databases_method,
            target_databases=target_databases,
        )
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

    if "load_lineage" in args.commands:
        qdc_client = qdc.QDCExternalAPIClient(
            base_url=api_url,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )
        load_lineage(
            conn=conn,
            qdc_client=qdc_client,
            tenant_id=args.tenant_id,
            enable_column_lineage=args.enable_column_lineage,
        )
    if "load_stats" in args.commands:
        qdc_client = qdc.QDCExternalAPIClient(
            base_url=api_url,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )
        load_stats(
            conn=conn,
            qdc_client=qdc_client,
            tenant_id=args.tenant_id,
            stats_items=args.target_stats_items,
        )
    if "load_sqllineage" in args.commands:
        qdc_client = qdc.QDCExternalAPIClient(
            base_url=api_url,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )
        load_sqllineage(
            conn=conn,
            qdc_client=qdc_client,
            tenant_id=args.tenant_id,
        )
