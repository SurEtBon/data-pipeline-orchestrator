SELECT
    *,
    {{ normalize_restaurant_name('name') }} AS normalized_name
FROM
    {{ ref('stg_osm-france-food-service') }}
WHERE
    type IN ('restaurant', 'fast_food')