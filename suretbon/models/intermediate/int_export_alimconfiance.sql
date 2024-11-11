SELECT
    * EXCEPT(geores),
    ST_GEOGFROMTEXT(geores) AS geores,
    {{ normalize_restaurant_name('app_libelle_etablissement') }} AS normalized_app_libelle_etablissement,
    concat(adresse_2_ua, ', ', code_postal, ', ', libelle_commune) as full_address
FROM (
    SELECT DISTINCT
        * EXCEPT(geores),
        ST_ASTEXT(geores) AS geores
    FROM
        {{ ref('stg_export_alimconfiance') }}
    WHERE
        filtre = 'Restaurants'
)