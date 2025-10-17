from rosetta import rosetta, SoilData
from .van_genuchten import VangenuchtenTheta

def apply_rosetta(sand, silt, clay, bulk_density=None, th33=None, th1500=None, v=3):
    """Apply ROSETTA PTF to estimate soil properties from soil texture data.

    Parameters
    ----------
    sand : float
        Percent sand content in the soil.
    silt : float
        Percent silt content in the soil.
    clay : float
        Percent clay content in the soil.
    bulk_density : float, optional
        Bulk density of the soil (g/cm3).
    th33 : float, optional
        Volumetric water content at -33 kPa (cm3/cm3).
    th1500 : float, optional
        Volumetric water content at -1500 kPa (cm3/cm3).
    v : int, optional
        Version of the Rosetta models to use (default is 3).

    Returns
    -------
    thetaFC : float
        Volumetric water content at field capacity (cm3/cm3).
    thetaWP : float
        Volumetric water content at wilting point (cm3/cm3).
    """

    # use ROSETTA to estimate soil properties (i.e. van Genuchten model params)
    # https://cales.arizona.edu/research/rosetta/download/rosetta.pdf
    # https://github.com/usda-ars-ussl/rosetta-soil
    #
    # The Rosetta pedotransfer function predicts five parameters for the van
    # Genuchten model of unsaturated soil hydraulic properties:
    # - theta_r : residual volumetric water content
    # - theta_s : saturated volumetric water content
    # - log10(alpha) : retention shape parameter [log10(1/cm)]
    # - log10(n) : retention shape parameter
    # - log10(ksat) : saturated hydraulic conductivity [log10(cm/d)]
    #
    # Rosetta provides four models for predicting the five parameters from
    # soil characterization data. The models differ in the required input
    # data:
    # Model Code	Input Data
    #          2	sa, si, cl (SSC)
    #          3	SSC, bulk density (BD)
    #          4	SSC, BD, th33
    #          5	SSC, BD, th33, th1500
    # where:
    # - sa, si, cl are percentages of sand, silt and clay
    # - BD is soil bulk density (g/cm3)
    # - th33 is the soil volumetric water content at 33 kPa
    # - th1500 is the soil volumetric water content at 1500 kPa
    # Three versions of Rosetta are available. The versions effectively
    # represent three alternative calibrations of the four Rosetta models.

    """ ONLINE VERSION
    data = {"soildata": [[sand, silt, clay]]}
    rosetta_api = lambda version: f"http://www.handbook60.org/api/v1/rosetta/{version}"
    van_genuchten_params = requests.post(rosetta_api(3), json=data).json()["van_genuchten_params"][0]
    """

    assert not any([sand is None, silt is None, clay is None]), "Sand, silt, and clay must all be provided."
    assert 0 <= sand <= 100, f"Sand content must be between 0 and 100. Got {sand}."
    assert 0 <= silt <= 100, f"Silt content must be between 0 and 100. Got {silt}."
    assert 0 <= clay <= 100, f"Clay content must be between 0 and 100. Got {clay}."
    assert 99 <= sand + silt + clay <= 100, f"Sum of sand, silt, and clay must be around 100. Got {sand + silt + clay}."
    assert bulk_density is None or bulk_density >= 0, f"Bulk density must be between greater than 0. Got {bulk_density}."
    assert th33 is None or (0 <= th33 <= 1), f"th33 must be between 0 and 1. Got {th33}."
    assert th1500 is None or (0 <= th1500 <= 1), f"th1500 must be between 0 and 1. Got {th1500}."
    assert v in [1,2,3], f"Version number must be 1, 2, or 3. Got {v}."

    texture = [sand,silt,clay]
    if bulk_density is not None:
        texture.append(bulk_density)
    if th33 is not None and th1500 is not None:
        texture.append(th33)
        texture.append(th1500)

    mean, stdev, codes = rosetta(v, SoilData.from_array([texture]))
    van_genuchten_params = {
        "theta_r": mean[0][0],
        "theta_s": mean[0][1],
        "alpha": 10**mean[0][2],
        "n": 10**mean[0][3],
        #"Ks": 10**mean[0][4]
    }

    # derive theta_fc and theta_wp from the van Genuchten model
    vg = VangenuchtenTheta(**van_genuchten_params)
    thetaFC = vg(-330)
    thetaWP = vg(-15000)

    return thetaFC, thetaWP