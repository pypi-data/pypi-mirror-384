import pandas as pd
import numpy as np
from os import path as osp

luts_path = osp.dirname(osp.realpath(__file__)) + '/luts/'

CROP = pd.read_csv(luts_path + 'crop.csv')
CROP = CROP.set_index('crop').replace({np.nan:None}).to_dict('index')

SOIL = pd.read_csv(luts_path + 'soil.csv')
SOIL = SOIL.set_index('type').replace({np.nan:None}).to_dict('index')

IRRIGATION = pd.read_csv(luts_path + 'irrigation.csv')
IRRIGATION = IRRIGATION.set_index('type').replace({np.nan:None}).to_dict('index')