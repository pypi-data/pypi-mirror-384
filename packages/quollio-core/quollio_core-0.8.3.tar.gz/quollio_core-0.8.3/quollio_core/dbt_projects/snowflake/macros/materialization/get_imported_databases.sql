{% macro get_imported_databases() %}
    {%- set query %}
        WITH DATABASES AS (
            SELECT database_name
            FROM snowflake.account_usage.databases
            WHERE type = 'IMPORTED DATABASE'
            AND database_owner IS NOT NULL
            AND deleted is null
        ), ROLE_PERMISSIONS AS (
            SELECT
              table_catalog
              , ARRAY_AGG(grantee_name) grantee_names
              , ARRAY_CONTAINS('{{ var("query_role") }}'::VARIANT, ARRAY_AGG(grantee_name)) AS is_role_contained
            FROM
              SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
            WHERE
              GRANTED_ON = 'DATABASE'
              AND PRIVILEGE = 'USAGE'
              AND DELETED_ON IS NULL
            GROUP BY
              table_catalog
        )
        SELECT
          database_name
        FROM
          DATABASES
        INNER JOIN
          ROLE_PERMISSIONS
        ON
          DATABASES.database_name = ROLE_PERMISSIONS.table_catalog
        WHERE
          ROLE_PERMISSIONS.is_role_contained = TRUE
    {%- endset %}

    {%- set results = run_query(query) -%}
    {%- if execute %}
        {%- set all_databases = results.rows | map(attribute=0) | list %}
        {{ log("Extracted Databases: " ~ all_databases, info=True) }}
    {{ return(all_databases) }}
    {%- else %}
    {%- set all_databases = [] %}
    {%- endif %}

    {{ return(all_databases) }}
{% endmacro %}
