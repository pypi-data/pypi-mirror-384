import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt
from scipy.signal import firwin, freqz, lfilter
import pandas as pd
import numpy as np

from pygrnwang.read_qseis06 import *
from pygrnwang.read_qssp2020 import *
from pygrnwang.read_spgrn import *
from pygrnwang.signal_process import resample, filter_butter

if __name__ == '__main__':
    event_depth_km = 10
    receiver_depth_km = 1
    az_deg = 20
    dist_km = 300
    srate = 0.25
    fm = [30, 40, 50]
    tp,ts=cal_first_p_s(
        event_depth_km,dist_km,receiver_depth_km)
    print(tp, ts)

    ind = 2
    cutoff = 0.05
    cut_length = 64

    numtaps = 41
    taps = firwin(numtaps, cutoff, fs=srate, window='hamming')

    u_qseis = seek_qseis06(
        path_green="/e/grns_test/test_qseis",
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        rotate=True,
        before_p=20,
        pad_zeros=False,
        shift=False,
        only_seismograms=True,
        model_name="/e/grns_test/test_qseis/noq.nd",
        green_info=None,
    )
    u_qseis = u_qseis[ind]
    #u_qseis = u_qseis[2:]
    u_qseis_conv = np.convolve(u_qseis, taps, mode='full')

    u_qssp = seek_qssp2020(
        path_green="/e/grns_test/test_qssp",
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        before_p=20,
        pad_zeros=False,
        shift=False,
        rotate=True,
        only_seismograms=True,
        output_type="velo",
        model_name="/e/grns_test/test_qssp/noq.nd",
        green_info=None,
    )
    u_qssp = u_qssp[ind]
    u_qssp_conv = np.convolve(u_qssp, taps, mode='full')

    u_spgrn = seek_spgrn2020(
        path_green="/e/grns_test/test_spgrn",
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        before_p=20,
        pad_zeros=False,
        shift=False,
        rotate=True,
        only_seismograms=True,
        model_name="/e/grns_test/test_spgrn/noq.nd",
        green_info=None,
    )
    u_spgrn = u_spgrn[ind]
    u_spgrn_conv = np.convolve(u_spgrn, taps, mode='full')

    # plt.figure()
    # plt.plot(taps)
    # plt.show()

    plt.figure()
    plt.plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
             u_qseis[:cut_length], label='qseis')
    plt.plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
             u_qssp[:cut_length], label='qssp')
    plt.plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
             u_spgrn[:cut_length], label='spgrn')
    plt.legend()
    # plt.vlines(x=tp, ymin=np.min(u_qseis[:cut_length]),
    #            ymax=np.max(u_qseis[:cut_length]),color='red')
    plt.xlabel('Time (s)')
    plt.show()

    plt.figure()
    plt.plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
             u_qseis_conv[:cut_length], label='qseis')
    plt.plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
             u_qssp_conv[:cut_length], label='qssp')
    plt.plot(np.linspace(0, cut_length / srate, cut_length, endpoint=False),
             u_spgrn_conv[:cut_length], label='spgrn')
    plt.legend()
    plt.vlines(x=tp, ymin=np.min(u_qseis_conv[:cut_length]),
               ymax=np.max(u_qseis_conv[:cut_length]),color='red')
    plt.xlabel('Time (s)')
    plt.show()


