SELECT
    rwgmat.*,
    sgmppd.rating AS sgmppd_rating,
    sgmppd.googleMapsUri AS sgmppd_googleMapsUri,
    sgmppd.userRatingCount AS sgmppd_userRatingCount,
    sgmppd.displayName AS sgmppd_displayName,
    stld.name AS stld_name,
    stld.web_url AS stld_web_url,
    stld.rating AS stld_rating,
    stld.num_reviews AS stld_num_reviews
FROM
    {{ ref('restaurants_without_google_maps_and_tripadvisor') }} rwgmat
LEFT JOIN
    {{ ref('stg_google_maps_platform-place_details') }} sgmppd
ON
    iofff_meta_osm_id = sgmppd.meta_osm_id
LEFT JOIN
    {{ ref('stg_tripadvisor-location_details') }} stld
ON
    iofff_meta_osm_id = stld.meta_osm_id