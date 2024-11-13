SELECT
    *,
    {{ normalize_restaurant_name('app_libelle_etablissement') }} AS normalized_app_libelle_etablissement,
    concat(adresse_2_ua, ', ', code_postal, ', ', libelle_commune) as full_address,
    ROUND(ST_Y(geores), 4) as geores_latitude,
    ROUND(ST_X(geores), 4) as geores_longitude,
    ST_ASBINARY(geores) AS geores_binary
FROM
    {{ ref('stg_export_alimconfiance') }}
WHERE
    filtre = 'Restaurants'