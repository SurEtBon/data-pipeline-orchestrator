WITH inspections AS (
    SELECT
        iofff_name,
        iofff_meta_geo_point_binary,
        iea_app_libelle_etablissement,
        iea_geores_binary,
        count(iea_date_inspection) AS nb_inspections,
        array_agg(to_json_string(struct(iea_date_inspection, iea_app_code_synthese_eval_sanit))) AS inspections
    FROM
        {{ ref('int_osm-france-food-service_export_alimconfiance') }}
    GROUP BY
        iofff_name, iofff_meta_geo_point_binary, iea_app_libelle_etablissement, iea_geores_binary
),
restaurants AS (
    SELECT
        ioffsea.*,
        inspections.nb_inspections,
        inspections.inspections,
        ROW_NUMBER() OVER (
            PARTITION BY
                ioffsea.iofff_name,
                ioffsea.iofff_meta_geo_point_binary,
                ioffsea.iea_app_libelle_etablissement,
                ioffsea.iea_geores_binary
            ORDER BY
                ioffsea.iea_date_inspection DESC
        ) AS row_num
    FROM
        {{ ref('int_osm-france-food-service_export_alimconfiance') }} ioffsea
    JOIN
        inspections
    ON
        inspections.iofff_name = ioffsea.iofff_name
    AND
        ioffsea.iofff_meta_geo_point_binary = inspections.iofff_meta_geo_point_binary
    AND
        ioffsea.iea_app_libelle_etablissement = inspections.iea_app_libelle_etablissement
    AND
        ioffsea.iea_geores_binary = inspections.iea_geores_binary
    WHERE
        (ioffsea.iofff_normalized_name = ioffsea.iea_normalized_app_libelle_etablissement)
    OR
        (ioffsea.iofff_siret = ioffsea.iea_siret)
    OR
        (ioffsea.iea_normalized_app_libelle_etablissement IS NULL)
    OR
        (ioffsea.edit_distance_iofff_nn_iea_nale <= 3)
)
SELECT
    restaurants.* except(row_num)
FROM
    restaurants
WHERE
    row_num = 1