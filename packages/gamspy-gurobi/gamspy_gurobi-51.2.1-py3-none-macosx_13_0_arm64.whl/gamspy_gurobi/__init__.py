import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['libgurobi120.dylib', 'libgsi.dylib', 'grbgetkey', 'grbprobe', 'optgurobi.def', 'libgrbcclib64.dylib']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'GUROBI 11 5 GUGLGD 1 0 2 LP MIP RMIP NLP DNLP RMINLP MINLP QCP MIQCP RMIQCP\ngmsgenus.run\ngmsgenux.out\nlibgrbcclib64.dylib grb 1 1'
