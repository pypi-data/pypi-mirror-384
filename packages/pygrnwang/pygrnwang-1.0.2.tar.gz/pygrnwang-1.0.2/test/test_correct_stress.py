import os.path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.signal import firwin
from pygrnwang.signal_process import filter_butter, linear_interp
from pygrnwang.read_qseis2025 import *
from pygrnwang.geo import d2km
from pygrnwang.read_by_qssp import read_by_qssp
from pygrnwang.read_qssp2020 import seek_qssp2020
from pygrnwang.read_edcmp import *
from pygrnwang.create_edcmp_bulk import *
from pygrnwang.signal_process import *
from pygrnwang.obspy_taup import cal_first_p
from pygrnwang.focal_mechanism import *


def correct_zero_frequency(data, srate, A0, f_c, tc1, tc2,
                           ratio_interp=0):
    N_data = len(data)
    data = data[tc1:tc2]
    data[0] = 0
    data[-1] = 0
    # data = taper(data)
    if ratio_interp > 0:
        # u = np.concatenate([np.zeros(pad_len // 2), data.copy(), np.zeros(pad_len - pad_len // 2)])
        # l = ratio_interp * (tc2 - tc1)
        u = resample(data=data, srate_old=srate, srate_new=srate * ratio_interp)
        uf = np.fft.fft(u) / (srate * ratio_interp)
    else:
        u = data.copy()
        uf = np.fft.fft(u) / srate
    uf_correct = uf.copy()
    uf_correct[0] = A0

    N = len(uf)
    A_f = np.abs(uf)
    phi_f = np.angle(uf)

    # f = np.fft.fftfreq(N, 1 / srate)[:N // 2]
    # f_c = max(2, np.argmin(np.abs(cut_freq - f)))
    # print(f_c)

    w = np.zeros(N)
    w[0:f_c + 1] = 1 - 1 / 2 * (1 + np.cos(np.pi * np.arange(f_c + 1) / f_c))  # 0->1
    w[-f_c:] = w[1:f_c + 1][::-1]

    uf_correct[1:f_c + 1] = ((1 - w[1:f_c + 1]) * np.abs(A0) + w[1:f_c + 1] * A_f[1:f_c + 1]
                             ) * np.exp(1j * np.complex128(phi_f[1:f_c + 1]))
    uf_correct[-f_c:] = ((1 - w[-f_c:]) * np.abs(A0) + w[-f_c:] * A_f[-f_c:]
                         ) * np.exp(1j * np.complex128(phi_f[-f_c:]))

    if ratio_interp > 0:
        u_correct = np.real(np.fft.ifft(uf_correct)) * srate * ratio_interp
        # u_correct = filter_butter(data=u_correct, srate=srate * ratio_interp,
        #                           freq_band=[0, srate / 2])
        u_correct = resample(data=u_correct, srate_old=srate * ratio_interp, srate_new=srate)
    else:
        u_correct = np.real(np.fft.ifft(uf_correct)) * srate
    # u_correct = u_correct - u_correct[0]
    # u_correct = taper(u_correct, taper_len)
    u_correct = np.concatenate([np.zeros(tc1), u_correct, np.zeros(N_data - tc2)])
    return u_correct


