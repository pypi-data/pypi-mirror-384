from posixpath import join
from .h5utils import get_first_hdf5_entry, get_h5_value as _get_h5_value


def get_h5_value(fname, h5_path, default_ret=None):
    val = _get_h5_value(fname, h5_path, default_ret=default_ret)
    if isinstance(val, bytes):
        val = val.decode()
    return val


def get_title(fname, entry):
    title = get_h5_value(fname, join(entry, "title"))
    if isinstance(title, bytes):
        title = title.decode()
    return title


class ScanTypeBase:
    """
    Type scan base
    """

    default_detector_name = "pilatus"
    required_fields = []
    optional_fields = []

    def __init__(self, fname, entry=None, detector_name=None):
        self.fname = fname
        self.detector_name = detector_name or self.default_detector_name
        self.entry = entry or get_first_hdf5_entry(fname)
        self.title = get_title(self.fname, self.entry)

    def get_motors(self):
        raise NotImplementedError("Base class")

    def _handle_field_not_found(self, field, on_error):
        msg = "Cannot find field %s in entry %s of file %s" % (
            field,
            self.entry,
            self.fname,
        )
        if on_error == "raise":
            raise ValueError(msg)
        elif on_error == "print":
            print(msg)
        # else: pass

    def _format_variable_field(self, field):
        if "{" not in field:
            return field
        if "{motor}" in field:
            motors = self.get_motors()
            field_formatted = field.format(motor=motors)
        elif "{detector}" in field:
            field_formatted = field.format(detector=self.detector_name)
        else:
            raise ValueError("Unsupported variable: %s" % field)
        return field_formatted

    def get_metadata(self, on_error="raise"):
        """
        Check that all the metadata necessary to carry on XRD tomography reconstruction is present.
        Return a dictionary with the associated metadata.
        """

        def _add_field(field, metadata, on_error):
            field = self._format_variable_field(field)
            field_path = join(self.entry, field)
            val = get_h5_value(self.fname, field_path)
            if val is None:
                self._handle_field_not_found(field, on_error)
            metadata[field] = val

        metadata = {}
        for field in self.required_fields:
            _add_field(field, metadata, on_error)
        for field in self.optional_fields:
            _add_field(field, metadata, "ignore")
        return metadata


class LimaTake(ScanTypeBase):
    required_fields = [
        "start_time",
        "end_time",
        "title",
        "instrument/{detector}/acq_parameters/acq_expo_time",
    ]
    optional_fields = []


class LoopScan(ScanTypeBase):
    required_fields = LimaTake.required_fields + [
        "measurement/fpico2",
        "measurement/fpico3",
        "measurement/epoch",
        "measurement/elapsed_time",
    ]
    optional_fields = [
        "measurement/{detector}_roi1" + x for x in ["", "_avg", "_max", "_min", "_std"]
    ]


FtimeScan = LoopScan


class FScan(ScanTypeBase):
    required_fields = LimaTake.required_fields + [
        "measurement/fpico2",
        "measurement/fpico3",
        "measurement/epoch_trig",
        "measurement/{motor}",  # motor name in title, more than one in case of fscan2d
    ]
    optional_fields = LoopScan.optional_fields

    def get_motors(self):
        fscan_info = self.title.split()
        if fscan_info[0].lower() != "fscan":
            raise ValueError(
                "Not a fscan: %s in file %s entry %s"
                % (self.title, self.fname, self.entry)
            )
        return fscan_info[1]  # list to be consistent with FScan2D ?


class FScan2D(ScanTypeBase):
    required_fields = FScan.required_fields
    optional_fields = FScan.optional_fields

    def get_motors(self):
        fscan_info = self.title.split()
        if fscan_info[0].lower() != "fscan2d":
            raise ValueError(
                "Not a fscan2d: %s in file %s entry %s"
                % (self.title, self.fname, self.entry)
            )
        # This is still too brittle.
        # ID11 FSCAN2D entries are in the form "fscan2d dty -300 1 1 rot -90 0.05 3620 0.002 0.00200017"
        ret = fscan_info[1:2]
        if isinstance(ret, list):
            ret = ret[0]
        return ret


class AeroystepScan(ScanTypeBase):
    required_fields = LimaTake.required_fields + [
        "measurement/fpico2",
        "measurement/fpico3",
        "measurement/epoch_trig",
        "measurement/hrrz",
        "measurement/hry",
        "instrument/positioners/hrz",
    ]
    optional_fields = LoopScan.optional_fields


scan_classes = {
    "limatake": LimaTake,
    "loopscan": LoopScan,
    "ftimescan": FtimeScan,
    "fscan": FScan,
    "fscan2d": FScan2D,
    "aeroystepscan": AeroystepScan,
}


# class factory
def Scan(fname, entry=None, detector_name=None, raise_error_if_not_supported=True):
    entry = entry or get_first_hdf5_entry(fname)
    title = get_title(fname, entry)
    title = title.split(" ")[0]  # handle stuff like "loopscan 1 1"
    scan_cls = scan_classes.get(title, None)
    if scan_cls is None:
        if raise_error_if_not_supported:
            raise ValueError(
                "Unsupported scan type '%s' - supported are %s"
                % (title, str(list(scan_classes.keys())))
            )
        return None
    return scan_cls(fname, entry=entry, detector_name=detector_name)


def get_scan_metadata(fname, entry=None, detector_name=None, on_error="raise"):
    scan = Scan(
        fname,
        entry=entry,
        detector_name=detector_name,
        raise_error_if_not_supported=False,
    )
    if scan is None:
        return None
    return scan.get_metadata(on_error=on_error)
