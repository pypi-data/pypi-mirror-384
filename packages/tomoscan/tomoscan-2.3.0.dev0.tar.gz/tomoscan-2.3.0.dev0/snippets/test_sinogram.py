import os
import time

import h5py
import numpy

from tomoscan.esrf.scan.nxtomoscan import NXtomoScan, ImageKey

proj_data = numpy.arange(1000, 1000 + 10 * 20 * 30).reshape(30, 10, 20)
proj_angle = numpy.linspace(0, 180, 30)
dark_value = 0.5
flat_value = 1
dark_data = numpy.ones((10, 20)) * dark_value
dark_angle = numpy.array(
    [
        0,
    ]
)
flat_data_1 = numpy.ones((10, 20)) * flat_value
flat_angle_1 = numpy.array(
    [
        0,
    ]
)

flat_data_2 = numpy.ones((10, 20)) * flat_value
flat_angle_2 = numpy.array(
    [
        90,
    ]
)
flat_data_3 = numpy.ones((10, 20)) * flat_value
flat_angle_3 = numpy.array(
    [
        180,
    ]
)

# data dataset
data = numpy.empty((34, 10, 20))
data[0] = dark_data
data[1] = flat_data_1
data[2:17] = proj_data[:15]
data[17] = flat_data_2
data[18:33] = proj_data[15:]
data[33] = flat_data_3


def create_arange_dataset(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

    with h5py.File(file_path, mode="a") as h5f:
        entry = h5f.require_group("entry0000")

        # rotation angle
        assert data.ndim == 3
        entry["instrument/detector/data"] = data
        rotation_angle = numpy.empty(34)
        rotation_angle[0] = dark_angle
        rotation_angle[1] = flat_angle_1
        rotation_angle[2:17] = proj_angle[:15]
        rotation_angle[17] = flat_angle_2
        rotation_angle[18:33] = proj_angle[15:]
        rotation_angle[33] = flat_angle_3

        entry["sample/rotation_angle"] = rotation_angle

        # image key / images keys
        image_keys = []
        image_keys.append(ImageKey.DARK_FIELD.value)
        image_keys.append(ImageKey.FLAT_FIELD.value)
        image_keys.extend([ImageKey.PROJECTION.value] * 15)
        image_keys.append(ImageKey.FLAT_FIELD.value)
        image_keys.extend([ImageKey.PROJECTION.value] * 15)
        image_keys.append(ImageKey.FLAT_FIELD.value)
        entry["instrument/detector/image_key"] = numpy.array(image_keys)
        entry["instrument/detector/image_key_control"] = numpy.array(image_keys)


file_path = "test.h5"
create_arange_dataset(file_path)

scan = NXtomoScan(file_path, "entry0000")
assert len(scan.projections) == 30
assert len(scan.flats) == 3
assert len(scan.darks) == 1

scan.set_reduced_darks(
    {
        0: dark_data,
    }
)

scan.set_reduced_flats(
    {
        1: flat_data_1,
        17: flat_data_2,
        33: flat_data_3,
    }
)


scan._flats_weights = scan._get_flats_weights()


t0 = time.time()
sinogram_old = scan._get_sinogram_ref_imp(line=5)
print(f"execution time of the old implementation: {time.time() - t0}")
t0 = time.time()
sinogram_new = scan.get_sinogram(line=5)
print(f"execution time of the new implementation: {time.time() - t0}")

# plot the sinogram

from silx.gui import qt
from silx.gui.plot import Plot2D

app = qt.QApplication([])

plot_old = Plot2D()
plot_old.addImage(sinogram_old)
plot_old.setWindowTitle("old sinogram")
plot_old.show()

plot_new = Plot2D()
plot_new.addImage(sinogram_new)
plot_new.setWindowTitle("new sinogram")
plot_new.show()

raw_sinogram = proj_data[:, 5, :]

plot_raw = Plot2D()
plot_raw.addImage(raw_sinogram)
plot_raw.setWindowTitle("raw sinogram")
plot_raw.show()

# TODO: get the one from tomwer to compare as well
try:
    from tomwer.core.scan.hdf5scan import NXtomoScan as TomwerNXtomoScan
except ImportError:
    pass
else:
    scan_t = TomwerNXtomoScan(file_path, "entry0000")

    scan_t.set_reduced_darks(
        {
            0: dark_data,
        }
    )

    scan_t.set_reduced_flats(
        {
            1: flat_data_1,
            17: flat_data_2,
            33: flat_data_3,
        }
    )
    sinogram_tomwer = scan_t.get_sinogram(line=5)

    plot_tomwer = Plot2D()
    plot_tomwer.addImage(sinogram_tomwer)
    plot_tomwer.setWindowTitle("tomwer sinogram")
    plot_tomwer.show()

# TODO: check all lines of the sinogram
corrected = (raw_sinogram - dark_value) / (flat_value - dark_value)
numpy.testing.assert_array_equal(corrected, sinogram_old)


app.exec_()
