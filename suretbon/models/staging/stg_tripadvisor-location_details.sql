SELECT
    meta_osm_id,
    created_at,
    JSON_EXTRACT_SCALAR(response, '$.name') AS name,
    JSON_EXTRACT_SCALAR(response, '$.web_url') AS web_url,
    JSON_EXTRACT_SCALAR(response, '$.rating') AS rating,
    JSON_EXTRACT_SCALAR(response, '$.num_reviews') AS num_reviews
FROM
    {{ source('raw', 'tripadvisor-location_details') }}