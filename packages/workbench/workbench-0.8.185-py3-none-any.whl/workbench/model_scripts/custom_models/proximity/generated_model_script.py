# Model: feature_space_proximity
#
# Description: The feature_space_proximity model computes nearest neighbors for the given feature space
#

# Template Placeholders
TEMPLATE_PARAMS = {
    "id_column": "udm_mol_bat_id",
    "features": ['chi2v', 'fr_sulfone', 'chi1v', 'bcut2d_logplow', 'fr_piperzine', 'kappa3', 'smr_vsa1', 'slogp_vsa5', 'fr_ketone_topliss', 'fr_sulfonamd', 'fr_imine', 'fr_benzene', 'fr_ester', 'chi2n', 'labuteasa', 'peoe_vsa2', 'smr_vsa6', 'bcut2d_chglo', 'fr_sh', 'peoe_vsa1', 'fr_allylic_oxid', 'chi4n', 'fr_ar_oh', 'fr_nh0', 'fr_term_acetylene', 'slogp_vsa7', 'slogp_vsa4', 'estate_vsa1', 'vsa_estate4', 'numbridgeheadatoms', 'numheterocycles', 'fr_ketone', 'fr_morpholine', 'fr_guanido', 'estate_vsa2', 'numheteroatoms', 'fr_nitro_arom_nonortho', 'fr_piperdine', 'nocount', 'numspiroatoms', 'fr_aniline', 'fr_thiophene', 'slogp_vsa10', 'fr_amide', 'slogp_vsa2', 'fr_epoxide', 'vsa_estate7', 'fr_ar_coo', 'fr_imidazole', 'fr_nitrile', 'fr_oxazole', 'numsaturatedrings', 'fr_pyridine', 'fr_hoccn', 'fr_ndealkylation1', 'numaliphaticheterocycles', 'fr_phenol', 'maxpartialcharge', 'vsa_estate5', 'peoe_vsa13', 'minpartialcharge', 'qed', 'fr_al_oh', 'slogp_vsa11', 'chi0n', 'fr_bicyclic', 'peoe_vsa12', 'fpdensitymorgan1', 'fr_oxime', 'molwt', 'fr_dihydropyridine', 'smr_vsa5', 'peoe_vsa5', 'fr_nitro', 'hallkieralpha', 'heavyatommolwt', 'fr_alkyl_halide', 'peoe_vsa8', 'fr_nhpyrrole', 'fr_isocyan', 'bcut2d_chghi', 'fr_lactam', 'peoe_vsa11', 'smr_vsa9', 'tpsa', 'chi4v', 'slogp_vsa1', 'phi', 'bcut2d_logphi', 'avgipc', 'estate_vsa11', 'fr_coo', 'bcut2d_mwhi', 'numunspecifiedatomstereocenters', 'vsa_estate10', 'estate_vsa8', 'numvalenceelectrons', 'fr_nh2', 'fr_lactone', 'vsa_estate1', 'estate_vsa4', 'numatomstereocenters', 'vsa_estate8', 'fr_para_hydroxylation', 'peoe_vsa3', 'fr_thiazole', 'peoe_vsa10', 'fr_ndealkylation2', 'slogp_vsa12', 'peoe_vsa9', 'maxestateindex', 'fr_quatn', 'smr_vsa7', 'minestateindex', 'numaromaticheterocycles', 'numrotatablebonds', 'fr_ar_nh', 'fr_ether', 'exactmolwt', 'fr_phenol_noorthohbond', 'slogp_vsa3', 'fr_ar_n', 'sps', 'fr_c_o_nocoo', 'bertzct', 'peoe_vsa7', 'slogp_vsa8', 'numradicalelectrons', 'molmr', 'fr_tetrazole', 'numsaturatedcarbocycles', 'bcut2d_mrhi', 'kappa1', 'numamidebonds', 'fpdensitymorgan2', 'smr_vsa8', 'chi1n', 'estate_vsa6', 'fr_barbitur', 'fr_diazo', 'kappa2', 'chi0', 'bcut2d_mrlow', 'balabanj', 'peoe_vsa4', 'numhacceptors', 'fr_sulfide', 'chi3n', 'smr_vsa2', 'fr_al_oh_notert', 'fr_benzodiazepine', 'fr_phos_ester', 'fr_aldehyde', 'fr_coo2', 'estate_vsa5', 'fr_prisulfonamd', 'numaromaticcarbocycles', 'fr_unbrch_alkane', 'fr_urea', 'fr_nitroso', 'smr_vsa10', 'fr_c_s', 'smr_vsa3', 'fr_methoxy', 'maxabspartialcharge', 'slogp_vsa9', 'heavyatomcount', 'fr_azide', 'chi3v', 'smr_vsa4', 'mollogp', 'chi0v', 'fr_aryl_methyl', 'fr_nh1', 'fpdensitymorgan3', 'fr_furan', 'fr_hdrzine', 'fr_arn', 'numaromaticrings', 'vsa_estate3', 'fr_azo', 'fr_halogen', 'estate_vsa9', 'fr_hdrzone', 'numhdonors', 'fr_alkyl_carbamate', 'fr_isothiocyan', 'minabspartialcharge', 'fr_al_coo', 'ringcount', 'chi1', 'estate_vsa7', 'fr_nitro_arom', 'vsa_estate9', 'minabsestateindex', 'maxabsestateindex', 'vsa_estate6', 'estate_vsa10', 'estate_vsa3', 'fr_n_o', 'fr_amidine', 'fr_thiocyan', 'fr_phos_acid', 'fr_c_o', 'fr_imide', 'numaliphaticrings', 'peoe_vsa6', 'vsa_estate2', 'nhohcount', 'numsaturatedheterocycles', 'slogp_vsa6', 'peoe_vsa14', 'fractioncsp3', 'bcut2d_mwlow', 'numaliphaticcarbocycles', 'fr_priamide', 'nacid', 'nbase', 'naromatom', 'narombond', 'sz', 'sm', 'sv', 'sse', 'spe', 'sare', 'sp', 'si', 'mz', 'mm', 'mv', 'mse', 'mpe', 'mare', 'mp', 'mi', 'xch_3d', 'xch_4d', 'xch_5d', 'xch_6d', 'xch_7d', 'xch_3dv', 'xch_4dv', 'xch_5dv', 'xch_6dv', 'xch_7dv', 'xc_3d', 'xc_4d', 'xc_5d', 'xc_6d', 'xc_3dv', 'xc_4dv', 'xc_5dv', 'xc_6dv', 'xpc_4d', 'xpc_5d', 'xpc_6d', 'xpc_4dv', 'xpc_5dv', 'xpc_6dv', 'xp_0d', 'xp_1d', 'xp_2d', 'xp_3d', 'xp_4d', 'xp_5d', 'xp_6d', 'xp_7d', 'axp_0d', 'axp_1d', 'axp_2d', 'axp_3d', 'axp_4d', 'axp_5d', 'axp_6d', 'axp_7d', 'xp_0dv', 'xp_1dv', 'xp_2dv', 'xp_3dv', 'xp_4dv', 'xp_5dv', 'xp_6dv', 'xp_7dv', 'axp_0dv', 'axp_1dv', 'axp_2dv', 'axp_3dv', 'axp_4dv', 'axp_5dv', 'axp_6dv', 'axp_7dv', 'c1sp1', 'c2sp1', 'c1sp2', 'c2sp2', 'c3sp2', 'c1sp3', 'c2sp3', 'c3sp3', 'c4sp3', 'hybratio', 'fcsp3', 'num_stereocenters', 'num_unspecified_stereocenters', 'num_defined_stereocenters', 'num_r_centers', 'num_s_centers', 'num_stereobonds', 'num_e_bonds', 'num_z_bonds', 'stereo_complexity', 'frac_defined_stereo'],
    "target": "udm_asy_res_free_percent",
    "track_columns": None,
}

