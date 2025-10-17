"""
########################################################################
The irrigation.py module contains the Irrigation class, which provides
I/O tools for defining the irrigation management schedule, as required
for FAO-56 calculations.
########################################################################
"""

import pandas as pd

class Irrigation:
    """A class for managing irrigation data for FAO-56 calculations

    Attributes
    ----------
    data : DataFrame
        Irrigation data
        * index - Dates ('YYYY-MM-DD')
        * columns - ['Depth','fw','ieff']
        * * Depth - Irrigation depth (mm)
        * * fw - fraction of soil surface wetted (FAO-56 Table 20)
        * * ieff - Irrigation application efficiency (%)
    """

    COLS = ['Depth','fw','ieff']

    def __init__(self, data=None, **kwargs):
        """Initialize the Irrigation class attributes.

        Parameters
        ----------
        data : DataFrame
            Irrigation events
            index - Dates ('YYYY-MM-DD')
            columns - ['Depth','fw','ieff']
                Depth - Irrigation depth (mm)
                fw - fraction of soil surface wetted (FAO-56 Table 20)
                ieff - Irrigation application efficiency (%) (FAO-24 Section 3.3.1)
        """

        self.data = pd.DataFrame(columns=self.COLS)

        if data is not None:
            assert set(data.columns) == set(self.COLS), f'Columns should be {self.COLS}. Got {data.columns}'
            self.data = data[self.COLS] # change order of columns if necessary
            self.data.index = pd.to_datetime(self.data.index, format='%Y-%m-%d')

        # drop rows in which Depth is nan or 0
        self.data = self.data.dropna(subset=["Depth"])
        self.data = self.data[self.data['Depth'] > 0]

    def to_csv(self, path='pyfao56.irr'):
        """Save irrigation data to csv file

        Parameters
        ----------
        path : str
            Filepath for saving the irrigation data
        """

        self.data.to_csv(path)
        return

    @classmethod
    def from_csv(cls, path):
        """Load irrigation data from csv file

        Parameters
        ----------
        path : str
            Filepath for loading the irrigation data

        Returns
        -------
        Irrigation
            Irrigation class object
        """

        data = pd.read_csv(path, index_col=0)
        return cls(data)

    @classmethod
    def from_events(cls, events, **kwargs):
        """Create an Irrigation object from a list of irrigation events

        Parameters
        ----------
        events : list
            List of dictionaries containing irrigation events, e.g.:
            [{'Date': '2020-01-01', 'Depth': 8.0, 'fw': 1.0, 'ieff': 90}, ...]

        Returns
        -------
        Irrigation
            Irrigation class object
        """

        data = pd.DataFrame(events).set_index('Date')
        return cls(data)
    
    def get_irrig(self, date):
        """Get irrigation data for a specific date

        Parameters
        ----------
        date : str
            Date ('YYYY-MM-DD')

        Returns
        -------
        dict
            Irrigation data for the specified date
        """

        if date in self.data.index:
            return self.data.loc[date].to_dict()
        else:
            return {"Depth": 0, "fw": 0, "ieff": 100}