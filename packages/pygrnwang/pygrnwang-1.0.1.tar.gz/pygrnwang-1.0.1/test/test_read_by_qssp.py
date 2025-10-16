import sys

import datetime

from pygrnwang.focal_mechanism import plane2mt
from pygrnwang.geo import d2km, cal_first_p_s
from pygrnwang.read_qssp2020 import seek_qssp2020
from pygrnwang.read_by_qssp import read_by_qssp

from scipy.io import savemat
from scipy import signal
import numpy as np

if __name__ == "__main__":
    import time

    path_green = "/e/grns_test/test_qssp_lzw"
    event_depth_km = 0
    receiver_depth_km = 0
    az_deg = 40
    dist_km = 200
    focal_mechanism = [0, 90, -180]
    source_array = np.array(
        [
            [
                0,
                0,
                event_depth_km,
                focal_mechanism[0],
                focal_mechanism[1],
                focal_mechanism[2],
                0.001,
                0.001,
                1,
                1,
            ]
        ]
    )
    srate = 1
    before_p = None
    pad_zeros = False
    shift = False
    rotate = True
    only_seismograms = False
    output_type = "strain"
    model_name = "/e/grns_test/test_qssp_lzw/noq.nd"
    # s = time.time()
    # for i in range(1):
    #     seismograms, tpts_table, first_p, first_s, grn_dep, grn_receiver, green_dist = (
    #         seek_qssp2020(
    #             path_green,
    #             event_depth_km,
    #             receiver_depth_km,
    #             az_deg,
    #             dist_km,
    #             focal_mechanism,
    #             srate,
    #             before_p,
    #             pad_zeros,
    #             shift,
    #             rotate,
    #             only_seismograms,
    #             output_type,
    #             model_name,
    #         )
    #     )
    # e = time.time()
    # print("run time:", e - s, "s")
    # #
    # # for i in range(seismograms.shape[0]):
    # #     w = signal.firwin(11, 0.1, fs=srate / 2)
    # #     seismograms[i] = signal.convolve(seismograms[i], w, "same")
    # #     # w = signal.windows.hann(srate)
    # #     # seismograms[i] = signal.fftconvolve(seismograms[i],w, 'same')
    # mu = 31126160000
    # area = 1  # 1e6
    # disp_source = 1
    # m0 = mu * area * disp_source
    # print(m0)
    # print(seismograms.shape)
    # print(seismograms[1, round(0.4 * dist_km * srate + 1)] * m0)
    # print(tpts_table, first_p, first_s, grn_dep, grn_receiver, green_dist)

    first_p, _ = cal_first_p_s(event_depth_km, dist_km, receiver_depth_km, model_name)

    s = datetime.datetime.now()
    seismograms_qssp = read_by_qssp(
        path_green=path_green,
        source_array=source_array,
        obs_point=[
            dist_km * np.cos(np.deg2rad(az_deg)) / d2km,
            dist_km * np.sin(np.deg2rad(az_deg)) / d2km,
            receiver_depth_km,
        ],
        srate=srate,
        read_name="hash",
        output_type=output_type,
        green_info=None,
        check_finished=False,
    )
    e = datetime.datetime.now()
    print(e - s)
    # print(grn_dep, grn_receiver)

    import matplotlib.pyplot as plt
    import matplotlib


    ind_com = 4
    plt.figure()
    t = np.linspace(
        0, len(seismograms_qssp[ind_com]) / srate, len(seismograms_qssp[ind_com]), endpoint=False
    )
    plt.plot(
        np.array([first_p, first_p]),
        np.array([np.min(seismograms_qssp[ind_com]), np.max(seismograms_qssp[ind_com])]),
        color="red",
    )
    # plt.plot(t, seismograms[ind_com], color="blue")
    plt.plot(t, seismograms_qssp[ind_com], color="green")
    #plt.legend(["read_by_python", "read_by_qssp"])
    plt.show()
