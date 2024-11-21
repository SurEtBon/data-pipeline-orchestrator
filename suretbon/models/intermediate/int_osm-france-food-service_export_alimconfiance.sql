WITH `osm-france-food-service_export_alimconfiance` AS (
    SELECT
        osm_ffs.name AS `osm_ffs-name`,
        osm_ffs.type AS `osm_ffs-type`,
        osm_ffs.stars AS `osm_ffs-stars`,
        osm_ffs.siret AS `osm_ffs-siret`,
        osm_ffs.meta_name_com AS `osm_ffs-meta_name_com`,
        osm_ffs.meta_code_com AS `osm_ffs-meta_code_com`,
        osm_ffs.meta_name_dep AS `osm_ffs-meta_name_dep`,
        osm_ffs.meta_code_dep AS `osm_ffs-meta_code_dep`,
        osm_ffs.meta_name_reg AS `osm_ffs-meta_name_reg`,
        osm_ffs.meta_geo_point AS `osm_ffs-meta_geo_point`,
        osm_ffs.meta_osm_id AS `osm_ffs-meta_osm_id`,
        osm_ffs.normalized_name AS `osm_ffs-normalized_name`,
        osm_ffs.meta_geo_point_latitude AS `osm_ffs-meta_geo_point_latitude`,
        osm_ffs.meta_geo_point_longitude AS `osm_ffs-meta_geo_point_longitude`,
        osm_ffs.meta_geo_point_binary AS `osm_ffs-meta_geo_point_binary`,
        ea.app_libelle_etablissement AS `ea-app_libelle_etablissement`,
        ea.siret AS `ea-siret`,
        ea.adresse_2_ua AS `ea-adresse_2_ua`,
        ea.code_postal AS `ea-code_postal`,
        ea.libelle_commune AS `ea-libelle_commune`,
        ea.date_inspection AS `ea-date_inspection`,
        ea.synthese_eval_sanit AS `ea-synthese_eval_sanit`,
        ea.app_code_synthese_eval_sanit AS `ea-app_code_synthese_eval_sanit`,
        ea.geores AS `ea-geores`,
        ea.reg_name AS `ea-reg_name`,
        ea.dep_name AS `ea-dep_name`,
        ea.dep_code AS `ea-dep_code`,
        ea.com_name AS `ea-com_name`,
        ea.com_code AS `ea-com_code`,
        ea.normalized_app_libelle_etablissement AS `ea-normalized_app_libelle_etablissement`,
        ea.full_address AS `ea-full_address`,
        ea.geores_latitude AS `ea-geores_latitude`,
        ea.geores_longitude AS `ea-geores_longitude`,
        ea.geores_binary AS `ea-geores_binary`,
        EDIT_DISTANCE(osm_ffs.normalized_name, ea.normalized_app_libelle_etablissement) AS `edit_distance-osm_ffs_nn-ea_nale`
    FROM
        {{ ref('int_osm-france-food-service') }} osm_ffs
    JOIN
        {{ ref('int_export_alimconfiance') }} ea
    ON
        ST_DWithin(osm_ffs.meta_geo_point, ea.geores, 30)
),
controles_sanitaires AS (
    SELECT
        `osm_ffs-name`,
        `osm_ffs-meta_geo_point_binary`,
        `ea-app_libelle_etablissement`,
        `ea-geores_binary`,
        count(`ea-date_inspection`) AS nombre,
        array_agg(to_json(struct(`ea-date_inspection`, `ea-app_code_synthese_eval_sanit`))) AS controles_sanitaires
    FROM
        `osm-france-food-service_export_alimconfiance`
    GROUP BY
        `osm_ffs-name`, `osm_ffs-meta_geo_point_binary`, `ea-app_libelle_etablissement`, `ea-geores_binary`
),
restaurants AS (
    SELECT
        `osm_ffs-ea`.*,
        controles_sanitaires.nombre AS nombre_controles_sanitaires,
        controles_sanitaires.controles_sanitaires,
        ROW_NUMBER() OVER (
            PARTITION BY
                `osm_ffs-ea`.`osm_ffs-name`,
                `osm_ffs-ea`.`osm_ffs-meta_geo_point_binary`,
                `osm_ffs-ea`.`ea-app_libelle_etablissement`,
                `osm_ffs-ea`.`ea-geores_binary`
            ORDER BY
                `osm_ffs-ea`.`ea-date_inspection` DESC
        ) AS row_nb
    FROM
        `osm-france-food-service_export_alimconfiance` `osm_ffs-ea`
    JOIN
        controles_sanitaires
    ON
        `osm_ffs-ea`.`osm_ffs-name` = controles_sanitaires.`osm_ffs-name`
    AND
        `osm_ffs-ea`.`osm_ffs-meta_geo_point_binary` = controles_sanitaires.`osm_ffs-meta_geo_point_binary`
    AND
        `osm_ffs-ea`.`ea-app_libelle_etablissement` = controles_sanitaires.`ea-app_libelle_etablissement`
    AND
        `osm_ffs-ea`.`ea-geores_binary` = controles_sanitaires.`ea-geores_binary`
    WHERE
        `osm_ffs-ea`.`osm_ffs-normalized_name` = `osm_ffs-ea`.`ea-normalized_app_libelle_etablissement`
    OR
        `osm_ffs-ea`.`osm_ffs-siret` = `osm_ffs-ea`.`ea-siret`
    OR
        `osm_ffs-ea`.`ea-normalized_app_libelle_etablissement` IS NULL
    OR
        `osm_ffs-ea`.`edit_distance-osm_ffs_nn-ea_nale` <= 3
)
SELECT
    restaurants.* except(row_nb)
FROM
    restaurants
WHERE
    row_nb = 1