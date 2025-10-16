amc_v1 = {
    "name": "amc_process",
    "description": "Preprocessing of AMC data",
    "SOURCE": "SNOWFLAKE",
    "preprocessing": "/tmp/preprocessing",

    "snowflake_config": {
        "input_schema": "RAW_DATA",
        "output_schema": "PROCESSED_DATA",
        "database": "HEALTHCARE_DB"
    },

    "Datatools4heart_Patient": {
        "table_name": "PATIENT_DATA",
        "columns": ["pseudo_id", "Geboortejaar", "Geboortemaand", "Geslacht", "Overlijdensdatum"]
    },
    "Datatools4heart_Tabakgebruik": {
        "table_name": "SMOKING_DATA",
        "columns": ["pseudo_id", "IsHuidigeRoker", "IsVoormaligRoker", "Patientcontactid"]
    },

    "categories": {"Geslacht": ["Man", "Vrouw"]},
    "scaler": "scaler_amc.h5",
    "imputer": "imputer_amc.h5",

    "final_cols": ["Geslacht", "AgeAtOpname", "IsHuidigeRoker"],

    "InitTransforms": {
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
        "IsHuidigeRoker": {
            "func": "keepfirst",
            "kwargs": {
                "sort_col": "Patientcontactid",
                "drop_col": "pseudo_id"
            }
        }
    },

    "MergedTransforms": {
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
        }
    }
}
