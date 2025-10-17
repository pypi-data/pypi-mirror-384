"""
########################################################################
The pyfao56v2 Python package builds on top of the pyfao56 library mantained by USDA-ARS.

- pyfao56 facilitates FAO-56 computations of daily soil
water balance using the dual crop coefficient method to estimate crop
evapotranspiration (ET).
The FAO-56 method is described in the following documentation:
Allen, R. G., Pereira, L. S., Raes, D., Smith, M., 1998.  FAO Irrigation
and Drainage Paper No. 56. Crop Evapotranspiration: Guidelines for
Computing Crop Water Requirements. Food and Agriculture Organization of
the United Nations, Rome Italy.
http://www.fao.org/3/x0490e/x0490e00.htm
Reference ET is computed using the ASCE Standardized Reference ET
Equation, which is described in the following documentation:
ASCE Task Committee on Standardization of Reference Evapotranspiration
(Walter, I. A., Allen, R. G., Elliott, R., Itenfisu, D., Brown, P.,
Jensen, M. E.,Mecham, B., Howell, T. A., Snyder, R., Eching, S.,
Spofford, T., Hattendorf, M., Martin, D., Cuenca, R. H., Wright, J. L.)
, 2005. The ASCE Standardized Reference Evapotranspiration Equation.
American Society of Civil Engineers, Reston, VA.
https://ascelibrary.org/doi/book/10.1061/9780784408056

- pyfao56v2 extends the pyfao56 library by:
    - working with "full" dates (YYYY-MM-DD) instead of day-of-year dates
      (YYYY-DOY)
    - allowing the input of custom Kcb time series, letting go of the
      trapezoidal Kcb curve in the original FAO-56 method
    - introducing lookup tables for crop, soil, and irrigation parameters
    - other improvements yet to be documented...
########################################################################
"""

# pyfao56v2/
from .main import simulate, WaterBalance
from .model import Model
from .parameters import Parameters
from .weather import Weather
from .irrigation import Irrigation
from .autoirrigate import AutoIrrigate
from .forecast import Forecast
#from .soil_profile import SoilProfile
#from .update import Update

# pyfao56v2/tools/
from .tools import Visualization
