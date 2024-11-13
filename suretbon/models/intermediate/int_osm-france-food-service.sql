SELECT
    *,
    {{ normalize_restaurant_name('name') }} AS normalized_name,
    ROUND(ST_Y(meta_geo_point), 4) as meta_geo_point_latitude,
    ROUND(ST_X(meta_geo_point), 4) as meta_geo_point_longitude,
    ST_ASBINARY(meta_geo_point) AS meta_geo_point_binary
FROM
    {{ ref('stg_osm-france-food-service') }}
WHERE
    type IN ('restaurant', 'fast_food')