if __name__ == "__main__":
    correct = True
    wavelet_type = 1
    wavelet_duration = 5
    sampling_interval = 0.25
    time_window_qseis = (1024 - 1) * sampling_interval
    wavenumber_sampling_rate = 12
    time_window_qssp = 256 - sampling_interval
    max_frequency = 2
    max_slowness = 0.4
    min_harmonic = 20000
    path_green_qseis = "/e/grns_test/qseis_%d_%d_%.3f_%.3f_%d_" % (
        wavelet_type, wavelet_duration, sampling_interval, time_window_qseis,
        wavenumber_sampling_rate
    )
    #path_green_qseis = "/e/grns_test/qseis_1_5_0.250_255.750_12_m"
    path_green_qssp = "/e/grns_test/qssp_%d_%.3f_%.3f_%.3f_%.3f_%d" % (
        wavelet_duration, sampling_interval, time_window_qssp,
        max_frequency, max_slowness, min_harmonic
    )
    path_green_edcmp = "/e/grns_test/test_edcmp"
    M0 = 31126160000 * (1 ** 2) * 1e6
    event_depth_km = 10
    receiver_depth_km = 1
    az_deg = 0
    dist_km = 6
    fm = [45, 90, 90]
    srate = 4
    cut_length = 128
    output_type = 'stress_rate'
    print(
        "%f %f"
        % (
            dist_km / d2km * np.cos(np.deg2rad(az_deg)),
            dist_km / d2km * np.sin(np.deg2rad(az_deg)),
        )
    )

    cutoff = 0.4
    numtaps = 51
    stf = firwin(numtaps, cutoff, fs=srate, window="hamming")
    stf = stf / (np.sum(stf) / srate)

    stress_qseis = seek_qseis2025(
        path_green=path_green_qseis,
        event_depth_km=event_depth_km,
        receiver_depth_km=receiver_depth_km,
        az_deg=az_deg,
        dist_km=dist_km,
        focal_mechanism=fm,
        srate=srate,
        output_type=output_type,
        before_p=None,
        pad_zeros=True,
        rotate=True,
        only_seismograms=True,
        model_name=os.path.join(path_green_qseis, "noq.nd"),
        green_info=None,
    )
    # stress_qseis = np.roll(stress_qseis, -40, axis=1)/10
    # fm = check_convert_fm(focal_mechanism=fm)
    # fm = mt2plane(fm)[0]
    source_array = np.array(
        [
            [
                0,
                0,
                event_depth_km,
                fm[0],
                fm[1],
                fm[2],
                0,
                0,
                1,
            ]
        ]
    )
    obs_point = np.array(
        [
            dist_km / d2km * np.cos(np.deg2rad(az_deg)),
            dist_km / d2km * np.sin(np.deg2rad(az_deg)),
            receiver_depth_km,
        ]
    )

    stress_qssp = seek_qssp2020(
        path_green=path_green_qssp,
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
        output_type=output_type,
        model_name=os.path.join(path_green_qssp, "noq.nd"),
        green_info=None
    )
    # stress_qssp_direct = read_by_qssp(
    #     path_green=path_green_qssp,
    #     event_lat=0,
    #     event_lon=0,
    #     event_depth_km=event_depth_km,
    #     receiver_lat=obs_point[0],
    #     receiver_lon=obs_point[1],
    #     receiver_depth_km=receiver_depth_km,
    #     focal_mechanism=fm,
    #     srate=srate,
    #     read_name="hash",
    #     output_type=output_type,
    #     green_info=None,
    #     check_finished=False
    # )

    path_bin_edcmp = "/home/zjc/python_works/pygrnwang/pygrnwang/exec/edcmp2.bin"
    source_array_new = np.zeros((len(source_array), 9))
    source_array_new[:, 0] = source_array[:, 8]
    source_array_new[:, 1:9] = source_array[:, 0:8]
    pre_process_edcmp2(
        processes_num=1,
        path_green=path_green_edcmp,
        path_bin=path_bin_edcmp,
        obs_depth_list=[receiver_depth_km],
        obs_x_range=[obs_point[0] - 0.01, obs_point[0] + 0.01],
        obs_y_range=[obs_point[1] - 0.01, obs_point[1] + 0.01],
        obs_delta_x=0.001,
        obs_delta_y=0.001,
        source_array=source_array_new,
        source_ref=[0, 0],
        obs_ref=[0, 0],
        layered=True,
    )
    compute_static_stress_edcmp2_sequential(
        path_green=path_green_edcmp, check_finished=False)
    stress_edcmp = seek_edcmp2(
        path_green_edcmp,
        'stress',
        np.array([obs_point]),
        geo_coordinate=True,
    )[0] * 1e6

    qseis_list = []
    qssp_list = []
    qssp_direct_list = []
    name_list = ["ee", "en", "ez", "nn", "nz", "zz"]
    first_p = cal_first_p(
        event_depth_km=event_depth_km,
        dist_km=dist_km,
        receiver_depth_km=receiver_depth_km,
        model_name='ak135'
    )
    tc1 = max(1, round(first_p * srate - 1))
    tc2 = round(dist_km * max_slowness * srate +
                1.5 * wavelet_duration * sampling_interval * srate+len(stf))
    print(tc1, tc2)
    for ind in range(6):
        qseis_ind = stress_qseis[ind][:cut_length] * M0
        #qseis_ind[:tc1] = 0
        #qseis_ind = np.convolve(qseis_ind, stf)[:cut_length] / srate
        if correct:
            qseis_ind = correct_zero_frequency(
                qseis_ind, srate, stress_edcmp[ind], 4,
                tc1, tc2, ratio_interp=0
            )

        # qseis_ind = np.convolve(qseis_ind, stf)[:cut_length]/srate
        # qseis_ind = filter_butter(qseis_ind, srate, [0, cutoff])
        # qseis_ind = np.cumsum(qseis_ind) / srate
        qseis_list.append(qseis_ind)

        qssp_ind = stress_qssp[ind][:cut_length] * M0
        qssp_ind = np.concatenate([np.zeros(1), qssp_ind])[:cut_length]
        #qssp_ind = np.convolve(qssp_ind, stf)[:cut_length]/srate
        # qssp_ind = filter_butter(qssp_ind, srate, [0, cutoff])
        # qssp_ind = np.cumsum(qssp_ind) / srate
        qssp_list.append(qssp_ind)

        # qssp_direct_ind = stress_qssp_direct[ind][round(20*srate):cut_length+round(20*srate)]*M0
        # #qssp_direct_ind = stress_qssp_direct[ind][:cut_length]
        # qssp_direct_ind = np.concatenate([np.zeros(1), qssp_direct_ind])[:cut_length]
        # qssp_direct_ind = np.convolve(qssp_direct_ind, stf)[:cut_length]
        # #qssp_direct_ind = filter_butter(qssp_direct_ind, srate, [0, cutoff])
        # # qssp_direct_ind = np.cumsum(qssp_direct_ind)/srate
        # qssp_direct_list.append(qssp_direct_ind)
    qseis_list = np.array(qseis_list)
    qssp_list = np.array(qssp_list)
    qssp_direct_list = np.array(qssp_direct_list)

    A_max = max(np.max(np.abs(qseis_list)), np.max(np.abs(qssp_list))) * 1.1
    t = np.linspace(0, cut_length / srate, cut_length, endpoint=False)
    fig, axs = plt.subplots(6, 1)
    for ind in range(6):
        axs[ind].plot(t, qseis_list[ind], label="qseis", color="red")
        axs[ind].plot(t, qssp_list[ind], label="qssp", color="green")
        # axs[ind].plot(t, qssp_direct_list[ind], label="qssp_direct", color="blue")
        # axs[ind].set_ylim([-A_max, A_max])
        axs[ind].set_ylabel("sr_%s" % name_list[ind])
    axs[-1].set_xlabel("Time (s)")
    axs[-1].legend(loc="upper right")
    plt.show()

    f = np.fft.fftfreq(cut_length, 1 / srate)[:cut_length // 2]
    fig, axs = plt.subplots(1, 6)
    for ind in range(6):
        A_qseis = np.abs(np.fft.fft(qseis_list[ind]))[:cut_length // 2] / srate
        A_qssp = np.abs(np.fft.fft(qssp_list[ind]))[:cut_length // 2] / srate
        axs[ind].plot(f, A_qseis, marker='o', label="qseis", color="red")
        axs[ind].plot(f, A_qssp, marker='o', label="qssp", color="blue")
        axs[ind].plot(f, np.ones_like(A_qseis) * np.abs(stress_edcmp[ind]),
                      label="edcmp", color="black")
        axs[ind].set_yscale('log')
        axs[ind].set_ylabel("s_%s" % name_list[ind])
        axs[ind].set_xlabel("Frequency (Hz)")
        axs[ind].legend(loc='lower right')
        # print(A_qseis[0], np.sum(qseis_list[ind]) / srate)
    plt.subplots_adjust(wspace=0.1, hspace=0.1)
    plt.show()

    A_max = max(np.max(np.abs(qseis_list)), np.max(np.abs(qssp_list))) * 1.1

    t = np.linspace(0, cut_length / srate, cut_length, endpoint=False)
    fig, axs = plt.subplots(6, 1)
    for ind in range(6):
        # qseis_list[ind] = np.convolve(qseis_list[ind], stf)[:cut_length] / srate
        # qssp_list[ind] = np.convolve(qssp_list[ind], stf)[:cut_length] / srate
        if output_type == 'stress_rate':
            qseis_list[ind] = np.cumsum(qseis_list[ind]) / srate
            qssp_list[ind] = np.cumsum(qssp_list[ind]) / srate
        axs[ind].plot(t, qseis_list[ind], label="qseis", color="red")
        axs[ind].plot(t, qssp_list[ind], label="qssp", color="green")
        # axs[ind].plot(t, qssp_direct_list[ind], label="qssp_direct", color="blue")
        axs[ind].plot(t, np.ones_like(qseis_list[ind]) * stress_edcmp[ind],
                      label="edcmp", color="black")
        # axs[ind].set_ylim([-A_max, A_max])
        axs[ind].set_ylabel("s_%s" % name_list[ind])
    axs[-1].set_xlabel("Time (s)")
    axs[-1].legend(loc="upper right")
    plt.show()

    print(['qseis: '] + ["%10.4e" % _ for _ in np.mean(qseis_list[:, cut_length - 10: cut_length], axis=1)])
    print(['qssp : '] + ["%10.4e" % _ for _ in np.mean(qssp_list[:, cut_length - 10: cut_length], axis=1)])
    print(['edcmp: '] + ["%10.4e" % _ for _ in stress_edcmp])
