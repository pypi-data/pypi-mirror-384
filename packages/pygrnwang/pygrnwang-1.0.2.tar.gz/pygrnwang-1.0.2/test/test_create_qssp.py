from pygrnwang.create_qssp2020_bulk import *

if __name__ == '__main__':
    wavelet_duration = 5
    sampling_interval = 0.25
    time_window = 512-sampling_interval
    max_frequency = 2
    max_slowness = 0.4
    min_harmonic = 20000
    max_harmonic = 20000
    path_green = "/e/grns_test/qssp_%d_%.3f_%.3f_%.3f_%.3f_%d" % (
        wavelet_duration, sampling_interval, time_window,
        max_frequency, max_slowness, min_harmonic
    )
    # wavelet_duration = 0
    # sampling_interval = 0.5
    # time_window = 256 - sampling_interval
    # max_frequency = 0.5
    # max_slowness = 0.4
    # min_harmonic = 10000
    # path_green = "/e/grns_qssp2020/myanmar"
    os.makedirs(path_green, exist_ok=True)
    output_observables = [1 for _ in range(11)]
    pre_process_qssp2020(
        processes_num=6,
        path_green=path_green,
        path_bin='/home/zjc/python_works/pygrnwang/pygrnwang/exec/qssp2020.bin',
        # event_depth_list=list(np.linspace(2.5, 37.5, 8)),
        # receiver_depth_list=list(np.linspace(2.5, 37.5, 8)),
        # dist_range=[0, 800],
        # delta_dist=2,
        event_depth_list=[10],
        receiver_depth_list=[1],
        dist_range=[0, 100],
        delta_dist=10,
        spec_time_window=time_window,
        sampling_interval=sampling_interval,
        max_frequency=max_frequency,
        max_slowness=max_slowness,
        anti_alias=0.01,
        turning_point_filter=0,
        turning_point_d1=0,
        turning_point_d2=0,
        free_surface_filter=1,
        gravity_fc=0,
        gravity_harmonic=0,
        cal_sph=1,
        cal_tor=1,
        min_harmonic=min_harmonic,
        max_harmonic=max_harmonic,
        source_radius=0,
        source_duration=wavelet_duration*sampling_interval,
        output_observables=output_observables,
        time_window=time_window,
        time_reduction=-20,
        path_nd='/home/zjc/python_works/pygrnwang/test/ak135fc.nd',
        earth_model_layer_num=30,
        physical_dispersion=0,
        check_finished_tpts_table=False
    )
    create_grnlib_qssp2020_parallel(
        path_green=path_green, check_finished=False, cal_spec=True
    )
