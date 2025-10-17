from .tools.misc import *
from .weather import Weather
from .parameters import Parameters
from .irrigation import Irrigation
from .autoirrigate import AutoIrrigate
from .model import Model
from .tools.rosetta import apply_rosetta
try:
    from .tools.euptfv2 import apply_euptfv2
    EUPTFV2_AVAILABLE = True
except ImportError:
    # it happens when rpy2 package is not installed
    import warnings
    warnings.warn("EUPTFV2 is not available, as rpy2 package is not installed. ROSETTA will be used instead.")
    EUPTFV2_AVAILABLE = False
from .tools.pheno import PHENO_SUPPORTED_CROPS, get_phenology
import warnings
import yaml
# import pandas as pd


def simulate(yaml_path=None, **kwargs):

    ########## PARSE ARGUMENTS ##########

    args = {}
    if yaml_path is not None:
        # read arguments from yaml file
        with open(yaml_path, 'r') as f:
            args.update(yaml.safe_load(f))
    # override arguments with given arguments
    args.update(kwargs)

    # TODO remove deprecated arguments in v1.0.0
    if "fao_class" in args:
        args["variety"] = args["fao_class"]
        warnings.warn("The 'fao_class' argument is deprecated. Use 'variety' instead.")
        del args["fao_class"]

    # Check that minimum weather data is provided
    if args.get("wth_path") is None and args.get("wth_data") is None:
        raise ValueError("Weather data must be provided either as a path or as a DataFrame.")
    
    # Check that minimum crop parameters are provided
    if args.get("crop") is None:
        raise ValueError("Crop parameters must be provided.")
    
    # Check that at least one among (thetaFC, thetaWP) or (sand, silt, clay) is provided
    if not all([args.get("thetaFC"), args.get("thetaWP")]) and not all([args.get("sand"), args.get("silt"), args.get("clay")]):
        raise ValueError("Either (thetaFC, thetaWP) or (sand, silt, clay) must be provided.")
    
    # Check that start and end dates are provided
    if args.get("start") is None or args.get("end") is None:
        raise ValueError("Start and end dates must be provided.")


    ########## WEATHER DATA ##########

    # Order of preference for weather data:
    # 1. read from provided file
    # 2. read from provided DataFrame
    if args.get("wth_path") is not None:
        ### read weather data from csv file
        wth = Weather.from_csv(args["wth_path"])
    else:
        ### read weather data from given arguments
        wth = Weather(
            data=args.get("wth_data"),  # pd.DataFrame
            z=args.get("z"),
            lat=args.get("lat"),
            wndht=args.get("wndht"),
            clmt=args.get("clmt"),
            loctn=args.get("loctn"),
        )



    ########## CROP AND SOIL PARAMETERS ##########

    if args.get("par_path") is not None:
        ### read crop parameters from csv file
        par = Parameters.from_csv(args["par_path"])
    else:
        ### read crop parameters from given arguments
        if not args.get("thetaFC") or not args.get("thetaWP"):
            # if thetaFC or thetaWP are not provided, calculate them from soil
            # texture (and bulk density, if available)
            if EUPTFV2_AVAILABLE and args.get("mean_depth") is not None:
                # if mean sampling depth is provided, use euptfv2
                args["thetaFC"], args["thetaWP"] = apply_euptfv2(
                    sand = args["sand"],
                    silt = args["silt"],
                    clay = args["clay"],
                    mean_depth = args["mean_depth"],
                    bulk_density = args.get("bulk_density"),
                    organic_carbon = args.get("organic_matter"),
                    pH_H2O = args.get("pH_H2O"),
                    CACO3 = args.get("CACO3"),
                    CEC = args.get("CEC"),
                )
            else:
                # if mean sampling depth is not provided, use rosetta
                args["thetaFC"], args["thetaWP"] = apply_rosetta(
                    sand = args["sand"],
                    silt = args["silt"],
                    clay = args["clay"],
                    bulk_density = args.get("bulk_density")
                    )
        
        # Order of preference for phenology stage length parameters:
        # 1. provided by user
        # 2. predicted by phenology module (if crop is supported)
        # 3. default values in the look-up table (managed directly in the Parameters class)
        if args["crop"] in PHENO_SUPPORTED_CROPS and not all([args.get(L) for L in ["Lini", "Ldev", "Lmid", "Lend"]]):
            # if crop is provided and is supported by the phenology module, use it
            # to calculate the phenology parameters
            T_mean = args.get("T_mean") or wth.data["Tmean"]
            try:
                args["Lini"], args["Ldev"], args["Lmid"], args["Lend"] = get_phenology(args["crop"], T_mean, seeding_date=args.get("seeding_date"), fao_class=args.get("variety"))
            except AssertionError as e:
                warnings.warn(str(e))
                # if phenology prediction fails, use provided parameters (if any) OR at worst use the default values in the look-up table
                # NB: last version of the code forced the user to provide Lini, Ldev, Lmid, Lend explicitly if phenology prediction failed
                #assert None not in [args.get("Lini"), args.get("Ldev"), args.get("Lmid"), args.get("Lend")], "Phenology parameters could neither be predicted nor were provided"

        par = Parameters(
            crop=args.get("crop"),                  # str
            soil=args.get("soil"),                  # str
            Kcbini=args.get("Kcbini"),              # float
            Kcbmid=args.get("Kcbmid"),              # float
            Kcbend=args.get("Kcbend"),              # float
            Lini=args.get("Lini"),                  # int
            Ldev=args.get("Ldev"),                  # int
            Lmid=args.get("Lmid"),                  # int
            Lend=args.get("Lend"),                  # int
            hini=args.get("hini"),                  # float
            hmax=args.get("hmax"),                  # float
            Zrini=args.get("Zrini"),                # float
            Zrmax=args.get("Zrmax"),                # float
            thetaFC=args.get("thetaFC"),            # float
            thetaWP=args.get("thetaWP"),            # float
            theta0=args.get("theta0"),              # float
            pbase=args.get("pbase"),                # float
            Ze=args.get("Ze"),                      # float (defaults to 0.1)
            REW=args.get("REW"),                    # float (defaults to 8.0)
            CN2=args.get("CN2"),                    # int (defaults to 70)
            Kcb_ts=args.get("Kcb_ts"),              # pd.Series
            h_ts=args.get("h_ts"),                  # pd.Series
            Zr_ts=args.get("Zr_ts"),                # pd.Series
            seeding_date=args.get("seeding_date")   # str
        )
    


    ########## IRRIGATION DATA ##########

    if args.get("irr_path") is not None:
        ### read irrigation data from csv file
        irr = Irrigation.from_csv(args["irr_path"])
    elif args.get("irr_data") is not None:
        ### read irrigation data from given arguments
        irr = Irrigation(
            data=args["irr_data"]       # pd.DataFrame
        )
    else:
        ### no irrigation data provided
        irr = None
    


    ########## AUTOIRRIGATION RULES ##########

    if args.get("autoirr_path") is not None:
        ### read autoirrigation rules from csv file
        autoirr = AutoIrrigate.from_csv(args["autoirr_path"])
    elif args.get("autoirr_rules") is not None:
        ### read autoirrigation rules from given list of dicts
        autoirr = AutoIrrigate.from_rules(
            args["autoirr_rules"]       # list of dicts (see autoirrigate.py for details)
        )
    else:
        ### no autoirrigation rules provided
        autoirr = None
    


    ########## RUN SIMULATION ##########

    model = Model(
        start=args.get("start"),
        end=args.get("end"),
        par=par,
        wth=wth,
        irr=irr,
        autoirr=autoirr,
        sol=None,
        upd=None,
        roff=False,
        cons_p=False,
        aq_Ks=False,
    )
    model.run()

    return model.data



