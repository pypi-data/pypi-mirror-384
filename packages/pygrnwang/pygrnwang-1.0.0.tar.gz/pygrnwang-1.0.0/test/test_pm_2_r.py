import os.path
import sys

import numpy as np
import pandas as pd

from scipy.signal import firwin
from pygrnwang.signal_process import filter_butter
from pygrnwang.read_qseis2025 import *
from pygrnwang.geo import d2km
from pygrnwang.read_by_qssp import read_by_qssp
from pygrnwang.read_qssp2020 import seek_qssp2020
from pygrnwang.read_edcmp import *
from pygrnwang.create_edcmp_bulk import *
from pygrnwang.signal_process import taper
from pygrnwang.pytaup import cal_first_p
from pygrnwang.focal_mechanism import *
import matplotlib
matplotlib.use('tkagg')
import matplotlib.pyplot as plt

if __name__ == "__main__":
    cut_length = 128
    put_pr = np.load('/home/zjc/Desktop/put_pr.npy')
    #put_pr_m = np.load('/home/zjc/Desktop/put_pr_m.npy')
    put_pr_diff = np.load('/home/zjc/Desktop/put_pr_diff.npy')

    plt.figure()
    plt.plot(put_pr[:cut_length], label='qseis_stress')
    #plt.plot(put_pr_m[:cut_length], label='qseis_stress_dj')
    plt.plot(put_pr_diff[:cut_length], label='qseis_stress_diff')
    plt.legend()
    plt.show()

    pur_pr = np.load('/home/zjc/Desktop/pur_pr.npy')
    #pur_pr_m = np.load('/home/zjc/Desktop/pur_pr_m.npy')
    pur_pr_diff = np.load('/home/zjc/Desktop/pur_pr_diff.npy')

    plt.figure()
    plt.plot(pur_pr[:cut_length], label='qseis_stress')
    #plt.plot(pur_pr_m[:cut_length], label='qseis_stress_dj')
    plt.plot(pur_pr_diff[:cut_length], label='qseis_stress_diff')
    plt.legend()
    plt.show()
