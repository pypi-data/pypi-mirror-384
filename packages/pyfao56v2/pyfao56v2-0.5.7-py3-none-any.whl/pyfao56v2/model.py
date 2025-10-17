"""
########################################################################
The model.py module contains the Model class, which defines the
equations for daily soil water balance calculations based on the FAO-56
dual crop coefficient method for evapotranspiration (ET) estimation.

The FAO-56 method is described in the following documentation:
Allen, R. G., Pereira, L. S., Raes, D., Smith, M., 1998.  FAO Irrigation
and Drainage Paper No. 56. Crop Evapotranspiration: Guidelines for
Computing Crop Water Requirements. Food and Agriculture Organization of
the United Nations, Rome, Italy.

http://www.fao.org/3/x0490e/x0490e00.htm

Further details on the FAO56 methodology (as well as the runoff method)
can be found in the following documentation:
ASCE Task Committee on Revision of Manual 70, 2016. Evaporation,
Evapotranspiration, and Irrigation Water Requirements, 2nd edition. ASCE
Manuals and Reports on Engineering Practice No. 70. Jensen, M. E. and
Allen, R. G. (eds.). American Society of Civil Engineers, Reston,
Virginia.

The model.py module contains the following:
    Model - A class for managing FAO-56 soil water balance computations.

01/07/2016 Initial Python functions developed by Kelly Thorp
11/04/2021 Finalized updates for inclusion in the pyfao56 Python package
10/27/2022 Incorporated Fort Collins ARS stratified soil layers approach
11/30/2022 Incorporated Fort Collins ARS water balance approach
08/17/2023 Improved logic for case of missing rhmin data
10/31/2023 Added AquaCrop Ks option
11/01/2023 Added reports of the cumulative seasonal water balance
12/12/2023 Added the runoff functionality by Dinesh Gulati
02/15/2024 Added functionality for automatic irrigation scheduling
########################################################################
"""

import pandas as pd
import math

