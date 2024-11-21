SELECT
    rwgmat.*,
    gmp_pd.rating AS `gmp_pd-rating`,
    gmp_pd.googleMapsUri AS `gmp_pd-googleMapsUri`,
    gmp_pd.userRatingCount AS `gmp_pd-userRatingCount`,
    gmp_pd.displayName AS `gmp_pd-displayName`,
    t_ld.name AS `t_ld-name`,
    t_ld.web_url AS `t_ld-web_url`,
    t_ld.rating AS `t_ld-rating`,
    t_ld.num_reviews AS `t_ld-num_reviews`
FROM
    {{ ref('int_osm-france-food-service_export_alimconfiance') }} rwgmat
LEFT JOIN
    {{ ref('stg_google_maps_platform-place_details') }} gmp_pd
ON
    rwgmat.`osm_ffs-meta_osm_id` = gmp_pd.meta_osm_id
LEFT JOIN
    {{ ref('stg_tripadvisor-location_details') }} t_ld
ON
    rwgmat.`osm_ffs-meta_osm_id` = t_ld.meta_osm_id