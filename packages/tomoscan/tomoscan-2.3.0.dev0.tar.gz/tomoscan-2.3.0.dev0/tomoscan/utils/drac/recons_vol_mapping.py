"""Defines mapping rule to be applied for reconstructed volume to drac"""

from __future__ import annotations

import pint
import numpy

_ureg = pint.get_application_registry()


class DracRawDataMapping:
    """
    Map drac/icat metadata from / to raw data. Raw data in this context is expected to be a reconstructed volume (by nabu)
    This layer ease handling of unit conversion as data type (from a single field to multi field structures.)

    A raw data / nabu field can be split into several drac/icat field. And several drac/icat field can be concatenate to a single raw_data/nabu field.
    This is the purpose of the 'raw_data_field_index', 'raw_data_field_size' and 'raw_data_type_constructor' parameters.
    The over way around is not forseen
    """

    def __init__(
        self,
        drac_key: str,
        raw_data_key: str,
        raw_data_field_index: int | None = None,
        raw_data_type_constructor=None,
        raw_data_unit: str | pint.Unit = None,
        drac_unit: str | pint.Unit = None,
    ) -> None:
        self.drac_key = drac_key
        self.raw_data_key = raw_data_key

        self.raw_data_field_index = raw_data_field_index

        self.raw_data_type_constructor = raw_data_type_constructor

        self._raw_data_unit = raw_data_unit
        self._drac_unit = drac_unit

    def to_drac(self, raw_value):
        "convert a raw_data (nabu) field to an icat field"
        if self.raw_data_field_index is not None:
            assert isinstance(self.raw_data_field_index, int)
            assert isinstance(raw_value, (list, tuple, numpy.array))
            raw_value = raw_value[self.raw_data_field_index]

        if self._raw_data_unit is not None and self._drac_unit is not None:
            return (raw_value * self._raw_data_unit).to(self._drac_unit).magnitude
        else:
            return raw_value


DRAC_NABU_MAPPING = (
    DracRawDataMapping(
        drac_key="TOMOReconstruction_angle_offset",  # float
        raw_data_key="nabu_config/reconstruction/angle_offset",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_angles_file",  # str - file path
        raw_data_key="nabu_config/reconstruction/angles_file",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_axis_correction_file",  # str - file path
        raw_data_key="nabu_config/reconstruction/axis_correction_file",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_centered_axis",  # bool
        raw_data_key="nabu_config/reconstruction/centered_axis",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_clip_outer_circle",  # bool
        raw_data_key="nabu_config/reconstruction/clip_outer_circle",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_cor_options",  # str
        raw_data_key="nabu_config/reconstruction/cor_options",
    ),
    DracRawDataMapping(
        drac_key="endTime",  # str
        raw_data_key="date",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_enable_halftomo",  # bool
        raw_data_key="nabu_config/reconstruction/enable_halftomo",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_end_x",  # int (px)
        raw_data_key="nabu_config/reconstruction/end_x",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_end_y",  # int (px)
        raw_data_key="nabu_config/reconstruction/end_y",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_end_z",  # int (px)
        raw_data_key="nabu_config/reconstruction/end_z",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_fbp_filter_cutoff",  # float
        raw_data_key="nabu_config/reconstruction/fbp_filter_cutoff",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_fbp_filter_type",  # str
        raw_data_key="nabu_config/reconstruction/fbp_filter_type",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_method",  # str
        raw_data_key="nabu_config/reconstruction/method",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_optim_algorithm",  # str
        raw_data_key="nabu_config/reconstruction/optim_algorithm",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_padding_type",  # str
        raw_data_key="nabu_config/reconstruction/padding_type",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_preconditioning_filter",  # str
        raw_data_key="nabu_config/reconstruction/preconditioning_filter",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_rotation_axis_position",  # float
        raw_data_key="nabu_config/reconstruction/rotation_axis_position",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_start_x",  # int
        raw_data_key="nabu_config/reconstruction/start_x",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_start_y",  # int
        raw_data_key="nabu_config/reconstruction/start_y",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_start_z",  # int
        raw_data_key="nabu_config/reconstruction/start_z",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_translation_movements_file",  # str
        raw_data_key="nabu_config/reconstruction/translation_movements_file",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_weight_tv",  # float
        raw_data_key="nabu_config/reconstruction/weight_tv",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_voxel_size_x",  # float
        raw_data_key="processing_options/reconstruction/voxel_size_cm",
        raw_data_field_index=0,
        raw_data_unit=_ureg.centimeter,
        drac_unit=_ureg.micrometer,
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_voxel_size_y",  # float
        raw_data_key="processing_options/reconstruction/voxel_size_cm",
        raw_data_field_index=1,
        raw_data_unit=_ureg.centimeter,
        drac_unit=_ureg.micrometer,
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstruction_voxel_size_z",  # float
        raw_data_key="processing_options/reconstruction/voxel_size_cm",
        raw_data_field_index=2,
        raw_data_unit=_ureg.centimeter,
        drac_unit=_ureg.micrometer,
    ),
    # phase
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_ctf_advanced_params",  # str
        raw_data_key="nabu_config/phase/ctf_advanced_params",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_ctf_geometry",  # str
        raw_data_key="nabu_config/phase/ctf_geometry",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_delta_beta",  # float
        raw_data_key="nabu_config/phase/delta_beta",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_detector_sample_distance",  # float
        raw_data_key="nabu_config/phase/distance_m",
        raw_data_unit=_ureg.meter,
        drac_unit=_ureg.millimeter,
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_method",  # str
        raw_data_key="nabu_config/phase/method",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_padding_type",  # ste
        raw_data_key="nabu_config/phase/padding_type",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_unsharp_coeff",  # float
        raw_data_key="nabu_config/phase/unsharp_coeff",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_unsharp_method",  # str
        raw_data_key="nabu_config/phase/unsharp_method",
    ),
    DracRawDataMapping(
        drac_key="TOMOReconstructionPhase_unsharp_sigma",  # float
        raw_data_key="nabu_config/phase/unsharp_sigma",
    ),
)