class Model:
    """A class for managing FAO-56 soil water balance computations.

    Manages computations based on FAO-56 methods for evapotranspiration
    and soil water balance calculations (Allen et al., 1998).

    Attributes
    ----------
    start : datetime
        Simulation start date in 'YYYY-MM-DD' format
    end : datetime
        Simulation end date in 'YYYY-MM-DD' format
    par : pyfao56 Parameters class
        Provides the parameter data for simulations
    wth : pyfao56 Weather class
        Provides the weather data for simulations
    irr : pyfao56 Irrigation class, optional
        Provides the irrigation data for simulations
        (default = None)
    sol : pyfao56 SoilProfile class, optional
        Provides data for modeling with stratified soil layers
        (default = None)
    autoirr : pyfao56 AutoIrrigate class, optional
        Provides data for automatic irrigation scheduling
        (default = None)
    upd : pyfao56 Update class, optional
        Provides data and methods for state variable updating
        (default = None)
    roff : boolean, optional
        If True, computes surface runoff following ASCE (2016)
        (default = False)
    cons_p : boolean, optional
        If False, p follows FAO-56; if True, p is constant (=pbase)
        (default = False)
    aq_Ks : boolean, optional
        If False, Ks follows FAO-56; if True, Ks via AquaCrop equation
        (default = False)
    ModelState : class
        Contains parameters and model states for a single timestep
    cnames : list
        Column names for odata
    odata : DataFrame
        Model output data as float
        index - Year and day of year as string ('yyyy-ddd')
        columns - ['Year','DOY','DOW','Date','ETref','Kcb','h',
                   'Kcmax','fc','fw','few','De','Kr','Ke','E','DPe',
                   'Kc','ETc','TAW','TAWrmax','TAWb','Zr','p','RAW',
                   'Ks','Kcadj','ETcadj','T','DP','Dinc','Dr','fDr',
                   'Drmax','fDrmax','Db','fDb','Irrig','IrrLoss','Rain',
                   'Runoff','Year','DOY','DOW','Date']
            Date    - YYYY-MM-DD
            ETref   - Daily reference evapotranspiration (mm)
            Kcb     - Basal crop coefficient, considering updates
            h       - Plant height (m)
            Kcmax   - Upper limit crop coefficient, FAO-56 Eq. 72
            fc      - Canopy cover fraction, FAO-56 Eq. 76
            fw      - Fraction soil surface wetted, FAO-56 Table 20
            few     - Exposed & wetted soil fraction, FAO-56 Eq. 75
            De      - Cumulative depth of evaporation, FAO-56 Eqs. 77&78
            Kr      - Evaporation reduction coefficient, FAO-56 Eq. 74
            Ke      - Evaporation coefficient, FAO-56 Eq. 71
            E       - Soil water evaporation (mm), FAO-56 Eq. 69
            DPe     - Percolation under exposed soil (mm), FAO-56 Eq. 79
            Kc      - Crop coefficient, FAO-56 Eq. 69
            ETc     - Non-stressed crop ET (mm), FAO-56 Eq. 69
            TAW     - Total available water (mm), FAO-56 Eq. 82
            TAWrmax - Total available water for max root depth (mm)
            TAWb    - Total available water in bottom layer (mm)
            Zr      - Root depth (m), FAO-56 page 279
            p       - Fraction depleted TAW, FAO-56 p162 and Table 22
            RAW     - Readily available water (mm), FAO-56 Equation 83
            Ks      - Transpiration reduction factor, FAO-56 Eq. 84
            Kcadj   - Adjusted crop coefficient, FA0-56 Eq. 80
            ETcadj  - Adjusted crop ET (mm), FAO-56 Eq. 80
            T       - Adjusted crop transpiration (mm)
            DP      - Deep percolation (mm), FAO-56 Eq. 88
            Dinc    - Depletion increment due to root growth (mm)
            Dr      - Soil water depletion (mm), FAO-56 Eqs. 85 & 86
            fDr     - Fractional root zone soil water depletion (mm/mm)
            Drmax   - Soil water depletion for max root depth (mm)
            fDrmax  - Fractional depletion for max root depth (mm/mm)
            Db      - Soil water depletion in the bottom layer (mm)
            fDb     - Fractional depletion in the bottom layer (mm/mm)
            Irrig   - Depth of applied irrigation (mm)
            IrrLoss - Depth of irrigation loss due to inefficiency (mm)
            Rain    - Depth of precipitation (mm)
            Runoff  - Surface runoff (mm)
            Theta   - Soil volumetric water content (m3/m3)
    swb_data : dict
        Container for cumulative seasonal water balance data
        keys - ['ETref','ETc','ETcadj','E','T','DP','Irrig','IrrLoss',
                'Rain','Runoff','Dr_ini','Dr_end','Drmax_ini',
                'Drmax_end']
        value - Cumulative water balance data in mm
    """

    def __init__(self, start, end, par, wth, irr=None, autoirr=None,
                 sol=None, upd=None, roff=False, cons_p=False,
                 aq_Ks=False):
        """Initialize the Model class attributes.

        Parameters
        ----------
        start : str
            Simulation start date ('YYYY-MM-DD')
        end : str
            Simulation end date ('YYYY-MM-DD')
        par : pyfao56 Parameters object
            Provides the parameter data for simulations
        wth : pyfao56 Weather object
            Provides the weather data for simulations
        irr : pyfao56 Irrigation object, optional
            Provides the irrigation data for simulations
            (default = None)
        sol : pyfao56 SoilProfile object, optional
            Provides data for modeling with stratified soil layers
            (default = None)
        autoirr : pyfao56 AutoIrrigate object, optional
            Provides data for automatic irrigation scheduling
            (default = None)
        upd : pyfao56 Update object, optional
            Provides data and methods for state variable updating
            (default = None)
        roff : boolean, optional
            If True, computes surface runoff following ASCE (2016)
            (default = False)
        cons_p : boolean, optional
            If False, p follows FAO-56; if True, p is constant (=pbase)
            (default = False)
        aq_Ks : boolean, optional
            If False, Ks follows FAO-56; if True, Ks via AquaCrop Eqn
            (default = False)
        """

        self.start = pd.to_datetime(start)
        self.end = pd.to_datetime(end)
        self.par = par
        self.wth = wth
        self.irr = irr
        self.autoirr = autoirr
        self.sol = sol
        self.upd = upd
        self.roff = roff
        self.cons_p = cons_p
        self.aq_Ks = aq_Ks
        self.cnames = [
            'ETref', 'Kcb', 'h', 'Kcmax', 'fc', 'fw', 'afw', 'few', 'De',
            'Kr', 'Ke', 'E', 'DPe', 'Kc', 'ETc', 'TAW', 'TAWrmax', 'TAWb',
            'Zr', 'p', 'RAW', 'Ks', 'Kcadj', 'ETcadj', 'T', 'DP', 'Dinc',
            'Dr', 'fDr', 'Drmax', 'fDrmax', 'Db', 'fDb', 'Irrig', 'IrrLoss',
            'AutoIrrig', 'AutoIrrLoss', 'Rain', 'Runoff', 'Theta'
            ]
        self.data = pd.DataFrame(columns=self.cnames)
        self.data.index.name = 'Date'

        # some checks on the weather data
        assert self.start <= self.end, 'Start date must be before end date'
        assert (wth_start := self.wth.data.index[0]) <= self.start, f'Weather data starts on {wth_start}, after simulation start date {self.start}'
        assert (wth_end := self.wth.data.index[-1]) >= self.end, f'Weather data ends on {wth_end}, before simulation end date {self.end}'
        assert pd.date_range(self.start, self.end).isin(self.wth.data.index).all(), f'Weather data has gaps between start date ({self.start}) and end date ({self.end})'

    def to_csv(self, path='pyfao56.out'):
        """Save the model output data to a csv file.

        Parameters
        ----------
        path : str
            Any valid filepath string
        """
            
        self.data.to_csv(path)

    def sums_to_csv(self, path='pyfao56.sum'):
        """Save a summary file with cumulative water balance values to a csv file.

        Parameters
        ----------
        path : str
            Any valid filepath string
        """

        pd.Series(self.swb_data).to_csv(path, header=False)



    class ModelState:
        """Contain parameters and states for a single timestep."""
        pass

    def run(self):
        """Initialize model, conduct simulation, update self.data"""

        # Initialize model state
        io = self.ModelState()

        # Retrieve and interpolate Kcb, h, Zr, fc time series between start and end of simulation
        date_range = pd.date_range(self.start, self.end, freq='D')
        io.Kcb_ts = pd.Series([self.par.get_Kcb(date) for date in date_range], index=date_range)
        io.h_ts = pd.Series([self.par.get_h(date) for date in date_range], index=date_range)
        io.Zr_ts = pd.Series([self.par.get_Zr(date) for date in date_range], index=date_range)
        if self.par.fc_ts is not None:
            io.fc_ts = pd.Series([self.par.get_fc(date) for date in date_range], index=date_range)
        else:
            io.fc_ts = None

        if self.sol is None:
            io.solmthd = 'D' #Default homogeneous soil from Parameters
            #Total evaporable water (TEW, mm) - FAO-56 Eq. 73
            io.TEW = 1000. * (self.par.thetaFC - 0.50 * self.par.thetaWP) * self.par.Ze
            #Initial depth of evaporation (De, mm) - FAO-56 page 153
            io.De = 1000. * (self.par.thetaFC - 0.50 * self.par.thetaWP) * self.par.Ze
            #Initial root zone depletion (Dr, mm) - FAO-56 Eq. 87
            io.Dr = 1000. * (self.par.thetaFC - self.par.theta0) * io.Zr_ts.loc[self.start]
            #Initial soil depletion for max root depth (Drmax, mm)
            io.Drmax = 1000. * (self.par.thetaFC - self.par.theta0) * io.Zr_ts.max()
            #Initial root zone total available water (TAW, mm)
            io.TAW = 1000. * (self.par.thetaFC - self.par.thetaWP) * io.Zr_ts.loc[self.start]
            #By default, FAO-56 doesn't consider the following variables
            io.TAWrmax = -99.999
            io.Db = -99.999
            io.TAWb = -99.999
        else:
            io.solmthd = 'L' #Layered soil profile from SoilProfile
            io.lyr_dpths = list(self.sol.data.index)
            io.lyr_thFC  = list(self.sol.data['thetaFC'])
            io.lyr_thWP  = list(self.sol.data['thetaWP'])
            io.lyr_th0   = list(self.sol.data['theta0'])
            io.TEW = 0.
            io.De = 0.
            io.Dr = 0.
            io.Drmax = 0.
            io.TAW = 0.
            io.TAWrmax = 0.
            #Iterate down the soil profile in 1 mm increments
            for dpthmm in list(range(1, (io.lyr_dpths[-1] * 10 + 1))):
                #Find soil layer index that contains dpthmm
                lyr_idx = [idx for (idx, dpth) in
                          enumerate(io.lyr_dpths) if dpthmm<=dpth*10][0]
                #Total evaporable water (TEW, mm) - FAO-56 Eq. 73
                if dpthmm <= self.par.Ze * 1000.: #mm
                    diff=io.lyr_thFC[lyr_idx]-0.50*io.lyr_thWP[lyr_idx]
                    io.TEW += diff #mm
                #Initial depth of evaporation (De, mm) - FAO-56 page 153
                if dpthmm <= self.par.Ze * 1000.: #mm
                    diff=io.lyr_thFC[lyr_idx]-0.50*io.lyr_thWP[lyr_idx]
                    io.De += diff #mm
                #Initial root zone depletion (Dr, mm)
                if dpthmm <= io.Zr_ts.loc[self.start] * 1000.: #mm
                    diff = (io.lyr_thFC[lyr_idx] - io.lyr_th0[lyr_idx])
                    io.Dr += diff #mm
                #Initial depletion for max root depth (Drmax, mm)
                if dpthmm <= io.Zr_ts.max() * 1000.: #mm
                    diff = (io.lyr_thFC[lyr_idx] - io.lyr_th0[lyr_idx])
                    io.Drmax += diff #mm
                #Initial root zone total available water (TAW, mm)
                if dpthmm <= io.Zr_ts.loc[self.start] * 1000.: #mm
                    diff = (io.lyr_thFC[lyr_idx] - io.lyr_thWP[lyr_idx])
                    io.TAW += diff #mm
                #Total available water for max root depth (TAWrmax, mm)
                if dpthmm <= io.Zr_ts.max() * 1000.: #mm
                    diff = (io.lyr_thFC[lyr_idx] - io.lyr_thWP[lyr_idx])
                    io.TAWrmax += diff #mm
            #Initial depletion in the bottom layer (Db, mm)
            io.Db = io.Drmax - io.Dr
            #Initial total available water in bottom layer (TAWb, mm)
            io.TAWb = io.TAWrmax - io.TAW
        #Initial root zone soil water depletion fraction (fDr, mm/mm)
        io.fDr = 1.0 - ((io.TAW - io.Dr) / io.TAW)
        io.Ks = 1.0
        io.h = io.h_ts.loc[self.start]
        io.Zr = io.Zr_ts.loc[self.start]
        io.roff   = self.roff
        io.cons_p = self.cons_p
        io.aq_Ks  = self.aq_Ks

        # Set start date and timestep
        io.tcurr = self.start
        io.tdelta = pd.Timedelta(days=1)

        # Loop through each day of the simulation
        while io.tcurr <= self.end:
            assert io.tcurr in self.wth.data.index, f'Weather data missing for date {io.tcurr}'

            # Update ModelState object for current date

            ##### Get wndht and rfcrp
            io.wndht = self.wth.data.loc[io.tcurr].get('wndht', 2.0)
            io.rfcrp = self.wth.data.loc[io.tcurr].get('rfcrp', 'S')

            ##### Get ETref
            io.ETref = self.wth.data.loc[io.tcurr,'ETref']
            if math.isnan(io.ETref):
                io.ETref = self.wth.compute_etref(io.tcurr)
            io.rain = self.wth.data.loc[io.tcurr,'Rain']
            io.wndsp = self.wth.data.loc[io.tcurr,'Wndsp']
            if math.isnan(io.wndsp):
                io.wndsp = 2.0
            io.rhmin = self.wth.data.loc[io.tcurr,'RHmin']
            if math.isnan(io.rhmin):
                tmax = self.wth.data.loc[io.tcurr,'Tmax']
                tmin = self.wth.data.loc[io.tcurr,'Tmin']
                tdew = self.wth.data.loc[io.tcurr,'Tdew']
                if math.isnan(tdew):
                    tdew = tmin
                #ASCE (2005) Eqs. 7 and 8
                emax = 0.6108*math.exp((17.27*tmax)/(tmax+237.3))
                ea   = 0.6108*math.exp((17.27*tdew)/(tdew+237.3))
                io.rhmin = ea/emax*100.
            if math.isnan(io.rhmin):
                io.rhmin = 45.

            
            
            ##### Get irrigation data
            io.idep = 0.0
            io.fw = 1.0
            io.ieff = 100.0
            if self.irr is not None:
                if io.tcurr in self.irr.data.index:
                    io.idep = self.irr.data.loc[io.tcurr,'Depth']
                    io.idep, io.fw, io.ieff = self.irr.get_irrig(io.tcurr).values()

            
            
            ##### Evaluate autoirrigation conditions and compute amounts
            io.aidep = 0.0
            io.ailoss = 0.0
            io.afw = 0.0
            if self.autoirr is not None:
                for i in range(len(self.autoirr.data)):

                    # Evaluate date range condition
                    aistart = self.autoirr.data.loc[i,'start']
                    aiend  = self.autoirr.data.loc[i,'end']
                    if io.tcurr<aistart or io.tcurr>aiend:
                        continue

                    # Evaluate "after last recorded irrigation" condition
                    if self.autoirr.data.loc[i,'alre'] and self.irr is not None and not self.irr.data.empty:
                        lastirr = self.irr.data[self.irr.data['Depth']!=0].index[-1]
                        if io.tcurr <= lastirr:
                            continue
                    
                    # Evaluate day of the week condition
                    dow = pd.to_datetime(io.tcurr).day_of_week
                    if str(dow) not in self.autoirr.data.loc[i,'idow']:
                        continue

                    # Evaluate forecasted precipitation condition
                    fpdep = self.autoirr.data.loc[i,'fpdep']
                    fpday = self.autoirr.data.loc[i,'fpday']
                    fpact = self.autoirr.data.loc[i,'fpact']
                    fcrain = 0. # cumulative forecasted rain depth
                    for j in range(fpday):
                        fpdate = io.tcurr + j*io.tdelta
                        assert fpdate in self.wth.data.index, f'Weather data missing for forecasted date {fpdate}'
                        fcrain += self.wth.data.loc[fpdate,'Rain']
                    reduce_airr = 0.
                    if fcrain >= fpdep:
                        if fpact == 'cancel':
                            continue
                        elif fpact == 'reduce':
                            reduce_airr = fcrain
                    
                    # Evaluate fractional management allowed depletion (mm/mm)
                    if io.fDr <= self.autoirr.data.loc[i,'mad']:
                        continue

                    # Evaluate management allowed depletion (mm)
                    if io.Dr <= self.autoirr.data.loc[i,'madDr']:
                        continue

                    # Evaluate critical Ks
                    if io.Ks >= self.autoirr.data.loc[i,'ksc']:
                        continue

                    # Evaluate days since last irrigation
                    idays = self.data[self.data['Irrig']>0.].index
                    if len(idays) > 0:
                        dsli = (io.tcurr-max(idays)).days
                    else:
                        dsli = ((io.tcurr-self.start).days)+1
                    if dsli < self.autoirr.data.loc[i,'dsli']:
                        continue

                    # Evaluate days since last watering event
                    evnt = self.autoirr.data.loc[i,'evnt']
                    edays = self.data[(self.data['Irrig']+self.data['AutoIrrig']-self.data['IrrLoss']-self.data['AutoIrrLoss']+self.data['Rain']-self.data['Runoff'])>=evnt].index
                    if len(edays) > 0:
                        dsle = (io.tcurr-max(edays)).days
                    else:
                        dsle = ((io.tcurr-self.start).days)+1
                    if dsle < self.autoirr.data.loc[i,'dsle']:
                        continue

                    # All conditions were met: need to autoirrigate
                    # Default autoirrigation depth is current root-zone soil water depletion (Dr)
                    io.aidep = max([0.0, io.Dr - reduce_airr])

                    # Alternatively, the default rate may be modified:

                    # Use a contant rate
                    icon = self.autoirr.data.loc[i,'icon']
                    if icon is not None:
                        io.aidep = max([0.0, icon - reduce_airr])

                    # Target a specific root-zone soil water depletion
                    itdr = self.autoirr.data.loc[i,'itdr']
                    if itdr is not None:
                        io.aidep = max([0.0, io.Dr - reduce_airr - itdr])

                    # Target a fractional root-zone soil water depletion
                    itfdr = self.autoirr.data.loc[i,'itfdr']
                    if itfdr is not None:
                        #itdr2 = io.TAW-io.TAW*(1.0-itfdr)
                        itdr = io.TAW*itfdr
                        io.aidep = max([0.0, io.Dr - reduce_airr - itdr])

                    # Use ETcadj minus precip for past X number of days
                    ettyp = self.autoirr.data.loc[i,'ettyp']
                    ietrd = self.autoirr.data.loc[i,'ietrd']
                    if ietrd is not None:
                        dsss = (io.tcurr-self.start).days
                        recent = self.data.tail(min([dsss, ietrd]))
                        p1 = recent['Rain'].sum()
                        p2 = recent['Runoff'].sum()
                        et = recent[ettyp].sum()
                        etrd = et - (p1 - p2)
                        io.aidep = max([0.0, etrd - reduce_airr])

                    # Use ETcadj minus precip since last irrigation
                    ettyp = self.autoirr.data.loc[i,'ettyp']
                    ietri = self.autoirr.data.loc[i,'ietri']
                    if ietri:
                        dsss = (io.tcurr-self.start).days
                        recent = self.data.tail(min([dsss,dsli]))
                        p1 = recent['Rain'].sum()
                        p2 = recent['Runoff'].sum()
                        et = recent[ettyp].sum()
                        etri=(et-p1+p2)
                        io.aidep = max([0.0, etri - reduce_airr])

                    #Use ETcadj minus precip since last watering event
                    ettyp = self.autoirr.data.loc[i,'ettyp']
                    ietre = self.autoirr.data.loc[i,'ietre']
                    if ietre:
                        dsss = (io.tcurr-self.start).days
                        recent = self.data.tail(min([dsss,dsle]))
                        p1 = recent['Rain'].sum()
                        p2 = recent['Runoff'].sum()
                        et = recent[ettyp].sum()
                        etre=(et-p1+p2)
                        io.aidep = max([0.0, etre - reduce_airr])

                    # Furthermore, adjustments to the autoirrigation depth can be made

                    # Adjust autoirrigation depth by a fixed percentage
                    aiper = self.autoirr.data.loc[i,'iper']
                    if aiper is not None:
                        io.aidep = io.aidep * (aiper / 100.)

                    # Adjust rate for minimum irrigation amount
                    aimin = self.autoirr.data.loc[i,'imin']
                    if aimin is not None:
                        io.aidep = max([aimin, io.aidep])

                    # Adjust rate for maximum irrigation amount
                    aimax = self.autoirr.data.loc[i,'imax']
                    if aimax is not None:
                        io.aidep = min([aimax, io.aidep])

                    # Finally, adjust rate for (auto)irrigation inefficiency
                    io.aieff = self.autoirr.data.loc[i,'ieff'] or io.ieff
                    io.ailoss = io.aidep - io.aidep * (io.aieff / 100.)

                    # Set fraction of soil wetted (fw) for autoirrigation
                    io.afw = self.autoirr.data.loc[i,'fw']



            ##### Obtain updates for Kcb, h, and fc, if available (TODO)
            io.updKcb = float('NaN')
            io.updh = float('NaN')
            io.updfc = float('NaN')
            if self.upd is not None:
                io.updKcb = self.upd.getdata(io.tcurr,'Kcb')
                io.updh = self.upd.getdata(io.tcurr,'h')
                io.updfc = self.upd.getdata(io.tcurr,'fc')



            ##### Simulate the daily soil water balance
            self._advance(io)



            ##### Append results to self.data
            data = [
                io.ETref, io.Kcb, io.h, io.Kcmax, io.fc, io.fw, io.afw, io.few, io.De,
                io.Kr, io.Ke, io.E, io.DPe, io.Kc, io.ETc, io.TAW, io.TAWrmax,
                io.TAWb, io.Zr, io.p, io.RAW, io.Ks, io.Kcadj, io.ETcadj, io.T,
                io.DP, io.Dinc, io.Dr, io.fDr, io.Drmax, io.fDrmax, io.Db, io.fDb,
                io.idep, io.irrloss, io.aidep, io.ailoss, io.rain, io.runoff,
                io.theta
                ]
            self.data.loc[io.tcurr] = data



            ##### Advance to next timestep
            io.tcurr = io.tcurr + io.tdelta

        ##### Save seasonal water balance data to self.swb_data dictionary
        self.swb_data = {
            'ETref'     : sum(self.data['ETref']),
            'ETc'       : sum(self.data['ETc']),
            'ETcadj'    : sum(self.data['ETcadj']),
            'E'         : sum(self.data['E']),
            'T'         : sum(self.data['T']),
            'DP'        : sum(self.data['DP']),
            'Irrig'     : sum(self.data['Irrig']),
            'IrrLoss'   : sum(self.data['IrrLoss']),
            'AutoIrrig' : sum(self.data['AutoIrrig']),
            'AutoIrrLoss': sum(self.data['AutoIrrLoss']),
            'Rain'      : sum(self.data['Rain']),
            'Runoff'    : sum(self.data['Runoff']),
            'Dr_ini'    : self.data.loc[self.start,'Dr'],
            'Dr_end'    : self.data.loc[self.end,'Dr'],
            'Drmax_ini' : self.data.loc[self.start,'Drmax'],
            'Drmax_end' : self.data.loc[self.end,'Drmax'],
            }



    def _advance(self, io):
        """Advance the model by one daily timestep.

        Parameters
        ----------
        io : ModelState object
        """

        # Basal crop coefficient (Kcb) (FAO-56 Tables 11 and 17)
        io.Kcb = io.Kcb_ts.loc[io.tcurr]
        # Overwrite Kcb if updates are available (TODO)
        if io.updKcb > 0: io.Kcb = io.updKcb

        # Plant height (h, m)
        io.h = io.h_ts.loc[io.tcurr]
        # Overwrite h if updates are available (TODO)
        if io.updh > 0: io.h = io.updh

        # Root depth (Zr, m) (FAO-56 page 279)
        io.Zr = io.Zr_ts.loc[io.tcurr]

        # Upper limit crop coefficient (Kcmax) (FAO-56 Eq. 72)
        u2 = io.wndsp * (4.87/math.log(67.8*io.wndht-5.42))
        u2 = sorted([1.0, u2, 6.0])[1]
        rhmin = sorted([20.0, io.rhmin, 80.])[1]
        if io.rfcrp == 'S':
            io.Kcmax = max([1.2+(0.04*(u2-2.0)-0.004*(rhmin-45.0))*(io.h/3.0)**.3, io.Kcb+0.05])
        elif io.rfcrp == 'T':
            io.Kcmax = max([1.0, io.Kcb + 0.05])

        # Canopy cover fraction (fc, 0.0-0.99) (FAO-56 Eq. 76)
        if self.par.Kcbini is not None:
            io.fc = sorted([0.0, ((io.Kcb-self.par.Kcbini)/(io.Kcmax-self.par.Kcbini))**(1.0+0.5*io.h), 0.99])[1]
            # TODO fc starts at 0.0 (i.e. when Kcb = Kcbini) and increases to 0.99.
            # But what if the simulation starts from a later date than planting?
        else:
            io.fc = io.fc_ts.loc[io.tcurr]

        # Overwrite fc if updates are available (TODO)
        if io.updfc > 0: io.fc = io.updfc

        # Losses due to irrigation inefficiency (irrloss, mm)
        io.irrloss = io.idep - io.idep * (io.ieff / 100.)
        # Effective irrigation (manual+auto) (mm)
        effirr = (io.idep - io.irrloss) + (io.aidep - io.ailoss)

        # Surface runoff (runoff, mm)
        io.runoff = 0.0
        if io.roff is True:
            # Method per ASCE (2016) Eqs. 14-12 to 14-20, page 451-454
            CN1 = self.par.CN2/(2.281-0.01281*self.par.CN2) #ASCE (2016) Eq. 14-14
            CN3 = self.par.CN2/(0.427+0.00573*self.par.CN2) #ASCE (2016) Eq. 14-15
            if io.De <= 0.5*self.par.REW:
                CN = CN3 #ASCE (2016) Eq. 14-18
            elif io.De >= 0.7*self.par.REW+0.3*io.TEW:
                CN = CN1 #ASCE (2016) Eq. 14-19
            else:
                CN = (io.De-0.5*self.par.REW)*CN1
                CN = CN+(0.7*self.par.REW+0.3*io.TEW-io.De)*CN3
                CN = CN/(0.2*self.par.REW+0.3*io.TEW) #ASCE (2016) Eq. 14-20
            storage = 250.*((100./CN)-1.) #ASCE (2016) Eq. 14-12
            if io.rain > 0.2*storage:
                #ASCE (2016) Eq. 14-13
                io.runoff = (io.rain-0.2*storage)**2
                io.runoff = io.runoff/(io.rain+0.8*storage)
                io.runoff = min([io.runoff,io.rain])
            else:
                io.runoff = 0.0
        # Effective precipitation (mm)
        effrain = io.rain - io.runoff

        # Fraction soil surface wetted (fw) - FAO-56 Table 20, page 149
        if io.rain >= 3.0:
            io.fw = 1.0 # when it rains, the soil gets uniformly wet
        elif io.idep > 0.0 and io.aidep == 0:
            pass #fw=fw input
        elif io.idep == 0.0 and io.aidep > 0:
            io.fw = io.afw
        elif io.idep > 0.0 and io.aidep > 0:
            io.fw = max([io.fw, io.afw])
        else:   # io.idep == 0 and io.aidep == 0
            pass #fw = fw of the previous day

        # Exposed & wetted soil fraction (few, 0.01-1.0) - FAO-56 Eq. 75
        io.few = sorted([0.01, min([1.0-io.fc, io.fw]), 1.0])[1]

        # Evaporation reduction coefficient (Kr, 0-1) - FAO-56 Eq. 74
        io.Kr = sorted([0.0, (io.TEW-io.De)/(io.TEW-self.par.REW), 1.0])[1]

        # Evaporation coefficient (Ke) - FAO-56 Eq. 71
        io.Ke = min([io.Kr*(io.Kcmax-io.Kcb), io.few*io.Kcmax])

        # Soil water evaporation (E, mm) - FAO-56 Eq. 69
        io.E = io.Ke * io.ETref

        # Deep percolation under exposed soil (DPe, mm) - FAO-56 Eq. 79
        io.DPe = max([effrain + effirr/io.fw - io.De, 0.0])

        # Cumulative depth of evaporation (De, mm) - FAO-56 Eqs. 77 & 78
        De = io.De - effrain - effirr/io.fw + io.E/io.few + io.DPe
        io.De = sorted([0.0, De, io.TEW])[1]

        # Crop coefficient (Kc) - FAO-56 Eq. 69
        io.Kc = io.Ke + io.Kcb

        # Non-stressed crop evapotranspiration (ETc, mm) - FAO-56 Eq. 69
        io.ETc = io.Kc * io.ETref

        if io.solmthd == 'D':
            # Total available water (TAW, mm) - FAO-56 Eq. 82
            io.TAW = 1000.0 * (self.par.thetaFC - self.par.thetaWP) * io.Zr
        elif io.solmthd == 'L':
            io.TAW = 0.
            # Iterate down the soil profile in 1 mm increments
            for dpthmm in list(range(1, (io.lyr_dpths[-1] * 10 + 1))):
                # Find soil layer index that contains dpthmm
                lyr_idx = [idx for (idx, dpth) in enumerate(io.lyr_dpths) if dpthmm<=dpth*10][0]
                # Total available water (TAW, mm)
                if dpthmm <= io.Zr * 1000.: #mm
                    diff = (io.lyr_thFC[lyr_idx] - io.lyr_thWP[lyr_idx])
                    io.TAW += diff #mm
            # Total available water in the bottom layer (TAWb, mm)
            io.TAWb_prev = io.TAWb
            io.TAWb = io.TAWrmax - io.TAW

        # Fraction depleted TAW (p, 0.1-0.8) - FAO-56 p162 and Table 22
        if io.cons_p is True:
            io.p = self.par.pbase
        else:
            io.p = sorted([0.1,self.par.pbase+0.04*(5.0-io.ETc),0.8])[1]

        # Readily available water (RAW, mm) - FAO-56 Equation 83
        io.RAW = io.p * io.TAW

        # Transpiration reduction factor (Ks, 0.0-1.0)
        if io.aq_Ks is True:
            # Ks method from AquaCrop
            rSWD = io.Dr/io.TAW
            Drel = (rSWD-io.p)/(1.0-io.p)
            sf = 1.5
            aqKs = 1.0-(math.exp(sf*Drel)-1.0)/(math.exp(sf)-1.0)
            io.Ks = sorted([0.0, aqKs, 1.0])[1]
        else:
            #FAO-56 Eq. 84
            io.Ks = sorted([0.0, (io.TAW-io.Dr)/(io.TAW-io.RAW), 1.0])[1]

        # Adjusted crop coefficient (Kcadj) - FAO-56 Eq. 80
        io.Kcadj = io.Ks * io.Kcb + io.Ke

        # Adjusted crop evapotranspiration (ETcadj, mm) - FAO-56 Eq. 80
        io.ETcadj = io.Kcadj * io.ETref

        # Adjusted crop transpiration (T, mm)
        io.T = (io.Ks * io.Kcb) * io.ETref

        # Water balance methods
        if io.solmthd == 'D':
            # Deep percolation (DP, mm) - FAO-56 Eq. 88
            # Boundary layer is considered at the root zone depth (Zr)
            DP = effrain + effirr - io.ETcadj - io.Dr
            io.DP = max([DP,0.0])

            # Root zone soil water depletion (Dr,mm) - FAO-56 Eqs.85 & 86
            Dr = io.Dr - effrain - effirr + io.ETcadj + io.DP
            io.Dr = sorted([0.0, Dr, io.TAW])[1]

            # Root zone soil water depletion fraction (fDr, mm/mm)
            io.fDr = 1.0 - ((io.TAW - io.Dr) / io.TAW)

            # Soil volumetric water content (Theta, m3/m3)
            io.theta = self.par.thetaFC - (io.Dr/(1000.0*io.Zr))

            # By default, FAO-56 doesn't consider the following variables
            io.Dinc = -99.999
            io.Drmax = -99.999
            io.fDrmax = -99.999
            io.Db = -99.999
            io.fDb = -99.999

        elif io.solmthd == 'L':
            # Deep percolation (DP, mm)
            # Boundary layer is at the max root depth (Zrmax)
            DP = effrain + effirr - io.ETcadj - io.Drmax
            io.DP = max([DP, 0.0])

            # Depletion increment due to root growth (Dinc, mm)
            # Computed from Db based on the incremental change in TAWb
            if io.TAWb_prev > 0.0:
                io.Dinc = io.Db * (1.0 - (io.TAWb / io.TAWb_prev))
            else: #handle zero divide issue
                io.Dinc = 0.0

            # Root zone soil water depletion (Dr, mm)
            Dr = io.Dr - effrain - effirr + io.ETcadj + io.Dinc
            io.Dr = sorted([0.0, Dr, io.TAW])[1]

            # Root zone soil water depletion fraction (fDr, mm/mm)
            io.fDr = 1.0 - ((io.TAW - io.Dr) / io.TAW)

            # Soil water depletion at max root depth (Drmax, mm)
            Drmax = io.Drmax - effrain - effirr + io.ETcadj + io.DP
            io.Drmax = sorted([0.0, Drmax, io.TAWrmax])[1]

            # Soil water depletion fraction at Zrmax (fDrmax, mm/mm)
            io.fDrmax = 1.0 - ((io.TAWrmax - io.Drmax) / io.TAWrmax)

            # Soil water depletion in the bottom layer (Db, mm)
            Db = io.Drmax - io.Dr
            io.Db = sorted([0.0, Db, io.TAWb])[1]

            # Bottom layer soil water depletion fraction (fDb, mm/mm)
            if io.TAWb > 0.0:
                io.fDb = 1.0 - ((io.TAWb - io.Db) / io.TAWb)
            else:
                io.fDb = 0.0
