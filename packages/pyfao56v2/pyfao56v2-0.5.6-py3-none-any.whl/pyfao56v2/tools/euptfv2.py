import rpy2.robjects as robjects
import pandas as pd
pd.DataFrame.iteritems = pd.DataFrame.items
from rpy2.robjects.conversion import localconverter
from rpy2.robjects import default_converter, pandas2ri
from rpy2.rinterface_lib import callbacks
from os import path as osp

EUPTFV2_PATH = osp.dirname(osp.realpath(__file__)) + '/euptfv2/'

# Suppress R console output
original_writeconsole_warnerror = callbacks.consolewrite_warnerror
callbacks.consolewrite_warnerror = lambda x: None
#original_writeconsole_print = callbacks.consolewrite_print
#callbacks.consolewrite_print = lambda x: None


def _eval_ptf(variable: str, ptf: str, predictors: dict) -> float:
    """Evaluate a pedotransfer function (PTF) using the provided predictors.

    Parameters
    ----------
    variable : str
        The variable to evaluate (e.g., 'FC' for theta_FC, 'WP' for theta_WP).
    ptf : dict
        The PTF to evaluate, containing coefficients and intercepts.
    predictors : dict
        The predictors to use for evaluation.

    Returns
    -------
    float
        The evaluated value from the PTF.
    """

    # Load R packages
    robjects.r('library(ranger)')   # to use ranger models
    robjects.r('library(parallel)') # to use detectCores()
    #robjects.r('library(repmis)')  # to use source_data

    # Load PTF from file
    robjects.r(f'load("{EUPTFV2_PATH}/{variable}_EUHYDI/{variable}_{ptf}.rdata")') # this is a ranger model

    # Convert predictors from Python dict to R dataframe
    predictors_df = pd.DataFrame([predictors])
    with localconverter(default_converter + pandas2ri.converter):
        robjects.globalenv['predictors'] = robjects.conversion.py2rpy(predictors_df)

    # Eval PTF
    robjects.r(f'{variable} <- predict({variable}_{ptf}, data=predictors, type="response", num.threads=detectCores()-1)')

    # Extract prediction
    value = robjects.r(f'{variable}$predictions')[0]

    return value


def apply_euptfv2(sand, silt, clay, mean_depth=15, bulk_density=None, organic_carbon=None, pH_H2O=None, CACO3=None, CEC=None):
    """Apply EUPTFV2 to estimate soil properties from soil texture data.

    Parameters
    ----------
    sand : float
        Percent sand content in the soil sample.
    silt : float
        Percent silt content in the soil sample.
    clay : float
        Percent clay content in the soil sample.
    mean_depth : float
        Mean soil sample depth (cm).
    bulk_density : float, optional
        Bulk density of the soil sample (g/cm3).
    organic_carbon : float, optional
        Organic carbon content in the soil sample (%).
    pH_H2O : float, optional
        pH in water of the soil sample.
    CACO3 : float, optional
        Calcium carbonate content in the soil sample (%).
    CEC : float, optional
        Cation exchange capacity of the soil sample (meq/100g).

    Returns
    -------
    thetaFC : float
        Volumetric water content at field capacity (cm3/cm3).
    thetaWP : float
        Volumetric water content at wilting point (cm3/cm3).
    """

    assert not any([sand is None, silt is None, clay is None]), "Sand, silt, and clay must all be provided."
    assert 0 <= sand <= 100, f"Sand content must be between 0 and 100. Got {sand}."
    assert 0 <= silt <= 100, f"Silt content must be between 0 and 100. Got {silt}."
    assert 0 <= clay <= 100, f"Clay content must be between 0 and 100. Got {clay}."
    assert 99 <= sand + silt + clay <= 100, f"Sum of sand, silt, and clay must be around 100. Got {sand + silt + clay}."
    assert mean_depth > 0, f"Mean depth must be greater than 0. Got {mean_depth}."
    assert bulk_density is None or bulk_density >= 0, f"Bulk density must be between greater than 0. Got {bulk_density}."
    assert organic_carbon is None or (0 <= organic_carbon <= 100), f"Organic carbon must be between 0 and 100. Got {organic_carbon}."
    assert pH_H2O is None or (0 <= pH_H2O <= 14), f"pH_H2O must be between 0 and 14. Got {pH_H2O}."
    assert CACO3 is None or (0 <= CACO3 <= 100), f"Calcium carbonate must be between 0 and 100. Got {CACO3}."
    assert CEC is None or CEC >= 0, f"Cation exchange capacity must be greater than or equal to 0. Got {CEC}."

    predictors_py2r = {
        'sand' : 'USSAND',
        'silt' : 'USSILT',
        'clay' : 'USCLAY',
        'mean_depth' : 'DEPTH_M',
        'organic_carbon' : 'OC',
        'bulk_density' : 'BD',
        'CACO3' : 'CACO3',
        'pH_H2O' : 'PH_H2O',
        'CEC' : 'CEC',
    }

    local_vars = locals()

    # Prepare the predictors dictionary for R
    predictors = {k_r : local_vars[k_py] for k_py, k_r in predictors_py2r.items() if local_vars[k_py] is not None}
    predictor_names = tuple(predictors.keys())

    # Create a dictionary from the PTFs DataFrame
    ptf_df = pd.read_csv(f"{EUPTFV2_PATH}/list_of_final_PTFs.csv", sep=";")
    ptf_df["Predictor variables"] = ptf_df["Predictor variables"].str.split(" ").apply(tuple)
    predictors_to_ptf = ptf_df.set_index("Predictor variables").to_dict(orient="index")

    # Get the best PTFs to compute theta_fc and theta_wp
    fc_ptf = predictors_to_ptf[predictor_names]['FC']
    wp_ptf = predictors_to_ptf[predictor_names]['WP']
    
    # Prepend SAMPLE_ID = 1, X_WGS84 = 0., Y_WGS84 = 0. to the predictors
    predictors = {'SAMPLE_ID': 1, 'X_WGS84': 0., 'Y_WGS84': 0., **predictors}
    
    # Evaluate the PTFs using the predictors
    thetaFC = _eval_ptf("FC", fc_ptf, predictors)
    thetaWP = _eval_ptf("WP", wp_ptf, predictors)
    
    return thetaFC, thetaWP