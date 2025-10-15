{%- materialization divided_view, default %}
{%- set identifier = model['alias'] %}
{%- set target_relations = [] %}
{%- set grant_config = config.get('grants') %}
{%- set max_columns_per_view = config.get('max_columns_per_view', 100) %}

{{ run_hooks(pre_hooks, inside_transaction=False) }}
-- BEGIN happens here:
{{ run_hooks(pre_hooks, inside_transaction=True) }}

-- fetch target_tables
{%- set query_stats_target_tables -%}
    SELECT
      TABLE_CATALOG
      , TABLE_SCHEMA
      , TABLE_NAME
      , OBJECT_AGG(COLUMN_NAME, OBJECT_CONSTRUCT('IS_CALCULABLE', IS_CALCULABLE, 'CAN_APPROX_COUNT', CAN_APPROX_COUNT))
    FROM
      {{ ref('quollio_stats_profiling_columns') }}
    WHERE NOT startswith(table_name, 'QUOLLIO_')
    GROUP BY
      TABLE_CATALOG
      , TABLE_SCHEMA
      , TABLE_NAME
{%- endset -%}
{%- set results = run_query(query_stats_target_tables) -%}
{%- if execute -%}
{%- set stats_target_tables = results.rows -%}
{%- else -%}
{%- set stats_target_tables = [] -%}
{%- endif -%}

-- skip creating views if the target profiling columns don't exist.
{%- if stats_target_tables | length == 0 -%}
  {% call statement("main") %}
    {{ log("No records found. Just execute select stmt for skipping call statement.", info=True) }}
    select null
  {% endcall %}
  {%- set full_refresh_mode = (should_full_refresh()) -%}
  {%- set should_revoke = should_revoke(target_relation, full_refresh_mode) %}
{%- endif -%}

-- create view for each table
{%- for stats_target_table in stats_target_tables -%}
  {%- set columns_json = fromjson(stats_target_table[3]) %}
  {%- set column_list = columns_json.keys() | list %}
  {%- set chunk_count = ((column_list | length) / max_columns_per_view) | round(0, 'ceil') | int %}
  
  {%- for chunk_index in range(chunk_count) %}
    {%- set start_idx = chunk_index * max_columns_per_view %}
    {%- set end_idx = start_idx + max_columns_per_view %}
    {%- set chunk_columns = column_list[start_idx:end_idx] %}
    
    -- build sql for column value aggregation.
    {%- set sql_for_column_stats %}
    {%- for col_name in chunk_columns -%}
      {%- set attr = columns_json[col_name] %}
      {%- if not loop.first %}UNION{% endif %}
      SELECT
        DISTINCT
        '{{stats_target_table[0]}}' as db_name
        , '{{stats_target_table[1]}}' as schema_name
        , '{{stats_target_table[2]}}' as table_name
        , '{{col_name}}' as column_name
        , {% if attr["IS_CALCULABLE"] == True %}CAST(MAX("{{col_name}}") AS STRING){% else %}NULL{% endif %} AS max_value
        , {% if attr["IS_CALCULABLE"] == True %}CAST(MIN("{{col_name}}") AS STRING){% else %}NULL{% endif %} AS min_value
        , COUNT_IF("{{col_name}}" IS NULL) AS null_count
        , {% if attr["CAN_APPROX_COUNT"] == True %}APPROX_COUNT_DISTINCT("{{col_name}}"){% else %}NULL{% endif %} AS cardinality
        , {% if attr["IS_CALCULABLE"] == True %}AVG("{{col_name}}"){% else %}NULL{% endif %} AS avg_value
        , {% if attr["IS_CALCULABLE"] == True %}MEDIAN("{{col_name}}"){% else %}NULL{% endif %} AS median_value
        , {% if attr["IS_CALCULABLE"] == True %}APPROX_TOP_K("{{col_name}}")[0][0]{% else %}NULL{% endif %} AS mode_value
        , {% if attr["IS_CALCULABLE"] == True %}STDDEV("{{col_name}}"){% else %}NULL{% endif %} AS stddev_value
      FROM "{{stats_target_table[0]}}"."{{stats_target_table[1]}}"."{{stats_target_table[2]}}" {{ var("sample_method") }}
    {% endfor -%}
    {%- endset %}

    -- create a view with a index as suffix and chunk indicator
    {%- set chunk_suffix = "" if chunk_count == 1 else "_PART" ~ (chunk_index + 1) %}
    {%- set stats_view_identifier = "\"%s_%s_%s_%s%s\"" | format(model['name'], stats_target_table[0], stats_target_table[1], stats_target_table[2], chunk_suffix) | upper %}
    {%- set schema_name = "\"%s\""|format(schema) %}
    {%- set db_name = "\"%s\""|format(database) %}
    {%- set target_relation = api.Relation.create(identifier=stats_view_identifier, schema=schema_name, database=db_name, type='view') %}
    
    {{ log("Creating view " ~ stats_view_identifier ~ " with " ~ chunk_columns | length ~ " columns (chunk " ~ (chunk_index + 1) ~ " of " ~ chunk_count ~ ")", info=True) }}
    
    {% call statement("main") %}
      {{ get_create_view_as_sql(target_relation, sql_for_column_stats) }}
    {% endcall %}
    
    {%- set full_refresh_mode = (should_full_refresh()) -%}
    {%- set should_revoke = should_revoke(target_relation, full_refresh_mode) %}
    {%- do apply_grants(target_relation, grant_config, should_revoke) %}
    {%- set target_relations = target_relations.append(target_relation) %}
  {%- endfor %}
{%- endfor -%}

{{ run_hooks(post_hooks, inside_transaction=True) }}
-- COMMIT happens here:
{{ adapter.commit() }}
{{ run_hooks(post_hooks, inside_transaction=False) }}

{{ return({'relations': target_relations}) }}
{%- endmaterialization -%}
