{#- Simple surrogate key (MD5 of the concatenated columns), so the project
    runs without installing the dbt_utils package. -#}
{% macro dbt_utils_surrogate_key_fallback(columns) -%}
    md5(concat_ws('||', {% for c in columns %}coalesce(cast({{ c }} as string), ''){% if not loop.last %}, {% endif %}{% endfor %}))
{%- endmacro %}
