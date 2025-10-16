{
    "name": "amc_process",
    "description": "Preprocessing of AMC data",
    "SOURCE": "SNOWFLAKE",

    "absolute_path": "/scratch-shared/sbenson/FeatherFormat/",
    "preprocessing": "/scratch-shared/sbenson/preprocessing_v3",

    "snowflake_config": {
        "input_schema": "RAW_DATA",
        "output_schema": "PROCESSED_DATA",
        "database": "HEALTHCARE_DB"
    },

    "Datatools4heart_Patient": {
        "table_name": "PATIENT_DATA",
        "columns": ["pseudo_id", "Geboortejaar", "Geboortemaand", "Geslacht", "Overlijdensdatum"]
    },
    "Datatools4heart_Opnametraject": {
        "table_name": "ADMISSION_DATA", 
        "columns": ["pseudo_id", "OpnameDatum"]
    },
    "Datatools4heart_Tabakgebruik": {
        "table_name": "SMOKING_DATA",
        "columns": ["pseudo_id", "IsHuidigeRoker", "IsVoormaligRoker", "Patientcontactid"]
    },
    "Datatools4heart_MetingBMI": {
        "table_name": "BMI_DATA",
        "columns": ["pseudo_id", "Patientcontactid", "BMI"]
    },
    "Datatools4heart_MetingBloeddruk": {
        "table_name": "BLOODPRESSURE_DATA",
        "columns": ["pseudo_id", "PatientContactId", "SystolischeBloeddrukWaarde", "DiastolischeBloeddrukWaarde"]
    },
    "Datatools4heart_VoorgeschiedenisMedisch": {
        "table_name": "MEDICAL_HISTORY_DATA",
        "columns": ["pseudo_id", "diagnosecode_classified", {"diagnosecode": {"t2dm": "t2dm", "af": "af", "chronic_ischemic_hd": "chronic_ischemic_hd", "acute_mi": "acute_mi"}}, ["IndicatieDatumVaststelling"]]
    },
    "Datatools4heart_MedicatieToediening": {
        "table_name": "MEDICATION_DATA", 
        "columns": ["pseudo_id", "ATCKlasseCode_classified", {"ATCKlasseCode": {"ace": "ace", "beta": "beta"}}, ["ToedieningsDatum"]]
    },
    "Datatools4heart_Labuitslag": {
        "table_name": "LAB_RESULTS_DATA",
        "columns": ["pseudo_id", "BepalingCode", {"UitslagNumeriek": {"RKRE;BL": "creatinine", "RHDL;BL": "hdl_cholesterol", "RCHO;BL": "total_cholesterol"}}, ["MateriaalAfnameDatum"]]
    },

    "categories": {"gender": ["M", "F"]},
    "scaler": "scaler_amc.h5",
    "imputer": "imputer_amc.h5",
    "final_cols": ["Geslacht", "AgeAtOpname", "IsHuidigeRoker", "hdl_cholesterol", "total_cholesterol", "OpnameDatum",
    "BMI", "SystolischeBloeddrukWaarde", "DiastolischeBloeddrukWaarde", "ace", "time", "beta", "creatinine", "t2dm", "chronic_ischemic_hd", "acute_mi", "af"],
    "comment_gencols": ["age_###", "bmi_###", "sbp_###", "dbp_###", "hdl_cholesterol_###", "total_cholesterol_###", "rf_smoking_###",
    "sex_###", "hypertension_threshold_###", "t2dm_threshold_###", "diabetes_threshold_###", "ht_medication_###", 
    "hf_threshold_***", "arthritis_threshold_***", "fam_history_***", 
    "rf_ethnicity_***", "townsend_deprivation_index_***"],

    "InitTransforms": {
        "ATCKlasseCode_classified": {
            "func": "classify",
            "kwargs": {
                "classification_map": ["ace", "beta"],
                "input_col": "ATCKlasseCode",
                "out_col": "ATCKlasseCode_classified",
                "id_col": "pseudo_id"
            }
        },
        "diagnosecode_classified": {
            "func": "classify",
            "kwargs": {
                "classification_map": ["t2dm", "af", "chronic_ischemic_hd", "acute_mi"],
                "input_col": "diagnosecode",
                "out_col": "diagnosecode_classified",
                "id_col": "pseudo_id"
            }
        }
    },
    "PreTransforms": {
        "OpnameDatum": {
            "func": "datetime_keepfirst",
            "kwargs": {
                "col_to_date": "OpnameDatum",
                "sort_col": "OpnameDatum",
                "drop_col": "pseudo_id"
            }
        },
        "Overlijdensdatum": {
            "func": "datetime",
            "kwargs": {
                "col_to_date": "Overlijdensdatum"
            }
        },
        "IsHuidigeRoker": {
            "func": "keepfirst",
            "kwargs": {
                "sort_col": "Patientcontactid",
                "drop_col": "pseudo_id"
            }
        },
        "SystolischeBloeddrukWaarde": {
            "func": "keepfirst",
            "kwargs": {
                "sort_col": "PatientContactId",
                "drop_col": "pseudo_id"
            }
        },
        "BMI": {
            "func": "keepfirst",
            "kwargs": {
                "sort_col": "Patientcontactid",
                "drop_col": "pseudo_id"
            }
        }
    },

    "MergedTransforms": {
        "time": {
            "func": "diff",
            "kwargs": {
                "end": "Overlijdensdatum",
                "start": "OpnameDatum"
            }
        },
        "AgeAtOpname": {
            "func": "diff",
            "kwargs": {
                "end": "OpnameDatum",
                "start": "Geboortejaar",
                "level": "year"
            }
        },
        "Geslacht": {
            "func": "map",
            "kwargs": {
                "map": {"Man": 0, "Vrouw": 1}
            }
        },
        "IsHuidigeRoker": {
            "func": "map",
            "kwargs": {
                "map": {"Nee": 0, "Ja": 1}
            }
        },
        "FillNaN": {
            "func": "fillna",
            "kwargs": {
                "values": {"IsHuidigeRoker": 0}
            }
        },
        "DropNaN": {
            "func": "dropna",
            "kwargs": {
                "subset": ["BMI", "SystolischeBloeddrukWaarde"]
            }
        }
    }
}
