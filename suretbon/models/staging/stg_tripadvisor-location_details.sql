SELECT
    meta_osm_id,
    created_at,
    JSON_EXTRACT_SCALAR(JSON_VALUE(response), '$.name') AS name,
    JSON_EXTRACT_SCALAR(JSON_VALUE(response), '$.rating') AS rating,
    JSON_EXTRACT_SCALAR(JSON_VALUE(response), '$.num_reviews') AS num_reviews
FROM
    {{ source('raw', 'tripadvisor-location_details') }}