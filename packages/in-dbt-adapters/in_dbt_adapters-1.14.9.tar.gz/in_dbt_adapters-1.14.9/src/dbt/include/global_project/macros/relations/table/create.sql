{% macro get_create_table_as_sql(temporary, relation, sql) -%}
  {{ adapter.dispatch('get_create_table_as_sql', 'dbt')(temporary, relation, sql) }}
{%- endmacro %}

{% macro default__get_create_table_as_sql(temporary, relation, sql) -%}
  {{ return(create_table_as(temporary, relation, sql)) }}
{% endmacro %}


/* {# keep logic under old macro name for backwards compatibility #} */
{% macro create_table_as(temporary, relation, compiled_code, language='sql') -%}
  {% do log("[DBT_MACRO] CREATE_TABLE_AS: Starting create_table_as - temporary: " ~ temporary ~ ", relation: " ~ relation ~ ", language: " ~ language, info=True) %}
  {# backward compatibility for create_table_as that does not support language #}
  {% if language == "sql" %}
    {% do log("[DBT_MACRO] CREATE_TABLE_AS: Dispatching to adapter-specific create_table_as (SQL)", info=True) %}
    {{ adapter.dispatch('create_table_as', 'dbt')(temporary, relation, compiled_code)}}
  {% else %}
    {% do log("[DBT_MACRO] CREATE_TABLE_AS: Dispatching to adapter-specific create_table_as (non-SQL)", info=True) %}
    {{ adapter.dispatch('create_table_as', 'dbt')(temporary, relation, compiled_code, language) }}
  {% endif %}
  {% do log("[DBT_MACRO] CREATE_TABLE_AS: Completed create_table_as", info=True) %}

{%- endmacro %}

{% macro default__create_table_as(temporary, relation, sql) -%}
  {%- set sql_header = config.get('sql_header', none) -%}

  {{ sql_header if sql_header is not none }}

  create {% if temporary: -%}temporary{%- endif %} table
    {{ relation.include(database=(not temporary), schema=(not temporary)) }}
  {% set contract_config = config.get('contract') %}
  {% if contract_config.enforced and (not temporary) %}
    {{ get_assert_columns_equivalent(sql) }}
    {{ get_table_columns_and_constraints() }}
    {%- set sql = get_select_subquery(sql) %}
  {% endif %}
  as (
    {{ sql }}
  );
{%- endmacro %}


{% macro default__get_column_names() %}
  {#- loop through user_provided_columns to get column names -#}
    {%- set user_provided_columns = model['columns'] -%}
    {%- for i in user_provided_columns %}
      {%- set col = user_provided_columns[i] -%}
      {%- set col_name = adapter.quote(col['name']) if col.get('quote') else col['name'] -%}
      {{ col_name }}{{ ", " if not loop.last }}
    {%- endfor -%}
{% endmacro %}


{% macro get_select_subquery(sql) %}
  {{ return(adapter.dispatch('get_select_subquery', 'dbt')(sql)) }}
{% endmacro %}

{% macro default__get_select_subquery(sql) %}
    select {{ adapter.dispatch('get_column_names', 'dbt')() }}
    from (
        {{ sql }}
    ) as model_subq
{%- endmacro %}
