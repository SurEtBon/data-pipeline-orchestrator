SELECT
    meta_osm_id,
    created_at,
    JSON_EXTRACT_SCALAR(JSON_VALUE(response), '$.places[0].rating') AS rating,
    JSON_EXTRACT_SCALAR(JSON_VALUE(response), '$.places[0].userRatingCount') AS userRatingCount,
    JSON_EXTRACT_SCALAR(JSON_VALUE(response), '$.places[0].displayName.text') AS displayName
FROM
    {{ source('raw', 'google_maps_platform-place_details') }}