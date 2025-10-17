"""
########################################################################
The weather.py module contains the Weather class, which provides I/O
tools for defining weather input data, as required for FAO-56
calculations.
########################################################################
"""

import pandas as pd
from . import refet
import numpy as np
from .tools.misc import read_comments

class Weather:
    """A class for managing weather data for FAO-56 calculations.

    Attributes
    ----------
    data : DataFrame
        Weather data dataframe
        index - Year and day of year as string ('yyyy-ddd')
        columns - ['Tmin','Tmax','Tmean','RHmin','RHmax','RHmean','Vapr','Tdew','Wndsp','Srad','Rain','z','lat','wndht','ETref']
            Tmin  - Daily minimum air temperature (deg C)
            Tmax  - Daily maximum air temperature (deg C)
            Tmean - Daily average air temperature (deg C)
            RHmin - Daily minimum relative humidity (%)
            RHmax - Daily maximum relative humidity (%)
            RHmean- Daily average relative humidity (%)
            Vapr  - Daily average vapor pressure (kPa)
            Tdew  - Daily average dew point temperature (deg C)
            Wndsp - Daily average wind speed (m/s)
            Srad  - Incoming solar radiation (MJ/m2)
            Rain  - Daily precipitation (mm)
            z     - Weather station elevation (z) (m)
            lat   - Weather station latitude (decimal degrees)
            wndht - Weather station wind speed measurement height (m)
            ETref - Daily reference ET (mm)
    """

    REQ_COLS = ['Tmin','Tmax','RHmin','RHmax','z','lat']
    COLS =     ['Tmin','Tmax','Tmean','RHmin','RHmax','RHmean','Vapr','Tdew','Wndsp','Srad','Rain','z','lat','wndht','clmt','loctn','ETref']

    def __init__(self, data, z=None, lat=None, wndht=2.0, clmt='dry', loctn='interior', **kwargs):
        """Initialize the Weather class attributes.

        Parameters
        ----------
        data : DataFrame
            Weather data
            * index - date ('YYYY-MM-DD')
            * columns - ['Tmin','Tmax','RHmin','RHmax','Vapr','Tdew','Wndsp','Srad','Rain','ETref']
            * * Tmax  - Daily maximum air temperature (°C) (REQUIRED)
            * * Tmin  - Daily minimum air temperature (°C) (REQUIRED)
            * * Tmean - Daily average air temperature (°C) (optional, but needed for get_phenology())
            * * RHmax - Daily maximum relative humidity (%) (REQUIRED)
            * * RHmin - Daily minimum relative humidity (%) (REQUIRED)
            * * RHmean- Daily average relative humidity (%) (optional)
            * * Vapr  - Daily average vapor pressure (kPa) (optional)
            * * Tdew  - Daily average dew point temperature (°C) (optional)
            * * Wndsp - Daily average wind speed (m/s) (optional)
            * * Srad  - Incoming solar radiation (MJ/m2) (optional)
            * * Rain  - Daily precipitation (mm) (optional, but needed for water balance)
            * * z     - Elevation (m) (REQUIRED)
            * * lat   - Latitude (dec deg) (REQUIRED)
            * * wndht - Wind height (m) (optional, defaults to 2.0)
            * * clmt  - Climate type - 'dry' or 'wet' (optional, defaults to 'dry')
            * * loctn - Location type - 'interior', 'coastal' or 'island' (optional, defaults to 'interior')
            * * ETref - Daily reference ET (mm) (optional, will be computed if missing)
        """

        # if given, add metadata to data
        if 'z' not in data.columns and z is not None:
            data['z'] = float(z)
        if 'lat' not in data.columns and lat is not None:
            data['lat'] = float(lat)
        if 'wndht' not in data.columns and wndht is not None:
            data['wndht'] = float(wndht)
        if 'clmt' not in data.columns and clmt is not None:
            data['clmt'] = clmt
        if 'loctn' not in data.columns and loctn is not None:
            data['loctn'] = loctn

        # check that required columns are present
        missing_req_cols = [col for col in self.REQ_COLS if col not in data.columns]
        assert len(missing_req_cols) == 0, f'Missing required columns: {missing_req_cols}'
        # check that required columns have no NaNs
        assert data[self.REQ_COLS].notna().all(axis=None), 'Required columns cannot have NaN values'
        # add missing columns
        for col in self.COLS:
            if col not in data.columns:
                data[col] = np.nan

        self.data = data[self.COLS] # reorder columns and delete extra columns
        self.data.index = pd.to_datetime(self.data.index, format='%Y-%m-%d')
        self.data.index.name = 'Date'

        # if NaNs are present in ETref, compute ETref for those dates
        for date in self.data.index:
            if np.isnan(self.data.loc[date,'ETref']):
                self.data.loc[date,'ETref'] = self.compute_etref(date)


    def compute_etref(self, date):
        """Compute ASCE standardized reference ET for data at index.

        Parameters
        ----------
        date : str
            Date

        Returns
        -------
        ETref : float
            Daily standardized reference evapotranspiration for the short or tall reference crop (mm)
        """
        return refet.ascedaily(
            rfcrp="S",
            z=self.data.loc[date,'z'],
            lat=self.data.loc[date,'lat'],
            doy=pd.to_datetime(date).dayofyear,
            tmax=self.data.loc[date,'Tmax'],
            tmin=self.data.loc[date,'Tmin'],
            israd=self.data.loc[date,'Srad'],
            vapr=self.data.loc[date,'Vapr'],
            tdew=self.data.loc[date,'Tdew'],
            rhmax=self.data.loc[date,'RHmax'],
            rhmin=self.data.loc[date,'RHmin'],
            wndsp=self.data.loc[date,'Wndsp'],
            wndht=self.data.loc[date,'wndht'] or 2.0,
            loctn=self.data.loc[date,'loctn'] or 'interior',
            clmt=self.data.loc[date,'clmt'] or 'dry'
        )


    def to_csv(self, path='pyfao56.wth'):
        """Save weather data to a CSV file.

        Parameters
        ----------
        filepath : str, optional
            Path to weather data file (default = 'pyfao56.wth')
        """

        with open(path, 'w') as f:
            # f.write(f'#z: {self.z}\n')
            # f.write(f'#lat: {self.lat}\n')
            # f.write(f'#wndht: {self.wndht}\n')
            # f.write(f'#rfcrp: {self.rfcrp}\n')
            # f.write(f'#clmt: {self.clmt}\n')
            # f.write(f'#loctn: {self.loctn}\n')
            self.data.to_csv(f)
    
    @classmethod
    def from_csv(cls, path):
        """
        Load weather data from a CSV file.
        NB: compatible with the old format of weather data files, which
        contained comments with metadata.

        Parameters
        ----------
        path : str, optional
            Path to weather data file
        """

        data = pd.read_csv(path, comment="#", index_col=0)
        for c in read_comments(path):
            k = c.split(': ')[0][1:]
            v = c.split(': ')[1]
            if k in ['z','lat','wndht']: data[k] = float(v)
            elif k in ['clmt','loctn']: data[k] = v
        return cls(data)
    
    def add_data(self, df):
        """Add data to the weather DataFrame.

        Parameters
        ----------
        df : DataFrame
            Data to be added
        """

        # check that required columns are present
        missing_req_cols = [col for col in self.REQ_COLS if col not in df.columns]
        assert len(missing_req_cols) == 0, f'Missing required columns: {missing_req_cols}'
        # check that required columns have no NaNs
        assert df[self.REQ_COLS].notna().all(axis=None), 'Required columns cannot have NaN values'
        # add missing columns
        for col in self.COLS:
            if col not in df.columns:
                df[col] = np.nan

        # add data to weather DataFrame
        self.data = pd.concat([self.data, df[self.COLS]], axis=0)
        self.data.index = pd.to_datetime(self.data.index, format='%Y-%m-%d')
        self.data.index.name = 'Date'

        # sort dates
        self.data = self.data.sort_index()

        # if NaNs are present in ETref, compute ETref for those dates
        for date in df.index:
            if np.isnan(self.data.loc[date,'ETref']):
                self.data.loc[date,'ETref'] = self.compute_etref(date)