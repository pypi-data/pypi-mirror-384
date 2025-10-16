import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt
from scipy.signal import firwin, freqz, lfilter
import pandas as pd

from pygrnwang.read_qseis06_diff import *
from pygrnwang.read_qssp2020 import *
from pygrnwang.signal_process import resample, filter_butter

if __name__ == '__main__':
    event_depth_km = 10
    receiver_depth_km = 1
    az_deg = 0
    dist_km = 100
    srate = 4
    fm = [30, 40, 50]

    tp, ts = cal_first_p_s(
        event_depth_km, dist_km, receiver_depth_km)
    print(tp, ts)

    ind = 1
    cutoff = 0.25
    cut_length = 256

    numtaps = 21
    taps = firwin(numtaps, cutoff, fs=srate, window='hamming')

    strain_rate_qseis = seek_qseis06_strain_rate_diff(
        path_green="/e/grns_test/qseis06_strain",
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        before_p=None,
        pad_zeros=True,
        shift=False,
        only_seismograms=True,
        model_name="/e/grns_test/qseis06_strain/noq.nd",
        green_info=None,
    )

    strain_rate_qssp = seek_qssp2020(
        path_green='/e/grns_test/qssp_5_0.250_255.750_2.000_0.400_20000',
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        before_p=None,
        pad_zeros=True,
        shift=False,
        rotate=True,
        only_seismograms=True,
        output_type="strain_rate",
        model_name="/e/grns_test/qssp_5_0.250_255.750_2.000_0.400_20000/noq.nd",
        green_info=None,
    )

    # plt.figure()
    # plt.plot(taps)
    # plt.show()

    fig, axs = plt.subplots(nrows=6, ncols=1)
    for i in range(6):
        axs[i].plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
                    strain_rate_qseis[i][1:cut_length + 1])
        axs[i].plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
                    strain_rate_qssp[i][:cut_length])
        # axs[i].vlines(x=tp, ymin=np.min(strain_rate_qseis[:cut_length]),
        #               ymax=np.max(strain_rate_qseis[:cut_length]), color='red')
    axs[-1].legend(['qseis', 'qssp'])
    plt.xlabel('Time (s)')
    plt.show()

    fig, axs = plt.subplots(nrows=6, ncols=1)
    for i in range(6):
        strain_rate_qseis_conv = np.convolve(strain_rate_qseis[i], taps, mode='full')
        strain_rate_qssp_conv = np.convolve(strain_rate_qssp[i], taps, mode='full')
        axs[i].plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
                    strain_rate_qseis_conv[1:cut_length + 1])
        axs[i].plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
                    strain_rate_qssp_conv[:cut_length])
        # axs[i].vlines(x=tp, ymin=np.min(strain_rate_qseis[:cut_length]),
        #               ymax=np.max(strain_rate_qseis[:cut_length]), color='red')
    axs[-1].legend(['qseis', 'qssp'])
    plt.xlabel('Time (s)')
    plt.show()
