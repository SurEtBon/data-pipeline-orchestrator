SELECT
    iofff.name AS iofff_name,
    iofff.type AS iofff_type,
    iofff.stars AS iofff_stars,
    iofff.siret AS iofff_siret,
    iofff.meta_name_com AS iofff_meta_name_com,
    iofff.meta_code_com AS iofff_meta_code_com,
    iofff.meta_name_dep AS iofff_meta_name_dep,
    iofff.meta_code_dep AS iofff_meta_code_dep,
    iofff.meta_name_reg AS iofff_meta_name_reg,
    iofff.meta_geo_point AS iofff_meta_geo_point,
    iofff.meta_osm_id AS iofff_meta_osm_id,
    ST_ASBINARY(iofff.meta_geo_point) AS iofff_meta_geo_point_geopandas,
    iofff.normalized_name AS iofff_normalized_name,
    iea.app_libelle_etablissement AS iea_app_libelle_etablissement,
    iea.siret AS iea_siret,
    iea.adresse_2_ua AS iea_adresse_2_ua,
    iea.code_postal AS iea_code_postal,
    iea.libelle_commune AS iea_libelle_commune,
    iea.date_inspection AS iea_date_inspection,
    iea.synthese_eval_sanit AS iea_synthese_eval_sanit,
    iea.app_code_synthese_eval_sanit AS iea_app_code_synthese_eval_sanit,
    iea.geores AS iea_geores,
    iea.reg_name AS iea_reg_name,
    iea.dep_name AS iea_dep_name,
    iea.dep_code AS iea_dep_code,
    iea.com_name AS iea_com_name,
    iea.com_code AS iea_com_code,
    iea.normalized_app_libelle_etablissement AS iea_normalized_app_libelle_etablissement,
    iea.full_address AS iea_full_address,
    ST_ASBINARY(iea.geores) AS iea_geores_geopandas,
    EDIT_DISTANCE(iofff.normalized_name, iea.normalized_app_libelle_etablissement) AS edit_distance_iofff_nn_iea_nale
FROM
    {{ ref('int_osm-france-food-service') }} iofff
JOIN
    {{ ref('int_export_alimconfiance') }} iea
ON
    ST_DWithin(iofff.meta_geo_point, iea.geores, 30)