"""
# EXAMPLE OF USAGE
df = simulate(
    ### GENERAL PARAMETERS
    start="2024-04-25",
    end="2024-09-18",
    yaml_path=None, # NB: yaml arguments will be overridden by provided arguments
    ### CROP PARAMETERS
    crop="maize",
    Lini=16,
    Ldev=68,
    Lmid=24,
    Lend=38,
    variety="FAO 500",
    seeding_date="2024-04-25",
    ### SOIL PARAMETERS
    sand=47.1,  # when thetaFC and thetaWP are not provided, they are calculated from soil texture
    silt=34.4,
    clay=18.5,
    ### WEATHER DATA
    wth_data=pd.read_csv("data/sample/pyfao56.wth", comment="#", index_col=0),   # or directly the path: wth_path="pyfao56.wth"
    z=203.0,
    lat=44.309125,
    wndht=2.0,
    clmt="dry",
    loctn="interior",
    ### IRRIGATION DATA
    irr_data=pd.read_csv("data/sample/pyfao56.irr", comment="#", index_col=0),   # or directly the path: irr_path="data/pyfao56.irr"
    ### AUTOIRRIGATION RULES
    autoirr_rules=[{
        'start': '2024-04-25',  # start date of autoirrigation rule
        'end': '2024-09-18',    # end date of autoirrigation rule
        'idow': '0',    # autoirrigate only on monday
        'mad': 0.5,     # autoirrigation trigger: fractional root-zone soil water depletion (fDr) >= 0.5 [mm/mm]
        'itfdr': 0.2,   # autoirrigation target: fDr = 0.2 [mm/mm]
        'imax': 30.0,   # limit autoirrigation to <= 30 mm
        'ieff': 75.0,   # autoirrigation efficiency
        'fw': 1.0       # fraction of soil surface wetted by autoirrigation
        }], # add more rules in other date ranges, if needed
)

df.to_csv("data/sample/pyfao56.out", float_format='%.3f')
"""



