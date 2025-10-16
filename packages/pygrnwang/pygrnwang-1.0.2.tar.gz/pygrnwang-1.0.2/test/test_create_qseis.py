from pygrnwang.create_qseis06_bulk import *

if __name__ == '__main__':
    wavelet_type = 1
    wavelet_duration = 5
    sampling_interval = 0.25
    time_window = (1024 - 1) * sampling_interval
    wavenumber_sampling_rate = 12
    path_green = "/e/grns_test/qseis06"
    pre_process_qseis06(
        processes_num=1,
        path_green=path_green,
        path_bin="/home/zjc/python_works/pygrnwang/pygrnwang/exec/qseis_stress.bin",
        # event_depth_list=list(np.linspace(2.5, 37.5, 8)),
        # receiver_depth_list=list(np.linspace(2.5, 37.5, 8)),
        # dist_range=[2, 800],
        # delta_dist=2,
        event_depth_list=[10],
        receiver_depth_list=[1],
        dist_range=[2, 100],
        delta_dist=2,
        N_each_group=300,
        time_window=time_window,
        sampling_interval=sampling_interval,
        slowness_int_algorithm=0,
        slowness_window=[0, 0, 0, 0],
        time_reduction_velo=0,
        wavenumber_sampling_rate=wavenumber_sampling_rate,
        anti_alias=0.01,
        free_surface=True,
        wavelet_duration=wavelet_duration,
        wavelet_type=wavelet_type,
        flat_earth_transform=False,
        path_nd='/home/zjc/articles/Myanmar/myanmar.nd',
        earth_model_layer_num=25,
        # path_nd="/e/grns_test/test_lzw_edcmp/test.nd",
        # earth_model_layer_num=3,
    )
    create_grnlib_qseis06_parallel(
        path_green=path_green, check_finished=False
    )
