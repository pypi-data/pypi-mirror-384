import pandas as pd
import numpy as np


PHENO_SUPPORTED_CROPS = ['maize']


def get_phenology(crop, T_mean, seeding_date, **kwargs):
    assert crop in PHENO_SUPPORTED_CROPS, f'Crop {crop} not supported. Supported crops are: {PHENO_SUPPORTED_CROPS}'
    assert isinstance(T_mean, (pd.Series)) and isinstance(T_mean.index, pd.DatetimeIndex), \
        f'T_mean must be a pandas Series indexed by date. \
        Got {type(T_mean)}{f" with index {type(T_mean.index)}" if isinstance(T_mean, pd.Series) else ""}'
    seeding_date = pd.to_datetime(seeding_date)
    assert T_mean.index[-1] >= seeding_date, f'T_mean must have dates after seeding_date. Got {T_mean.index[-1]} < {seeding_date}'
    
    # consider only dates after seeding_date
    T_mean = T_mean.loc[seeding_date:]
    if isinstance(T_mean, pd.Series):
        T_mean = T_mean.to_list()
    else:
        T_mean = T_mean['Tmean'].to_list()

    if crop == 'maize':
        return _maize(
            T_mean,
            kwargs.get('fao_class') or 'FAO 500',
            kwargs.get('T_base') or 10
        )
    else:
        raise ValueError(f'Crop {crop} not supported')
    


def _maize(T_mean, fao_class='FAO 500', T_base=10):

    TOTAL_GDD = {
        'FAO 200': 1150,
        'FAO 300': 1250,
        'FAO 400': 1300,
        'FAO 500': 1350,
        'FAO 600': 1450,
        'FAO 700': 1550
    }
    total_gdd = TOTAL_GDD[fao_class]

    # compute needed GDDs for starting each phenological stage
    gdd4stage = {
        'VE': int(0.03 * total_gdd),        # Emergence
        'V2': int(0.07 * total_gdd),        # 2 leaves
        'V3': int(0.13 * total_gdd),        # 3 leaves
        'V6': int(0.17 * total_gdd),        # 6 leaves
        'V9': int(0.22 * total_gdd),        # 9 leaves
        'VT': int(0.45 * total_gdd),        # Tasseling
        'R1': int(100 + 0.445 * total_gdd), # Silking
        'R4': int(0.7 * total_gdd),         # Dough
        'R6': total_gdd                     # Physiological maturity
    }

    # compute needed GDDs for starting ini, dev, mid, end stages (as required by FAO56)
    gdd4L = {
        'ini': gdd4stage['VE'],
        'dev': gdd4stage['VT'],
        'mid': gdd4stage['R4'],
        'end': gdd4stage['R6']
    }
    
    # compute cumulated GDD
    gdd = np.array([max(0, t-T_base) for t in T_mean])
    cum_gdd = np.cumsum(gdd)

    # compute duration of each stage
    Lini = np.argmax(cum_gdd >= gdd4L['ini'])
    Ldev = np.argmax(cum_gdd >= gdd4L['dev']) - Lini
    Lmid = np.argmax(cum_gdd >= gdd4L['mid']) - Lini - Ldev
    Lend = np.argmax(cum_gdd >= gdd4L['end']) - Lini - Ldev - Lmid

    assert cum_gdd[-1] >= total_gdd, f"\nNot enough GDDs for the crop to reach maturity!\nNeed {total_gdd} but got {cum_gdd[-1]:.2f}.\nLengths computed: Lini={Lini if Lini>0 else None}, Ldev={Ldev if Ldev>0 else None}, Lmid={Lmid if Lmid>0 else None}, Lend={Lend if Lend>0 else None}.\nAdd more weather data. Resorting to user-given or FAO56 default values..."

    return Lini, Ldev, Lmid, Lend



def _potato(todo):
    # https://www.researchgate.net/publication/222033953_Simulating_the_development_of_field_grown_potato_Solanum_tuberosum_L
    pass

def _beans(todo):
    pass

def _strawberry(todo):
    pass