from io import StringIO
import json
import argparse
import os
import pandas as pd

# Local Imports
from proximity import Proximity


# Function to check if dataframe is empty
def check_dataframe(df: pd.DataFrame, df_name: str) -> None:
    """Check if the DataFrame is empty and raise an error if so."""
    if df.empty:
        msg = f"*** The training data {df_name} has 0 rows! ***STOPPING***"
        print(msg)
        raise ValueError(msg)


# Function to match DataFrame columns to model features (case-insensitive)
def match_features_case_insensitive(df: pd.DataFrame, model_features: list) -> pd.DataFrame:
    """Match and rename DataFrame columns to match the model's features, case-insensitively."""
    # Create a set of exact matches from the DataFrame columns
    exact_match_set = set(df.columns)

    # Create a case-insensitive map of DataFrame columns
    column_map = {col.lower(): col for col in df.columns}
    rename_dict = {}

    # Build a dictionary for renaming columns based on case-insensitive matching
    for feature in model_features:
        if feature in exact_match_set:
            rename_dict[feature] = feature
        elif feature.lower() in column_map:
            rename_dict[column_map[feature.lower()]] = feature

    # Rename columns in the DataFrame to match model features
    return df.rename(columns=rename_dict)


# TRAINING SECTION
#
# This section (__main__) is where SageMaker will execute the training job
# and save the model artifacts to the model directory.
#
if __name__ == "__main__":
    # Template Parameters
    id_column = TEMPLATE_PARAMS["id_column"]
    features = TEMPLATE_PARAMS["features"]
    target = TEMPLATE_PARAMS["target"]  # Can be None for unsupervised models
    track_columns = TEMPLATE_PARAMS["track_columns"]  # Can be None

    # Script arguments for input/output directories
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument(
        "--output-data-dir", type=str, default=os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data")
    )
    args = parser.parse_args()

    # Load training data from the specified directory
    training_files = [os.path.join(args.train, file) for file in os.listdir(args.train) if file.endswith(".csv")]
    all_df = pd.concat([pd.read_csv(file, engine="python") for file in training_files])

    # Check if the DataFrame is empty
    check_dataframe(all_df, "training_df")

    # Create the Proximity model
    model = Proximity(all_df, id_column, features, target, track_columns=track_columns)

    # Now serialize the model
    model.serialize(args.model_dir)


