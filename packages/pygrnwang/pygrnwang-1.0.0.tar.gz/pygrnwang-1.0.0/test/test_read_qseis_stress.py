import os.path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.signal import firwin
from pygrnwang.signal_process import filter_butter
from pygrnwang.read_qseis2025 import *

if __name__ == "__main__":
    path_green = "/e/grns_test/test_qseis_vertical/"
    event_depth_km = 10
    receiver_depth_km = 1
    az_deg = 0
    dist_km = 0
    fm = [30, 40, 50]
    srate = 2
    cut_length = 256

    cutoff = 0.5
    numtaps_qseis = 21
    taps = firwin(numtaps_qseis, cutoff, fs=srate, window="hamming")

    (
        stress_rate_qseis,
        tpts_table,
        first_p,
        first_s,
        grn_dep_source,
        grn_dep_receiver,
        grn_dist,
    ) = seek_qseis2025(
        path_green=path_green,
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        before_p=None,
        pad_zeros=False,
        shift=False,
        rotate=False,
        only_seismograms=False,
        model_name=os.path.join(path_green, 'noq.nd'),
        green_info=None,
    )

    qseis_list = []
    qssp_list = []
    name_list = ["ee", "en", "ez", "nn", "nz", "zz"]

    for ind in range(6):
        # qseis_ind = resample(stress_rate_qseis[ind], srate_old=4, srate_new=srate)[:cut_length]
        qseis_ind = stress_rate_qseis[ind][:cut_length]
        # qseis_ind = np.convolve(qseis_ind, taps)[:cut_length]
        # qseis_ind = filter_butter(qseis_ind, srate, [0, cutoff])
        qseis_list.append(qseis_ind)

        df_qssp = pd.read_csv(
            '/e/grns_test/test_qssp_vertical/_stress_%s.dat' % name_list[ind], sep='\\s+')
        qssp_ind = df_qssp['test1'].values[:cut_length]
        qssp_list.append(qssp_ind)

    qseis_list = np.array(qseis_list)
    qssp_list = np.array(qssp_list)

    t = np.linspace(0, cut_length / srate, cut_length, endpoint=False)
    fig, axs = plt.subplots(6, 1)
    for ind in range(6):
        axs[ind].plot(t, qseis_list[ind], label="qseis", color="blue")
        axs[ind].plot(t, qssp_list[ind], label="qssp", color="green")
        axs[ind].set_ylabel("s%s" % name_list[ind])
    axs[-1].set_xlabel("Time (s)")
    axs[-1].legend()
    plt.show()
