{% macro normalize_restaurant_name(input_text) %}
    (
      REGEXP_REPLACE(
        LOWER(
            REGEXP_REPLACE(
                NORMALIZE({{ input_text }}, NFD),
                '[^a-zA-Z0-9]', ''
            )
        )
        , r'(sarl|sas|eurl|scs|scop|sasu|scic)', '')
    )
{% endmacro %}