# Model loading and prediction functions
def model_fn(model_dir):

    # Deserialize the model
    model = Proximity.deserialize(model_dir)
    return model


def input_fn(input_data, content_type):
    """Parse input data and return a DataFrame."""
    if not input_data:
        raise ValueError("Empty input data is not supported!")

    # Decode bytes to string if necessary
    if isinstance(input_data, bytes):
        input_data = input_data.decode("utf-8")

    if "text/csv" in content_type:
        return pd.read_csv(StringIO(input_data))
    elif "application/json" in content_type:
        return pd.DataFrame(json.loads(input_data))  # Assumes JSON array of records
    else:
        raise ValueError(f"{content_type} not supported!")


def output_fn(output_df, accept_type):
    """Supports both CSV and JSON output formats."""
    use_explicit_na = False
    if "text/csv" in accept_type:
        if use_explicit_na:
            csv_output = output_df.fillna("N/A").to_csv(index=False)  # CSV with N/A for missing values
        else:
            csv_output = output_df.to_csv(index=False)
        return csv_output, "text/csv"
    elif "application/json" in accept_type:
        return output_df.to_json(orient="records"), "application/json"  # JSON array of records (NaNs -> null)
    else:
        raise RuntimeError(f"{accept_type} accept type is not supported by this script.")


# Prediction function
def predict_fn(df, model):
    # Match column names before prediction if needed
    df = match_features_case_insensitive(df, model.features + [model.id_column])

    # Compute Nearest neighbors
    df = model.neighbors(df)
    return df
