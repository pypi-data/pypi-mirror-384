import sys

from pygrnwang.focal_mechanism import plane2mt
from pygrnwang.geo import cal_first_p_s
from pygrnwang.read_qssp2020 import seek_qssp2020

from scipy.io import savemat
from scipy import signal
import numpy as np

if __name__ == "__main__":
    import time

    s = time.time()
    path_green = "/e/grns_test/test_qssp"
    event_depth_km = 10
    receiver_depth_km = 1
    az_deg = 60
    dist_km = 100
    focal_mechanism = [30, 40, 50]
    srate = 2
    before_p = None
    pad_zeros = True
    shift = False
    rotate = True
    only_seismograms = False
    output_type = "stress"
    model_name = "/e/grns_test/test_qssp/noq.nd"
    for i in range(1):
        seismograms, tpts_table, first_p, first_s, grn_dep, grn_receiver, green_dist = (
            seek_qssp2020(
                path_green,
                event_depth_km,
                receiver_depth_km,
                az_deg,
                dist_km,
                focal_mechanism,
                srate,
                before_p,
                pad_zeros,
                shift,
                rotate,
                only_seismograms,
                output_type,
                model_name,
            )
        )
    e = time.time()
    print("run time:", e - s, "s")
    #
    # for i in range(seismograms.shape[0]):
    #     w = signal.firwin(11, 0.1, fs=srate / 2)
    #     seismograms[i] = signal.convolve(seismograms[i], w, "same")
    #     # w = signal.windows.hann(srate)
    #     # seismograms[i] = signal.fftconvolve(seismograms[i],w, 'same')
    mu = 31126160000
    area = 1  # 1e6
    disp_source = 1
    m0 = mu * area * disp_source
    print(m0)
    print(seismograms.shape)
    print(seismograms[1, round(0.4 * dist_km * srate + 1)] * m0)
    print(tpts_table, first_p, first_s, grn_dep, grn_receiver, green_dist)

    first_p, _ = cal_first_p_s(
        event_depth_km, dist_km, receiver_depth_km,  "/e/grns_test/test_qssp/noq.nd"
    )

    import matplotlib.pyplot as plt

    t = np.linspace(0, len(seismograms[0]) / srate, len(seismograms[0]), endpoint=False)
    fig, axs = plt.subplots(6, 1)
    for ind in range(6):
        axs[ind].plot(t, seismograms[ind])
    axs[-1].set_xlabel("Time (s)")
    axs[-1].legend(loc="upper right")
    plt.show()