class WaterBalance:
    def __init__(self, yaml_path=None, **kwargs):

        ########## PARSE ARGUMENTS ##########

        args = {}
        if yaml_path is not None:
            # read arguments from yaml file
            with open(yaml_path, 'r') as f:
                args.update(yaml.safe_load(f))
        # override arguments with given arguments
        args.update(kwargs)

        # TODO remove deprecated arguments in v1.0.0
        if "fao_class" in args:
            args["variety"] = args["fao_class"]
            warnings.warn("The 'fao_class' argument is deprecated. Use 'variety' instead.")
            del args["fao_class"]

        # Check that minimum weather data is provided
        if args.get("wth_path") is None and args.get("wth_data") is None:
            raise ValueError("Weather data must be provided either as a path or as a DataFrame.")
        
        # Check that minimum crop parameters are provided
        if args.get("crop") is None:
            raise ValueError("Crop parameters must be provided.")
        
        # Check that at least one among (thetaFC, thetaWP) or (sand, silt, clay) is provided
        if not all([args.get("thetaFC"), args.get("thetaWP")]) and not all([args.get("sand"), args.get("silt"), args.get("clay")]):
            raise ValueError("Either (thetaFC, thetaWP) or (sand, silt, clay) must be provided.")
        
        # Check that start and end dates are provided
        if args.get("start") is None or args.get("end") is None:
            raise ValueError("Start and end dates must be provided.")
    

        ########## WEATHER DATA ##########

        # Order of preference for weather data:
        # 1. read from provided file
        # 2. read from provided DataFrame
        if args.get("wth_path") is not None:
            ### read weather data from csv file
            self.wth = Weather.from_csv(args["wth_path"])
        else:
            ### read weather data from given arguments
            self.wth = Weather(
                data=args.get("wth_data"),  # pd.DataFrame
                z=args.get("z"),
                lat=args.get("lat"),
                wndht=args.get("wndht"),
                clmt=args.get("clmt"),
                loctn=args.get("loctn"),
            )


        ########## CROP AND SOIL PARAMETERS ##########

        if args.get("par_path") is not None:
            ### read crop parameters from csv file
            self.par = Parameters.from_csv(args["par_path"])
        else:
            ### read crop parameters from given arguments
            if not args.get("thetaFC") or not args.get("thetaWP"):
                # if thetaFC or thetaWP are not provided, calculate them from soil
                # texture (and bulk density, if available)
                if EUPTFV2_AVAILABLE and args.get("mean_depth") is not None:
                    # if mean sampling depth is provided, use euptfv2
                    args["thetaFC"], args["thetaWP"] = apply_euptfv2(
                        sand = args["sand"],
                        silt = args["silt"],
                        clay = args["clay"],
                        mean_depth = args["mean_depth"],
                        bulk_density = args.get("bulk_density"),
                        organic_carbon = args.get("organic_matter"),
                        pH_H2O = args.get("pH_H2O"),
                        CACO3 = args.get("CACO3"),
                        CEC = args.get("CEC"),
                    )
                else:
                    # if mean sampling depth is not provided, use rosetta
                    args["thetaFC"], args["thetaWP"] = apply_rosetta(
                        sand = args["sand"],
                        silt = args["silt"],
                        clay = args["clay"],
                        bulk_density = args.get("bulk_density")
                        )
                    
            # Order of preference for phenology stage length parameters:
            # 1. provided by user
            # 2. predicted by phenology module (if crop is supported)
            # 3. default values in the look-up table (managed directly in the Parameters class)
            if args["crop"] in PHENO_SUPPORTED_CROPS and not all([args.get(L) for L in ["Lini", "Ldev", "Lmid", "Lend"]]):
                # if crop is provided and is supported by the phenology module, use it
                # to calculate the phenology parameters
                T_mean = args.get("T_mean") or self.wth.data["Tmean"]
                try:
                    args["Lini"], args["Ldev"], args["Lmid"], args["Lend"] = get_phenology(args["crop"], T_mean, seeding_date=args.get("seeding_date"), fao_class=args.get("variety"))
                except AssertionError as e:
                    warnings.warn(str(e))
                    # if phenology prediction fails, use provided parameters (if any) OR at worst use the default values in the look-up table
                    # NB: last version of the code forced the user to provide Lini, Ldev, Lmid, Lend explicitly if phenology prediction failed
                    #assert None not in [args.get("Lini"), args.get("Ldev"), args.get("Lmid"), args.get("Lend")], "Phenology parameters could neither be predicted nor were provided"

            self.par = Parameters(
                crop=args.get("crop"),                  # str
                soil=args.get("soil"),                  # str
                Kcbini=args.get("Kcbini"),              # float
                Kcbmid=args.get("Kcbmid"),              # float
                Kcbend=args.get("Kcbend"),              # float
                Lini=args.get("Lini"),                  # int
                Ldev=args.get("Ldev"),                  # int
                Lmid=args.get("Lmid"),                  # int
                Lend=args.get("Lend"),                  # int
                hini=args.get("hini"),                  # float
                hmax=args.get("hmax"),                  # float
                Zrini=args.get("Zrini"),                # float
                Zrmax=args.get("Zrmax"),                # float
                thetaFC=args.get("thetaFC"),            # float
                thetaWP=args.get("thetaWP"),            # float
                theta0=args.get("theta0"),              # float
                pbase=args.get("pbase"),                # float
                Ze=args.get("Ze"),                      # float (defaults to 0.1)
                REW=args.get("REW"),                    # float (defaults to 8.0)
                CN2=args.get("CN2"),                    # int (defaults to 70)
                Kcb_ts=args.get("Kcb_ts"),              # pd.Series
                h_ts=args.get("h_ts"),                  # pd.Series
                Zr_ts=args.get("Zr_ts"),                # pd.Series
                seeding_date=args.get("seeding_date")   # str
            )
    

        ########## IRRIGATION DATA ##########

        if args.get("irr_path") is not None:
            ### read irrigation data from csv file
            self.irr = Irrigation.from_csv(args["irr_path"])
        elif args.get("irr_data") is not None:
            ### read irrigation data from given arguments
            self.irr = Irrigation(
                data=args["irr_data"]       # pd.DataFrame
            )
        else:
            ### no irrigation data provided
            self.irr = None
        


        ########## AUTOIRRIGATION RULES ##########

        if args.get("autoirr_path") is not None:
            ### read autoirrigation rules from csv file
            self.autoirr = AutoIrrigate.from_csv(args["autoirr_path"])
        elif args.get("autoirr_rules") is not None:
            ### read autoirrigation rules from given list of dicts
            self.autoirr = AutoIrrigate.from_rules(
                args["autoirr_rules"]       # list of dicts (see autoirrigate.py for details)
            )
        else:
            ### no autoirrigation rules provided
            self.autoirr = None
    

        ########## MODEL ##########

        self.start = args["start"]
        self.end = args["end"]

        self.model = Model(
            start=self.start,
            end=self.end,
            par=self.par,
            wth=self.wth,
            irr=self.irr,
            autoirr=self.autoirr,
            sol=None,
            upd=None,
            roff=False,
            cons_p=False,
            aq_Ks=False,
        )

    
    def simulate(self):
        # run the simulation
        self.model.run()
        # return the water balance time series data
        self.data = self.model.data
        return self.data