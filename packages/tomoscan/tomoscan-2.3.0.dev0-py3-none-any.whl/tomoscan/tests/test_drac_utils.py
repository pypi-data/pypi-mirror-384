import json
import numpy
import pint

from tomoscan.utils.drac.mapper import (
    flatten_vol_metadata,
    map_nabu_keys_to_drac,
)

_ureg = pint.get_application_registry()


_NABU_VOL_RAW_METADATA = {
    "@NX_class": "NXcollection",
    "date": "2024-10-02T17:42:01",
    "nabu_config": {
        "dataset": {
            "binning": 1,
            "binning_z": 1,
            "darks_flats_dir": "None",
            "exclude_projections": "None",
            "hdf5_entry": "/entry0000",
            "location": "/mnt/multipath-shares/tmp_14_days/payno/test_deployment/bambou_hercules_0001.nx",
            "nexus_version": 1.0,
            "overwrite_metadata": "",
            "projections_subsampling": numpy.array([1, 0]),
        },
        "output": {
            "file_format": "hdf5",
            "file_prefix": "bambou_hercules_0001_vol",
            "float_clip_values": "None",
            "jpeg2000_compression_ratio": "None",
            "location": "/mnt/multipath-shares/tmp_14_days/payno/test_deployment/reconstructed_volumes",
            "overwrite_results": True,
            "tiff_single_file": False,
        },
        "phase": {
            "distance_cm": 210,
            "distance_m": 2.1,
            "ctf_advanced_params": "length_scale=1e-05; lim1=1e-05; lim2=0.2; normalize_by_mean=True",
            "ctf_geometry": "z1_v=None; z1_h=None; detec_pixel_size=None; magnification=True",
            "delta_beta": 100.0,
            "method": "paganin",
            "padding_type": "edge",
            "unsharp_coeff": 0.0,
            "unsharp_method": "gaussian",
            "unsharp_sigma": 0.0,
            "pixel_size_m": 3.0325e-06,
            "pixel_size_microns": 3.0325,
            "energy_kev": 130,
        },
        "pipeline": {
            "resume_from_step": "None",
            "save_steps": "None",
            "steps_file": "None",
            "verbosity": "info",
        },
        "postproc": {"histogram_bins": 1000000, "output_histogram": True},
        "preproc": {
            "autotilt_options": "None",
            "ccd_filter_enabled": False,
            "ccd_filter_threshold": 0.04,
            "detector_distortion_correction": "None",
            "detector_distortion_correction_options": "None",
            "dff_sigma": 0.0,
            "double_flatfield_enabled": False,
            "flat_distortion_correction_enabled": False,
            "flat_distortion_params": "tile_size=100; "
            "interpolation_kind='linear'; "
            "padding_mode='edge'; "
            "correction_spike_threshold=None",
            "flatfield": True,
            "log_max_clip": 10.0,
            "log_min_clip": 1e-06,
            "normalize_srcurrent": True,
            "processes_file": "None",
            "rotate_projections": "None",
            "rotate_projections_center": "None",
            "sino_normalization": "None",
            "sino_normalization_file": "",
            "sino_rings_correction": "None",
            "sino_rings_options": "sigma=1.0 ; levels=10 ; " "padding=False",
            "take_logarithm": True,
            "tilt_correction": "None",
        },
        "reconstruction": {
            "angle_offset": 0.0,
            "angles_file": "None",
            "axis_correction_file": "None",
            "centered_axis": True,
            "clip_outer_circle": True,
            "cor_options": "side='from_file'",
            "cor_slice": "None",
            "enable_halftomo": True,
            "end_x": -1,
            "end_y": -1,
            "end_z": 180,
            "fbp_filter_cutoff": 1.0,
            "fbp_filter_type": "ramlak",
            "iterations": 200,
            "method": "FBP",
            "optim_algorithm": "chambolle-pock",
            "padding_type": "edge",
            "positivity_constraint": True,
            "preconditioning_filter": True,
            "rotation_axis_position": 2060.0,
            "sample_detector_dist": "None",
            "source_sample_dist": "None",
            "start_x": 0,
            "start_y": 0,
            "start_z": 150,
            "translation_movements_file": "None",
            "weight_tv": 0.01,
        },
        "resources": {
            "cpu_workers": 0,
            "gpu_id": numpy.array([], dtype=numpy.float64),
            "gpus": 1,
            "memory_per_node": numpy.array([90.0, 1.0]),
            "method": "local",
            "queue": "gpu",
            "threads_per_node": numpy.array([100.0, 1.0]),
            "walltime": numpy.array([1, 0, 0]),
        },
    },
    "processing_options": {
        "flatfield": {
            "binning": numpy.array([1, 1]),
            "do_flat_distortion": False,
            "flat_distortion_params": {
                "correction_spike_threshold": "None",
                "interpolation_kind": "linear",
                "padding_mode": "edge",
                "tile_size": 100,
            },
            "flats_srcurrent": numpy.array([0.19458202]),
            "normalize_srcurrent": True,
            "projs_indices": numpy.array([81, 82, 83, 4478, 4479, 4480]),
            "radios_srcurrent": numpy.array(
                [0.19458, 0.1945795, 0.19457899, 0.19364, 0.19364, 0.19364],
                dtype=numpy.float32,
            ),
        },
        "histogram": {"histogram_bins": 1000000},
        "read_chunk": {
            "binning": numpy.array([1, 1]),
            "dataset_subsampling": numpy.array([1, 0]),
            "files": {
                "100": "silx:///mnt/multipath-shares/tmp_14_days/payno/test_deployment/bambou_hercules_0001.nx?path=/entry0000/instrument/detector/data&slice=100",
                "999": "silx:///mnt/multipath-shares/tmp_14_days/payno/test_deployment/bambou_hercules_0001.nx?path=/entry0000/instrument/detector/data&slice=999",
            },
            "sub_region": "None",
        },
        "reconstruction": {
            "angles": numpy.array(
                [
                    0.00000000e00,
                    1.43989663e-03,
                    2.85934019e-03,
                    ...,
                    6.27849473e00,
                    6.27991963e00,
                    6.28134453e00,
                ]
            ),
            "axis_correction": "None",
            "centered_axis": True,
            "clip_outer_circle": True,
            "cor_estimated_auto": False,
            "enable_halftomo": True,
            "end_x": 4121,
            "end_y": 4121,
            "end_z": 180,
            "fbp_filter_cutoff": 1.0,
            "fbp_filter_type": "ramlak",
            "method": "FBP",
            "padding_type": "edge",
            "position": numpy.array([0.026, 0.0013, 0.0007]),
            "rotation_axis_position": 2060.0,
            "sample_detector_dist": "None",
            "source_sample_dist": "None",
            "start_x": 0,
            "start_y": 0,
            "start_z": 150,
            "voxel_size_cm": numpy.array([1.25e-05, 2.25e-05, 3.25e-05]),
        },
        "save": {
            "file_format": "hdf5",
            "file_prefix": "bambou_hercules_0001_vol",
            "float_clip_values": "None",
            "jpeg2000_compression_ratio": "None",
            "location": "/mnt/multipath-shares/tmp_14_days/payno/test_deployment/reconstructed_volumes",
            "overwrite": True,
            "overwrite_results": True,
            "tiff_single_file": False,
        },
        "take_log": {"log_max_clip": 10.0, "log_min_clip": 1e-06},
    },
    "reconstruction_stages": {
        "((0, 4400), (150, 181), (0, 2560))": "bambou_hercules_0001_vol/bambou_hercules_0001_vol_00150.hdf5"
    },
}


