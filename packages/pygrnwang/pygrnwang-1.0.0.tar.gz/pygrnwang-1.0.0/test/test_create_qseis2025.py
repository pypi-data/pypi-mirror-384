from pygrnwang.create_qseis2025_bulk import *

if __name__ == "__main__":
    wavelet_type = 2
    wavelet_duration = 5
    sampling_interval = 0.25
    time_window = (512 - 1) * sampling_interval
    wavenumber_sampling_rate = 12
    path_green = "/e/grns_test/qseis_%d_%d_%.3f_%.3f_%d_new_m" % (
        wavelet_type, wavelet_duration, sampling_interval, time_window,
        wavenumber_sampling_rate
    )
    # path_green = '/e/grn_qseis2025/ak135'
    pre_process_qseis2025(
        processes_num=1,
        path_green=path_green,
        path_bin="/home/zjc/python_works/pygrnwang/pygrnwang/exec/qseis2025.bin",
        event_depth_list=[10],
        receiver_depth_list=[1],
        dist_range=[1, 100],
        delta_dist=10,
        # event_depth_list=[h for h in range(1, 31, 2)],
        # receiver_depth_list=[h for h in range(0, 30, 2)],
        # dist_range=[0, 1000-1],
        # delta_dist=1,
        N_each_group=100,
        time_window=time_window,
        sampling_interval=sampling_interval,
        output_observables=[1, 1, 1, 1, 1],
        slowness_int_algorithm=0,
        eps_estimate_wavenumber=1e-6,
        source_radius_ratio=0.05,
        slowness_window=[0, 0, 0, 0],
        time_reduction_velo=0,
        wavenumber_sampling_rate=wavenumber_sampling_rate,
        anti_alias=0.01,
        free_surface=True,
        wavelet_duration=wavelet_duration,
        wavelet_type=wavelet_type,
        flat_earth_transform=False,
        path_nd='/home/zjc/python_works/pygrnwang/test/ak135fc.nd',
        earth_model_layer_num=30,
        # path_nd="/e/grns_test/test_lzw_edcmp/test.nd",
        # earth_model_layer_num=3,
    )
    create_grnlib_qseis2025_parallel(path_green=path_green, check_finished=False)
