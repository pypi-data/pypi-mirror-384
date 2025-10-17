"""
########################################################################
The autoirrigate.py module contains the AutoIrrigate class, which
provides I/O tools for defining conditions for scheduling irrigation
automatically in pyfao56.
########################################################################
"""

import pandas as pd

class AutoIrrigate:
    """A class for managing multiple sets of autoirrigation conditions

    Attributes
    ----------
    data : DataFrame
        AutoIrrigate data with mixed data types
        * index - counter as int
        * columns - ['start','end','alre','idow','fpdep','fpday','fpact',
                   'mad','madDr','ksc','dsli','dsle','evnt','icon',
                   'itdr','itfdr','ietrd','ietri','ietre','ettyp',
                   'iper','ieff','imin','imax','fw']

        Variables to determine if autoirrigation occurs or not:
        * * start - Autoirrigate only on start date or later
                    (str, 'yyyy-ddd')
        * * end   - Autoirrigate only on end date or earlier
                    (str, 'yyyy-ddd')
        * * alre  - Autoirrigate only after last reported irrigation
                    event (boolean)
        * * idow  - Autoirrigate only on specified days of the week
                    (str, e.g. '0123456'; default is all days)
                    0=sun, 1=mon, 2=tue, 3=wed, 4=thu, 5=fri, 6=sat
        * * fpdep - Threshold for cumulative forecasted precipitation depth
                    (float, mm; default: 10.)
        * * fpday : Number of days to consider for computing the cumulative
                    forecasted precipitation depth
                    (int, days; default: 1)
        * * fpact : Action if forecasted precip is above threshold:
                    None (default) - Proceed to autoirrigate anyway if needed
                    'cancel' - Do not autoirrigate
                    'reduce' - Deduct forecasted precip from autoirrigation amount
        * * mad   - Management allowed depletion (float, mm/mm)
                    Autoirrigate if fractional root-zone soil water
                    depletion (fDr) >= mad
        * * madDr - Management allowed depletion (float, mm)
                    Autoirrigate if root-zone soil water depletion (Dr) >= madDr
        * * ksc   - Critical value for transpiration reduction factor Ks
                    (float, 0-1, 1:full transpiration, 0:no trans.)
                    Autoirrigate if Ks <= ksc
        * * dsli  - Days since last irrigation event
                    (float, days)
                    Autoirrigate if days since last irrigation >= dsli
        * * dsle  - Days since last watering event, considering both
                    eff. precip and eff. irrigation (float, days)
                    Autoirrigate if days since last watering event >= dsle
        * * evnt  - Minimum depth of effective precipitation and
                    effective irrigation to be considered a watering
                    event (float, mm)

        The default autoirrigation amount is root-zone soil water depletion (Dr,
        mm). Variables to alter this irrigation amount are as follows:
        * * icon  - Apply a constant autoirrigation amount (float, mm)
        * * itdr  - Target a specfic root-zone soil water depletion (Dr)
                    following autoirrigation (float, mm)
        * * itfdr - Target a specific fractional root-zone soil water
                    depletion following autoirrigation (float, mm/mm)
        * * ietrd - Replace ET minus effective precipitation from the
                    past given number of days (int, days)
        * * ietri - Replace ET minus effective precipitation since the
                    last irrigation event (boolean)
        * * ietre - Replace ET minus effective precipitation since the
                    last watering event (boolean)
        * * ettyp - Specify type of ET to adjust, when one among ietrd, ietri or ietre is specified
                    'ETcadj' (default) - Replace ETcadj less precip
                    'ETc' - Replace ETc less precip
        * * iper  - Adjust the autoirrigation amount by a fixed
                    percentage (float, %)
        * * ieff  - Consider an application efficiency for
                    autoirrigation (float, %; default: same as
                    irrigation efficiency)
        * * imin  - Limit autoirrigation to >= minimum amount (float,mm)
        * * imax  - Limit autoirrigation to <= maximum amount (float,mm)
        * * fw    - Fraction of soil surface wetted (FAO-56 Table 20; default: 1.0)
    """

    COLS = ['start','end','alre','idow','fpdep','fpday',
            'fpact','mad','madDr','ksc','dsli','dsle','evnt',
            'icon','itdr','itfdr','ietrd','ietri','ietre',
            'ettyp','iper','ieff','imin','imax','fw']

    def __init__(self, data=None, **kwargs):
        """Initialize the AutoIrrigate class attributes.

        Parameters
        ----------
        data : DataFrame, optional
            AutoIrrigation rules
            columns - ['start','end','alre','idow','fpdep','fpday',
                       'fpact','mad','madDr','ksc','dsli','dsle','evnt',
                       'icon','itdr','itfdr','ietrd','ietri','ietre',
                       'ettyp','iper','ieff','imin','imax','fw']
        """
        
        self.data = pd.DataFrame(columns=self.COLS)

        if data is not None:
            assert set(data.columns).issubset(set(self.COLS)), 'Invalid column names are present'
            # add missing columns with NaN values
            self.data = pd.concat([self.data, data])
        
        # cast start and end columns to datetime
        self.data['start'] = pd.to_datetime(self.data['start'])
        self.data['end'] = pd.to_datetime(self.data['end'])


    def add_rule(self, start, end, alre=True, idow='0123456', fpdep=10.,
                fpday=1, fpact=None, mad=float('NaN'),
                madDr=float('NaN'), ksc=float('NaN'), dsli=float('NaN'),
                dsle=float('NaN'), evnt=10., icon=None,
                itdr=None, itfdr=None, ietrd=None,
                ietri=False, ietre=False, ettyp='ETcadj', iper=None,
                ieff=None, imin=None, imax=None, fw=1.0):
        """Add an autoirrigation rule for the given date range"""

        # check that no other rule is already present for the given date range
        if not self.data.empty:
            assert not ((self.data['start'] <= pd.to_datetime(end)) &
                        (self.data['end'] >= pd.to_datetime(start))).any(), \
                f'Rule already exists for the given date range: {start} to {end}'
        # check that the start and end dates are valid
        assert isinstance(start, str), f'start must be a string. Got type {type(start)}'
        assert isinstance(end, str), f'end must be a string. Got type {type(end)}'
        assert pd.to_datetime(start, format='%Y-%m-%d', errors='coerce') is not pd.NaT, \
            f'start must be a valid date string in the format yyyy-mm-dd. Got {start}'
        assert pd.to_datetime(end, format='%Y-%m-%d', errors='coerce') is not pd.NaT, \
            f'end must be a valid date string in the format yyyy-mm-dd. Got {end}'
        assert pd.to_datetime(start) <= pd.to_datetime(end), \
            f'start date must be before end date. Got {start} and {end}'
        # various checks on given arguments
        assert isinstance(alre, bool), f'alre must be a boolean. Got type {type(alre)}'
        assert isinstance(idow, str), f'idow must be a string. Got type {type(idow)}'
        assert len(idow) <= 7, f'idow must be a string of at most 7 numbers. Got {idow}'
        assert all(c in '0123456' for c in idow), \
            f'idow must be a string containing numbers in 0,...,6. Got {idow}'
        assert fpact is None or fpact in ['cancel', 'reduce'], \
            f'Invalid value for fpact. Must be None, "cancel", or "reduce". Got {fpact}'
        assert isinstance(fpday, int), f'fpday must be an integer. Got type {type(fpday)}'
        assert fpday >= 0, f'fpday must be >= 0. Got {fpday}'
        assert fpdep >= 0, f'fpdep must be >= 0. Got {fpdep}'
        if ieff is not None:
            assert isinstance(ieff, (int, float)), \
                f'ieff must be an integer or float. Got type {type(ieff)}'
            assert 0 <= ieff <= 100, f'ieff must be between 0 and 100. Got {ieff}'
            f'ieff must be between 0 and 100. Got {ieff}'
        if imin is not None:
            assert isinstance(imin, (int, float)), \
                f'imin must be an integer or float. Got type {type(imin)}'
            assert imin >= 0, f'imin must be >= 0. Got {imin}'
        if imax is not None:
            assert isinstance(imax, (int, float)), \
                f'imax must be an integer or float. Got type {type(imax)}'
            assert imax >= 0, f'imax must be >= 0. Got {imax}'
        if imin is not None and imax is not None:
            assert imin <= imax, f'imax must be >= imin. Got {imin} and {imax}'
        if fw is not None:
            assert isinstance(fw, (int, float)), \
                f'fw must be an integer or float. Got type {type(fw)}'
            assert 0 <= fw <= 1, f'fw must be between 0 and 1. Got {fw}'
        if ietrd is not None:
            assert isinstance(ietrd, int), \
                f'ietrd must be an integer. Got type {type(ietrd)}'
            assert ietrd >= 0, f'ietrd must be >= 0. Got {ietrd}'
        assert sum([
            (icon is not None), (itdr is not None), (itfdr is not None),
            (ietrd is not None), (ietri is True), (ietre is True)
            ]) == 1, \
            'Exactly one among icon, itdr, itfdr, ietrd, ietri or ietre must be specified'
        assert ettyp in ['ETcadj', 'ETc'], \
            f'Invalid value for ettyp. Must be "ETcadj" or "ETc". Got {ettyp}'
        


        rule = dict(
            start=pd.to_datetime(start, format='%Y-%m-%d'),
            end=pd.to_datetime(end, format='%Y-%m-%d'),
            alre=alre, idow=idow, fpdep=fpdep,
            fpday=fpday, fpact=fpact, mad=mad, madDr=madDr, ksc=ksc,
            dsli=dsli, dsle=dsle, evnt=evnt, icon=icon, itdr=itdr,
            itfdr=itfdr, ietrd=ietrd, ietri=ietri, ietre=ietre,
            ettyp=ettyp, iper=iper, ieff=ieff, imin=imin, imax=imax,
            fw=fw,
        )
        
        self.data = pd.concat([self.data, pd.DataFrame([rule])])
    

    def to_csv(self, path='pyfao56.airr'):
        """Save autoirrigation data to csv file

        Parameters
        ----------
        path : str
            Filepath for saving the autoirrigation data
        """

        self.data.to_csv(path, index=False)
    
    @classmethod
    def from_csv(cls, path):
        """Load autoirrigation data from csv file

        Parameters
        ----------
        path : str
            Filepath for loading the autoirrigation data

        Returns
        -------
        AutoIrrigate
            AutoIrrigate class object
        """

        data = pd.read_csv(path)
        return cls(data)
    
    @classmethod
    def from_rules(cls, rules):
        """Load autoirrigation data from a list of rules

        Parameters
        ----------
        rules : list
            List of dictionaries containing autoirrigation rules, e.g.:
            [{'start': '2020-01-01', 'end': '2020-12-31', 'alre': True, ...}, ...]

        Returns
        -------
        AutoIrrigate
            AutoIrrigate class object
        """

        #data = pd.DataFrame(rules)
        #return cls(data)
        airr = cls()
        for rule in rules:
            airr.add_rule(**rule)
        return airr