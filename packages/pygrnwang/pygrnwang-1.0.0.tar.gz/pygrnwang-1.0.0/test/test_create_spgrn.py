from pygrnwang.create_spgrn_bulk import *

if __name__ == '__main__':
    sampling_interval = 1/8
    time_window = 256-sampling_interval
    path_green = "/e/grns_test/test_spgrn_%f" % sampling_interval
    os.makedirs(path_green, exist_ok=True)
    pre_process_spgrn2020(
        processes_num=1,
        path_green=path_green,
        path_bin="/home/zjc/python_works/pygrnwang/pygrnwang/exec/spgrn2020.bin",
        event_depth_list=[10],
        receiver_depth_list=[1],
        spec_time_window=time_window,
        sampling_interval=sampling_interval,
        max_frequency=0.2,
        max_slowness=0.4,
        anti_alias=0.01,
        gravity_fc=0,
        gravity_harmonic=0,
        cal_sph=1,
        cal_tor=1,
        source_radius=0,
        cal_gf=1,
        time_window=time_window,
        green_before_p=20,
        source_duration=0,
        dist_range=[0, 300],
        delta_dist_range=[100, 100],
        path_nd='/home/zjc/python_works/pygrnwang/test/ak135fc.nd',
        earth_model_layer_num=12,
        physical_dispersion=0,
    )
    create_grnlib_spgrn2020_parallel(
        path_green=path_green, check_finished=False
    )
