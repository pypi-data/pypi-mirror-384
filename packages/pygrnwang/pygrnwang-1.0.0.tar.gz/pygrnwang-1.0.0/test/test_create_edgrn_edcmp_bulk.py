import numpy as np

from pygrnwang.create_edgrn_bulk import (
    pre_process_edgrn2,
    create_grnlib_edgrn2_parallel,
)

from pygrnwang.create_edcmp_bulk import (
    pre_process_edcmp2,
    compute_static_stress_edcmp2_parallel,
)

if __name__ == "__main__":
    path_green = "/e/grns_test/test_lzw_edcmp"
    path_nd = "/home/zjc/python_works/pygrnwang/test/ak135fc.nd"
    path_bin_edgrn = "/home/zjc/python_works/pygrnwang/pygrnwang/exec/edgrn2.bin"
    path_bin_edcmp = "/home/zjc/python_works/pygrnwang/pygrnwang/exec/edcmp2.bin"


    pre_process_edgrn2(
        processes_num=5,
        path_green=path_green,
        path_bin=path_bin_edgrn,
        grn_source_depth_range=[0, 30],
        grn_source_delta_depth=1,
        grn_dist_range=[0, 300],
        grn_delta_dist=1,
        obs_depth_list=[h for h in range(21)],
        wavenumber_sampling_rate=24,
        path_nd=path_nd,
        earth_model_layer_num=12,
    )
    create_grnlib_edgrn2_parallel(
        path_green=path_green, check_finished=False
    )

    # source_array = np.array([[0, 0, 10, 0.001, 0.001, 1, np.nan, 0, 90, 0]])
    # source_array_new = np.zeros((len(source_array), 9))
    # source_array_new[:, 0] = source_array[:, 8]
    # source_array_new[:, 1:9] = source_array[:, 0:8]
    # pre_process_edcmp2(
    #     processes_num=8,
    #     path_green=path_green,
    #     path_bin=path_bin_edcmp,
    #     obs_depth_list=[0, 1, 10, 20],
    #     obs_x_range=[-3, 3],
    #     obs_y_range=[-3, 3],
    #     obs_delta_x=0.01,
    #     obs_delta_y=0.01,
    #     source_array=source_array_new,
    #     source_ref=[0, 0],
    #     obs_ref=[0, 0],
    #     layered=True,
    # )
    # compute_static_stress_edcmp2_parallel_single_node(
    #     path_green=path_green, check_finished=False
    # )