# here we only compare keys because values have been cast (list to numpy array...) but this shouldn't prevent from creating the nabu config file
def compare_keys(dict_1: dict, dict_2: dict):
    """
    compare two nested dictionaries.
    Only keys are checked.
    Because we want to make sure the structure of the dict are equivalent. Some values might have been casted (from numpy.array to list for example)
    """
    all_keys = set(dict_1.keys()) | set(dict_2.keys())
    for key in all_keys:
        assert key in dict_1
        assert key in dict_2
        if isinstance(dict_1[key], dict):
            assert isinstance(
                dict_2[key], dict
            ), f"fail for key ({key}), values are {type(dict_1[key]), {type(dict_2[key])}}"
            compare_keys(dict_1[key], dict_2[key])


def test_nabu_and_drac_compatibility():
    """
    test that the nabu metadata can be publish to drac/icat and retrieve from drac/icat to nabu config (for remote processing)
    """

    flatten_dict = flatten_vol_metadata(_NABU_VOL_RAW_METADATA)
    drac_dict = map_nabu_keys_to_drac(flatten_dict=flatten_dict)

    # make sure the flatten dict is serializable
    json.dumps(drac_dict)

    assert drac_dict == {
        "TOMOReconstructionPhase_ctf_advanced_params": "length_scale=1e-05; "
        "lim1=1e-05; lim2=0.2; "
        "normalize_by_mean=True",
        "TOMOReconstructionPhase_ctf_geometry": "z1_v=None; z1_h=None; "
        "detec_pixel_size=None; "
        "magnification=True",
        "TOMOReconstructionPhase_delta_beta": 100.0,
        "TOMOReconstructionPhase_detector_sample_distance": 2100.0,
        "TOMOReconstructionPhase_method": "paganin",
        "TOMOReconstructionPhase_padding_type": "edge",
        "TOMOReconstructionPhase_unsharp_coeff": 0.0,
        "TOMOReconstructionPhase_unsharp_method": "gaussian",
        "TOMOReconstructionPhase_unsharp_sigma": 0.0,
        "TOMOReconstruction_angle_offset": 0.0,
        "TOMOReconstruction_angles_file": "None",
        "TOMOReconstruction_axis_correction_file": "None",
        "TOMOReconstruction_centered_axis": True,
        "TOMOReconstruction_clip_outer_circle": True,
        "TOMOReconstruction_cor_options": "side='from_file'",
        "TOMOReconstruction_enable_halftomo": True,
        "TOMOReconstruction_end_x": -1,
        "TOMOReconstruction_end_y": -1,
        "TOMOReconstruction_end_z": 180,
        "TOMOReconstruction_fbp_filter_cutoff": 1.0,
        "TOMOReconstruction_fbp_filter_type": "ramlak",
        "TOMOReconstruction_method": "FBP",
        "TOMOReconstruction_optim_algorithm": "chambolle-pock",
        "TOMOReconstruction_padding_type": "edge",
        "TOMOReconstruction_preconditioning_filter": True,
        "TOMOReconstruction_rotation_axis_position": 2060.0,
        "TOMOReconstruction_start_x": 0,
        "TOMOReconstruction_start_y": 0,
        "TOMOReconstruction_start_z": 150,
        "TOMOReconstruction_translation_movements_file": "None",
        "TOMOReconstruction_weight_tv": 0.01,
        "endTime": "2024-10-02T17:42:01",
        "TOMOReconstruction_voxel_size_x": (1.25e-05 * _ureg.centimeter)
        .to(_ureg.micrometer)
        .magnitude,
        "TOMOReconstruction_voxel_size_y": (2.25e-05 * _ureg.centimeter)
        .to(_ureg.micrometer)
        .magnitude,
        "TOMOReconstruction_voxel_size_z": (3.25e-05 * _ureg.centimeter)
        .to(_ureg.micrometer)
        .magnitude,
    }
