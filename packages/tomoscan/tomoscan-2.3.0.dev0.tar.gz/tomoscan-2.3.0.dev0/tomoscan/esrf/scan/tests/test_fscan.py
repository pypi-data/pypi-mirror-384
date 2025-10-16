import pytest
from tomoscan.esrf.scan.fscan_scantypes import scan_classes
from tomoscan.tests.datasets import GitlabDataset


@pytest.fixture(scope="class")
def bootstrap_test_scantypes(request):
    cls = request.cls
    cls.scan_fname = {}
    for scan_type in ["aeroystepscan", "fscan", "limatake", "loopscan"]:
        cls.scan_fname[scan_type] = GitlabDataset.get_dataset(
            f"h5_datasets/fscan/{scan_type}.h5"
        )

    yield
    # Tear-down


@pytest.mark.usefixtures("bootstrap_test_scantypes")
class TestScanTypes:
    """
    Test scan types for the different type of 'scan' of FScan
    """

    def test_scantype(self):
        for scan_type, scan_fname in self.scan_fname.items():
            scan_cls = scan_classes[scan_type]
            scan = scan_cls(scan_fname)
            metadata = scan.get_metadata()
            expected_fields = set(scan_cls.required_fields)

            # "metadata" might have more items (see 'optional_fields').
            # The following difference is the empty set iff 'metadata' has at least the items of 'expected_fields'
            diff = expected_fields - set(metadata.keys())
            diff_without_names_templates = set(item for item in diff if "{" not in item)
            assert (
                len(diff_without_names_templates) == 0
            ), "Expected fields %s for scan type %s, but got %s" % (
                str(expected_fields),
                scan_type,
                str(set(metadata.keys())),
            )
