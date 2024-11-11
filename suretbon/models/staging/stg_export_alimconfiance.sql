SELECT
    TRIM(app_libelle_etablissement) AS app_libelle_etablissement,
    TRIM(siret) AS siret,
    TRIM(adresse_2_ua) AS adresse_2_ua,
    TRIM(code_postal) AS code_postal,
    TRIM(libelle_commune) AS libelle_commune,
    CAST(date_inspection AS DATE) AS date_inspection,
    TRIM(app_libelle_activite_etablissement) AS app_libelle_activite_etablissement,
    TRIM(synthese_eval_sanit) AS synthese_eval_sanit,
    cast(app_code_synthese_eval_sanit AS INT64) AS app_code_synthese_eval_sanit,
    TRIM(agrement) AS agrement,
    geores,
    TRIM(filtre) AS filtre,
    TRIM(ods_type_activite) AS ods_type_activite,
    TRIM(reg_name) AS reg_name,
    TRIM(reg_code) AS reg_code,
    TRIM(dep_name) AS dep_name,
    TRIM(dep_code) AS dep_code,
    TRIM(com_name) AS com_name,
    TRIM(com_code) AS com_code
FROM
    {{ source('raw', 'export_alimconfiance') }}