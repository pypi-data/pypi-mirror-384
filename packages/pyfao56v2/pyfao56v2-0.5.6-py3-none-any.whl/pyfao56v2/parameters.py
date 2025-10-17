"""
########################################################################
The parameters.py module contains the Parameters class, which provides
I/O tools for defining input parameters for the pyfao56 model simulations.
########################################################################
"""

from .tools.lut import CROP, SOIL
from .tools.pheno import PHENO_SUPPORTED_CROPS
from .tools.misc import interp_ts
import pandas as pd
#from .tools.rosetta import apply_rosetta

class Parameters:
    """A class for managing input parameters for FAO-56 calculations

    Attributes
    ----------
    Kcbini : float
        Kcb Initial (FAO-56 Table 17)
    Kcbmid : float
        Kcb Mid (FAO-56 Table 17)
    Kcbend : float
        Kcb End (FAO-56 Table 17)
    Lini : int
        Length Stage Initial (days) (FAO-56 Table 11)
    Ldev : int
        Length Stage Development (days) (FAO-56 Table 11)
    Lmid : int
        Length Stage Mid (days) (FAO-56 Table 11)
    Lend : int
        Length Stage End (days) (FAO-56 Table 11)
    hini : float
        Plant Height Initial (m)
    hmax : float
        Plant Height Maximum (m) (FAO-56 Table 12)
    thetaFC : float, optional (if given in SoilProfile)
        Volumetric Soil Water Content, Field Capacity (cm3/cm3) [at maximum root zone depth]
    thetaWP : float, optional (if given in SoilProfile)
        Volumetric Soil Water Content, Wilting Point (cm3/cm3) [at maximum root zone depth]
    theta0 : float, optional (if given in SoilProfile)
        Volumetric Soil Water Content, Initial (cm3/cm3) [at maximum root zone depth]
    Zrini : float
        Rooting Depth Initial (m)
    Zrmax : float
        Rooting Depth Maximum (m) (FAO-56 Table 22)
    pbase : float
        Depletion Fraction (p) (FAO-56 Table 22)
    Ze : float
        Depth of surface evaporation layer (m) (FAO-56 Table 19 & p144)
    REW : float
        Total depth Stage 1 evaporation (mm) (FAO-56 Table 19)
    CN2 : int
        Curve Number for AWC II (ASCE (2016), Table 14-3, p452)
    Kcb_ts : pandas.Series
        Time series of Kcb values
    h_ts : pandas.Series
        Time series of plant height values
    Zr_ts : pandas.Series
        Time series of rooting depth values
    seeding_date : str (YYYY-MM-DD)
        Date of seeding (for the trapezoid Kcb curve)
    """

    def __init__(
        self,
        crop=None, # if crop is specified, the parameters (Kcb_ts, h_ts, Zr_ts, fc_ts, pbase) will be set to the default values for that crop
        soil=None, # if soil is specified, the parameters (thetaFC, thetaWP) will be set to the default values for that soil
        Kcbini=None,
        Kcbmid=None,
        Kcbend=None,
        Lini=None,
        Ldev=None,
        Lmid=None,
        Lend=None,
        hini=None,
        hmax=None,
        thetaFC=None,
        thetaWP=None,
        theta0=None,
        Zrini=None,
        Zrmax=None,
        pbase=None,
        Ze=None,
        REW=None,
        CN2=None,
        Kcb_ts=None,
        h_ts=None,
        Zr_ts=None,
        fc_ts=None,
        seeding_date=None,  # date of seeding (for the trapezoid Kcb curve)
        **kwargs
        ):

        # if crop is specified, override given function arguments and set them
        # to the default values for that crop
        if crop is not None:
            #assert Kcbini is None and Kcbmid is None and Kcbend is None and Lini is None and Ldev is None and Lmid is None and Lend is None and hini is None and hmax is None and Zrini is None and Zrmax is None and pbase is None and Kcb_ts is None and h_ts is None and Zr_ts is None and fc_ts is None, 'If crop is specified, all crop-related parameters must be None'
            assert crop in CROP.keys(), f"Crop '{crop}' not found in lookup table"
            Kcbini = Kcbini or CROP[crop]['Kcbini']
            Kcbmid = Kcbmid or CROP[crop]['Kcbmid']
            Kcbend = Kcbend or CROP[crop]['Kcbend']
            Lini = Lini or CROP[crop]['Lini']   # when the pheno.py module is used, Lini is the one computed by pheno.py and explicitly provided as argument
            Ldev = Ldev or CROP[crop]['Ldev']   # same as above
            Lmid = Lmid or CROP[crop]['Lmid']   # same as above
            Lend = Lend or CROP[crop]['Lend']   # same as above
            hini = hini or CROP[crop]['hini']
            hmax = hmax or CROP[crop]['hmax']
            Zrini = Zrini or CROP[crop]['Zrini']
            Zrmax = Zrmax or CROP[crop]['Zrmax']
            pbase = pbase or CROP[crop]['pbase']
        
        if soil is not None:
            assert thetaFC is None and thetaWP is None, 'If soil is specified, thetaFC and thetaWP must be None'
            assert soil in SOIL.keys(), f"Soil '{soil}' not found in lookup table"
            thetaFC, thetaWP, REW = SOIL[soil].values()

        if crop not in PHENO_SUPPORTED_CROPS:
            assert (Kcb_ts is not None) or (all([Kcbini,Kcbmid,Kcbend]) and all([Lini,Ldev,Lmid,Lend])), 'Kcb_ts or (Kcbini,Kcbmid,Kcbend,Lini,Ldev,Lmid,Lend) must be provided'
        assert (h_ts is not None) or all([hini,hmax]), 'h_ts or (hini,hmax) must be provided'
        assert (Zr_ts is not None) or all([Zrini,Zrmax]), 'Zr_ts or (Zrini,Zrmax) must be provided'
        if (Kcb_ts is None) or (h_ts is None) or (Zr_ts is None):
            assert seeding_date is not None, 'seeding_date must be provided when Kcb_ts, h_ts or Zr_ts are not provided'

        self.Kcbini  = Kcbini
        self.Kcbmid  = Kcbmid
        self.Kcbend  = Kcbend
        self.Lini    = Lini
        self.Ldev    = Ldev
        self.Lmid    = Lmid
        self.Lend    = Lend
        self.hini    = hini
        self.hmax    = hmax
        self.Zrini   = Zrini
        self.Zrmax   = Zrmax
        self.thetaFC = thetaFC
        self.thetaWP = thetaWP
        self.theta0  = theta0 or 0.5*(thetaFC+thetaWP) # if theta0 is not provided, set it to 0.5*(thetaFC+thetaWP)
        self.pbase   = pbase
        self.Ze      = Ze or 0.1
        self.REW     = REW or 8.0
        self.CN2     = CN2 or 70
        self.seeding_date = seeding_date

        # cast seeding_date to datetime
        if seeding_date is not None:
            self.seeding_date = pd.to_datetime(seeding_date, format='%Y-%m-%d')

        # if FAO56 parameters are provided, create time series for Kcb, h, and Zr from them
        if Kcb_ts is None:
            Kcb = [Kcbini, Kcbini, Kcbmid, Kcbmid, Kcbend]
            dates = [self.seeding_date]
            for L in [Lini, Ldev, Lmid, Lend]:
                dates.append(dates[-1] + pd.Timedelta(days=L))
            Kcb_ts = pd.Series(Kcb, index=dates)
        assert isinstance(Kcb_ts, pd.Series), f'Kcb_ts must be a pandas Series. Got {type(Kcb_ts)}'
        self.Kcb_ts = Kcb_ts
        self.Kcb_ts.index = pd.to_datetime(self.Kcb_ts.index)
        
        # since Kcbini is required for computing fc in model.py (as of now), we
        # set it to 0.15 or minimum Kcb value
        if Kcbini is None:
            self.Kcbini = min([0.15, self.Kcb_ts.min()])   

        if h_ts is None:
            h = [hini, hmax]
            if Lini is not None:
                dates = [self.seeding_date, self.seeding_date + pd.Timedelta(days=Lini+Ldev)] # FAO-56 page 279 (similar to Zr)
            else:
                dates = [self.seeding_date, Kcb_ts.idxmax()]
            h_ts = pd.Series(h, index=dates)
        assert isinstance(h_ts, pd.Series), f'h_ts must be a pandas Series. Got {type(h_ts)}'
        self.h_ts = h_ts.sort_index()
        self.h_ts.index = pd.to_datetime(self.h_ts.index, format='%Y-%m-%d')

        if Zr_ts is None:
            Zr = [Zrini, Zrmax]
            if Lini is not None:
                dates = [self.seeding_date, self.seeding_date + pd.Timedelta(days=Lini+Ldev)] # FAO-56 page 279
            else:
                dates = [self.seeding_date, Kcb_ts.idxmax()]
            Zr_ts = pd.Series(Zr, index=dates)
        assert isinstance(Zr_ts, pd.Series), f'Zr_ts must be a pandas Series. Got {type(Zr_ts)}'
        self.Zr_ts = Zr_ts.sort_index()
        self.Zr_ts.index = pd.to_datetime(self.Zr_ts.index, format='%Y-%m-%d')

        if fc_ts is not None:
            assert isinstance(fc_ts, pd.Series), f'fc_ts must be a pandas Series. Got {type(fc_ts)}'
            self.fc_ts = fc_ts.sort_index()
            self.fc_ts.index = pd.to_datetime(self.fc_ts.index, format='%Y-%m-%d')
        else:
            self.fc_ts = None


    def to_csv(self, path="pyfao56.par"):
        """Save pyfao56 parameters to a CSV file.

        Parameters
        ----------
        path : str, optional
            Any valid filepath string (default = 'pyfao56.par')
        """

        # create a Series with the time series and other params
        # Kcb_ts, h_ts, Zr_ts will be written as value1;value2;value3;...
        params = pd.Series({
            'Kcb': ';'.join(map(str, self.Kcb_ts)),
            'h': ';'.join(map(str, self.h_ts)),
            'Zr': ';'.join(map(str, self.Zr_ts)),
            'dates_Kcb': ';'.join(self.Kcb_ts.index.strftime("%Y-%m-%d")),
            'dates_h': ';'.join(self.h_ts.index.strftime("%Y-%m-%d")),
            'dates_Zr': ';'.join(self.Zr_ts.index.strftime("%Y-%m-%d")),
            'thetaFC': self.thetaFC,
            'thetaWP': self.thetaWP,
            'theta0': self.theta0,
            'pbase': self.pbase,
            'Ze': self.Ze,
            'REW': self.REW,
            'CN2': self.CN2,
            'start_date': self.start_date.strftime("%Y-%m-%d"),
            'end_date': self.end_date.strftime("%Y-%m-%d"),
        })

        # write the Series to a CSV file
        params.to_csv(path, header=False)
    
    @classmethod
    def from_csv(cls, path):
        """Load pyfao56 parameters from a CSV file.

        Parameters
        ----------
        filepath : str, optional
            Any valid filepath string
        """

        # read the CSV file as a Series
        params = pd.read_csv(path, header=None, index_col=0).squeeze()

        # extract the time series and other params
        Kcb_ts = pd.Series(map(float, params['Kcb'].split(';')))
        h_ts = pd.Series(map(float, params['h'].split(';')))
        Zr_ts = pd.Series(map(float, params['Zr'].split(';')))
        Kcb_ts.index = pd.to_datetime(params['dates_Kcb'].split(';'))
        h_ts.index = pd.to_datetime(params['dates_h'].split(';'))
        Zr_ts.index = pd.to_datetime(params['dates_Zr'].split(';'))

        # return Parameters object
        return cls(
            Kcb_ts=Kcb_ts,
            h_ts=h_ts,
            Zr_ts=Zr_ts,
            thetaFC=float(params['thetaFC']),
            thetaWP=float(params['thetaWP']),
            theta0=float(params['theta0']),
            pbase=float(params['pbase']),
            Ze=float(params['Ze']),
            REW=float(params['REW']),
            CN2=int(params['CN2']),
            start_date=params['start_date'],
            end_date=params['end_date'],
        )
    
    def get_Kcb(self, date): return interp_ts(self.Kcb_ts, date)
    def get_max_Kcb(self): return self.Kcb_ts.max()

    def get_h(self, date): return interp_ts(self.h_ts, date)
    def get_max_h(self): return self.h_ts.max()

    def get_Zr(self, date): return interp_ts(self.Zr_ts, date)
    def get_max_Zr(self): return self.Zr_ts.max()

    def get_fc(self, date):
        if self.fc_ts is not None:
            return interp_ts(self.fc_ts, date)
        else:
            return None
    def get_max_fc(self):
        if self.fc_ts is not None:
            return self.fc_ts.max()
        else:
            return None