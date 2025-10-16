import pandas as pd
import numpy as np
from pygrnwang.read_spgrn import *
from pygrnwang.read_qssp2020 import *

from pygrnwang.obspy_taup import cal_first_p

if __name__ == '__main__':
    event_depth_km = 10
    receiver_depth_km = 1
    az_deg = 20
    dist_km = 300
    u_spgrn_list = []
    u_qssp_list = []
    for n in [1, 0, -1, -2, -3, -4]:
        sampling_interval = 2 ** n
        srate = 1 / sampling_interval
        fm = [0, 0, 1, 0, 0, 0]
        ind = 2
        tp = cal_first_p(event_depth_km,
                         dist_km,
                         receiver_depth_km,
                         model_name="/e/grns_test/test_spgrn/noq.nd")
        (
            u_spgrn,
            tpts_table,
            first_p,
            first_s,
            grn_dep_source,
            grn_dep_receiver,
            grn_dist,
        ) = seek_spgrn2020(
            path_green="/e/grns_test/test_spgrn_%f" % sampling_interval,
            event_depth_km=event_depth_km,
            receiver_depth_km=receiver_depth_km,
            az_deg=az_deg,
            dist_km=dist_km,
            focal_mechanism=fm,
            srate=srate,
            before_p=None,
            pad_zeros=False,
            shift=False,
            rotate=True,
            only_seismograms=False,
            model_name="/e/grns_test/test_spgrn/noq.nd",
            green_info=None,
        )
        u_spgrn = np.concatenate([np.zeros(round(tpts_table['p_onset'] * srate)), u_spgrn[ind]])
        u_spgrn = u_spgrn[round(20 * srate):]
        print(tpts_table)
        print(tp)
        print(grn_dep_source)
        print(grn_dep_receiver)
        print(grn_dist)
        print()

        (
            u_qssp,
            tpts_table,
            first_p,
            first_s,
            grn_dep_source,
            grn_dep_receiver,
            grn_dist,
        ) = seek_qssp2020(
            path_green="/e/grns_test/test_qssp_%f" % sampling_interval,
            event_depth_km=event_depth_km,
            receiver_depth_km=receiver_depth_km,
            az_deg=az_deg,
            dist_km=dist_km,
            focal_mechanism=fm,
            srate=srate,
            before_p=None,
            pad_zeros=False,
            shift=False,
            rotate=True,
            only_seismograms=False,
            output_type="velo",
            model_name="/e/grns_test/test_qssp/noq.nd",
            green_info=None,
        )
        u_qssp = u_qssp[ind]
        # u_qssp = np.concatenate([np.zeros(2), u_qssp])
        print(tpts_table)
        print(grn_dep_source)
        print(grn_dep_receiver)
        print(grn_dist)
        print()

        u_spgrn_list.append(u_spgrn)
        u_qssp_list.append(u_qssp)

    import matplotlib

    matplotlib.use('tkagg')

    import matplotlib.pyplot as plt
    exp_list = [1, 0, -1, -2, -3, -4]
    fig,axs=plt.subplots(6,1, figsize=(24, 10))
    for n in range(6):
        print(n, len(u_qssp_list[n]),2**exp_list[n])
        print(n, len(u_spgrn_list[n]), 2 ** exp_list[n])
        t = np.linspace(0, len(u_qssp_list[n])*(2**exp_list[n]), len(u_qssp_list[n]), endpoint=False)
        axs[n].plot(t, u_qssp_list[n], label='qssp', linewidth=0.5)
        axs[n].plot(t, u_spgrn_list[n][:len(u_qssp_list[n])], label='spgrn', linewidth=0.5)
    plt.legend()
    plt.show()

    plt.figure()
    plt.plot(u_qssp_list[4], label='qssp')
    plt.plot(u_spgrn_list[4], label='spgrn')
    plt.legend()
    plt.show()

    plt.figure()
    plt.plot(u_qssp_list[5], label='qssp')
    plt.plot(u_spgrn_list[5], label='spgrn')
    plt.legend()
    plt.show()

    # from scipy.signal import firwin, freqz, lfilter
    #
    # cutoff = 0.05
    # numtaps = 21
    # taps = firwin(numtaps, cutoff, fs=srate, window='hamming')
    # u_qssp_conv = np.convolve(u_qssp, taps, mode='full')
    # u_spgrn_conv = np.convolve(u_spgrn, taps, mode='full')
    #
    # plt.figure()
    # plt.plot(u_qssp_conv, label='qssp')
    # plt.plot(u_spgrn_conv, label='spgrn')
    # plt.legend()
    # plt.show()
