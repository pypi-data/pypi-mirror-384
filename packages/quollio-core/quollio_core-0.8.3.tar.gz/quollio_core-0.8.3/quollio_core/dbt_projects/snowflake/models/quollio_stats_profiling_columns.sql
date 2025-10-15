{% if var('target_imported_databases') == 'ENABLED' %}
  {% set imported_databases = get_imported_databases() %}
{% endif %}

WITH columns AS (
    SELECT
      table_catalog
      , table_schema
      , table_name
      , column_name
      , data_type
    FROM
      {{ source('account_usage', 'COLUMNS') }}
    WHERE
      deleted is null
      AND table_name NOT LIKE 'QUOLLIO_%%'
    GROUP BY
      table_catalog
      , table_schema
      , table_name
      , column_name
      , data_type
    ORDER BY
      table_catalog
      , table_schema
      , table_name
),
{% if var('target_imported_databases') == 'ENABLED' %}
  {% if imported_databases | length > 0 %}
  imported_tables AS (
    {% for database in imported_databases %}
        SELECT
          c.table_catalog
          , c.table_schema
          , c.table_name
          , c.column_name
          , c.data_type
        FROM
          {{ database }}.INFORMATION_SCHEMA.COLUMNS c
        INNER JOIN
          {{ database }}.INFORMATION_SCHEMA.TABLE_PRIVILEGES tp
        ON
          c.table_catalog = tp.table_catalog
          AND c.table_schema = tp.table_schema
          AND c.table_name = tp.table_name
        WHERE
          c.TABLE_SCHEMA != 'INFORMATION_SCHEMA'
          AND tp.grantee = '{{ var("query_role") }}'
          AND tp.PRIVILEGE_TYPE = 'SELECT'
        {% if not loop.last %}
        UNION ALL
        {% endif %}
    {% endfor %}
  ),
  {% endif %}
{% endif %}
accessible_tables AS (
    SELECT
      table_catalog
      , table_schema
      , name
    FROM
      {{ source('account_usage', 'GRANTS_TO_ROLES') }}
    WHERE
      granted_on in ('TABLE', 'VIEW', 'MATERIALIZED VIEW')
      AND grantee_name = '{{ var("query_role") }}'
      AND privilege in ('SELECT', 'OWNERSHIP')
      AND deleted_on IS NULL
    GROUP BY
      table_catalog
      , table_schema
      , name  
), m_view_sys_columns AS (
  SELECT
    cols.table_catalog
    , cols.table_schema
    , cols.table_name
    , cols.column_name
    , cols.data_type
  FROM
    {{ source('account_usage', 'COLUMNS') }} cols
  LEFT OUTER JOIN
    {{ source('account_usage', 'TABLES') }} tbls
  ON
    cols.table_catalog = tbls.table_catalog
    AND cols.table_schema = tbls.table_schema
    AND cols.table_name = tbls.table_name
  WHERE
    tbls.table_type = 'MATERIALIZED VIEW'
    AND cols.column_name = 'SYS_MV_SOURCE_PARTITION'
), implicit_columns_removed AS (
  SELECT
    c.table_catalog
    , c.table_schema
    , c.table_name
    , c.column_name
    , c.data_type
  FROM
    columns c
  INNER JOIN
    accessible_tables a
  ON
    c.table_catalog = a.table_catalog
    AND c.table_schema = a.table_schema
    AND c.table_name = a.name
  {% if var('target_imported_databases') == 'ENABLED' %}
    UNION
    SELECT
      table_catalog
      , table_schema
      , table_name
      , column_name
      , data_type
    FROM
      imported_tables
  {% endif %}
  MINUS
  SELECT
    table_catalog
    , table_schema
    , table_name
    , column_name
    , data_type
  FROM
    m_view_sys_columns
), final AS (
  SELECT
    table_catalog
    , table_schema
    , table_name
    , column_name
    , data_type
    , case when data_type in('NUMBER','DECIMAL', 'DEC', 'NUMERIC',
                             'INT', 'INTEGER', 'BIGINT', 'SMALLINT',
                             'TINYINT', 'BYTEINT', 'FLOAT')
                             THEN true
           else false END AS is_calculable
    , case when data_type not in('GEOGRAPHY')
                             THEN true
           else false END AS can_approx_count
  FROM
    implicit_columns_removed
  WHERE
      {% if var('target_databases_method') == 'ALLOWLIST' %}
          {% if var('target_databases') %}
              TABLE_CATALOG LIKE ANY ({{ var('target_databases')|join(",") }})
          {% else %}
              1=0  -- If no databases specified in allowlist, deny all
          {% endif %}
      {% elif var('target_databases_method') == 'DENYLIST' %}
          {% if var('target_databases') %}
              NOT (TABLE_CATALOG LIKE ANY ({{ var('target_databases')|join(",") }}))
          {% else %}
              1=1  -- If no databases specified in denylist, include all
          {% endif %}
      {% else %}
          1=1  -- Default case: allow all databases
      {% endif %}
  )
select * from final
