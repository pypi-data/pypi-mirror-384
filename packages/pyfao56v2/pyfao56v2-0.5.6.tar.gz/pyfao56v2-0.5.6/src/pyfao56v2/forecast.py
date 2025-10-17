"""
########################################################################
The forecast.py module contains the Forecast class, which is used to
retrieve weather forecasts from OpenMeteo.
########################################################################
"""

import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from .weather import Weather
from math import log



class Forecast:
    def __init__(
            self, lat, lon, z=None, wndht=2.0, rfcrp='S', clmt='dry', loctn='interior',
            cache_dir='.cache', expire_after=3600, retries=5, backoff_factor=0.2,
            **kwargs
            ):
        """Initialize the Forecast class attributes.

        Parameters
        ----------
        lat : float
            Weather station latitude (decimal degrees)
        lon : float
            Weather station longitude (decimal degrees)
        z : float, optional
            Weather station elevation (z) (m)
        wndht : float, optional
            Weather station wind speed measurement height (m)
        rfcrp : str, optional
            Type of reference crop  - Short ('S') or Tall ('T')
        clmt : str, optional
            Climate type - 'dry' or 'wet'
        loctn : str, optional
            Location type - 'coastal' or 'interior'
        cache_dir : str, optional
            Directory to store the cache (default = '.cache')
        expire_after : int, optional
            Cache expiration time (default = 3600)
        retries : int, optional
            Number of retries on error (default = 5)
        backoff_factor : float, optional
            Backoff factor for retries (default = 0.2)
        """
        
        self.lat = lat
        self.lon = lon
        self.z = z
        self.wndht = wndht
        self.rfcrp = rfcrp
        self.clmt = clmt
        self.loctn = loctn
        self.data = None

        # Setup the Open-Meteo API client with cache and retry on error
        self.cache_session = requests_cache.CachedSession(cache_dir, expire_after=expire_after)
        self.retry_session = retry(self.cache_session, retries=retries, backoff_factor=backoff_factor)
        self.openmeteo = openmeteo_requests.Client(session=self.retry_session)
        self.url_endpoint = "https://api.open-meteo.com/v1/forecast"
        

    def get_forecast(self, start_date=None, end_date=None, forecast_days=7):
        """Get the weather forecast for a location

        Parameters
        ----------
        start_date : str, optional
            Start date of the forecast (YYYY-MM-DD)
        end_date : str, optional
            End date of the forecast (YYYY-MM-DD)
        forecast_days : int, optional
            Number of days to forecast from the start date

        Returns
        -------
        forecast : pd.DataFrame
            Weather forecast data
        """
        if end_date is not None:
            assert start_date is not None, "start_date must be provided if end_date is provided"
            # in this case, ignore the forecast_days parameter
            forecast_days = None
            
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "elevation": self.z,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "vapour_pressure_deficit",
                "dew_point_2m",
                "wind_speed_10m",
                "precipitation_probability",
                "precipitation",
                ],
            "daily": [
                "shortwave_radiation_sum",
                "et0_fao_evapotranspiration",
                ],
            "start_date": start_date,
            "end_date": end_date,
            "forecast_days": forecast_days,
            "wind_speed_unit": "ms",
            "timezone": "auto"
        }

        # perform the request
        response = self.openmeteo.weather_api(self.url_endpoint, params=params)[0]
        if self.z is None:
            self.z = response.Elevation()   # if elevation is not provided, use the elevation from the response
        #timezone = response.TimezoneAbbreviation()
        #utc_offset = response.UtcOffsetSeconds()

        # Process hourly data
        hourly = response.Hourly()
        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        for v_idx,v in enumerate(params["hourly"]):
            hourly_data[v] = hourly.Variables(v_idx).ValuesAsNumpy()
        hourly_dataframe = pd.DataFrame(data=hourly_data).set_index("date")

        # Process daily data
        daily = response.Daily()
        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit="s", utc=True),
            end = pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}
        for v_idx,v in enumerate(params["daily"]):
            daily_data[v] = daily.Variables(v_idx).ValuesAsNumpy()
        daily_dataframe = pd.DataFrame(data=daily_data).set_index("date")

        # aggregate data
        daily_dataframe["Tmin"] = hourly_dataframe["temperature_2m"].resample("D").min()
        daily_dataframe["Tmax"] = hourly_dataframe["temperature_2m"].resample("D").max()
        daily_dataframe["Tmean"] = hourly_dataframe["temperature_2m"].resample("D").mean()
        daily_dataframe["RHmin"] = hourly_dataframe["relative_humidity_2m"].resample("D").min()
        daily_dataframe["RHmax"] = hourly_dataframe["relative_humidity_2m"].resample("D").max()
        daily_dataframe["RHmean"] = hourly_dataframe["relative_humidity_2m"].resample("D").mean()
        daily_dataframe["Vapr"] = hourly_dataframe["vapour_pressure_deficit"].resample("D").mean()
        daily_dataframe["Tdew"] = hourly_dataframe["dew_point_2m"].resample("D").mean()
        daily_dataframe["Wndsp"] = hourly_dataframe["wind_speed_10m"].resample("D").mean()  # NB: forecasted wind speed seems a bit overestimated...
        # adjust wind speed to the desired height
        if self.wndht != 10.0:
            daily_dataframe["Wndsp"] = daily_dataframe["Wndsp"] * (4.87/log(67.8*self.wndht-5.42))
        daily_dataframe["Srad"] = daily_dataframe.pop("shortwave_radiation_sum")
        # compute rain as sum of hourly values weighted by probability
        hourly_dataframe["precipitation_probability"] = hourly_dataframe["precipitation_probability"].fillna(100) / 100
        daily_dataframe["Rain"] = (hourly_dataframe["precipitation"] * hourly_dataframe["precipitation_probability"]).resample("D").sum()
        daily_dataframe["ETref"] = daily_dataframe.pop("et0_fao_evapotranspiration")
        daily_dataframe.index.name = "Date"

        # compute the reference evapotranspiration (through the Weather class)
        #daily_dataframe["ETref"] = Weather(data=daily_dataframe, z=self.z, lat=self.lat, wndht=self.wndht, rfcrp=self.rfcrp, clmt=self.clmt, loctn=self.loctn).data["ETref"]
        self.data = daily_dataframe

        return self.data

    def to_csv(self, path='pyfao56.frc'):
        """Save forecast weather data to a CSV file.

        Parameters
        ----------
        filepath : str, optional
            Path to forecast weather data file (default = 'pyfao56.frc')
        """

        with open(path, 'w') as f:
            f.write(f'#z: {self.z}\n')
            f.write(f'#lat: {self.lat}\n')
            f.write(f'#wndht: {self.wndht}\n')
            f.write(f'#rfcrp: {self.rfcrp}\n')
            f.write(f'#clmt: {self.clmt}\n')
            f.write(f'#loctn: {self.loctn}\n')
            self.data.to_csv(f)