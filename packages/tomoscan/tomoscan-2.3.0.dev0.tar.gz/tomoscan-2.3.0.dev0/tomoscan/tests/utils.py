#!/usr/bin/python
# coding: utf-8
#
#    Project: Azimuthal integration
#             https://github.com/pyFAI/pyFAI
#
#    Copyright (C) 2015-2022 European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


__doc__ = """test modules for pyFAI."""
__authors__ = ["Jérôme Kieffer", "Valentin Valls", "Henri Payno"]
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "07/02/2017"

import logging
import os
import shutil
import tempfile

from tomoscan.esrf.scan.mock import MockNXtomo

try:
    from contextlib import AbstractContextManager
except ImportError:
    from tomwer.third_party.contextlib import AbstractContextManager

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class MockContext(AbstractContextManager):
    def __init__(self, output_folder):
        self._output_folder = output_folder
        if self._output_folder is None:
            tempfile.mkdtemp()
            self._output_folder_existed = False
        elif not os.path.exists(self._output_folder):
            os.makedirs(self._output_folder)
            self._output_folder_existed = False
        else:
            self._output_folder_existed = True
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        mock_class = kwargs.get("mock_class", None)
        if mock_class is None:
            raise KeyError("mock_class should be provided to the " "metaclass")
        cls._mock_class = mock_class

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._output_folder_existed:
            shutil.rmtree(self._output_folder)


class NXtomoMockContext(MockContext, mock_class=MockNXtomo):
    """
    Util class to provide a context with a new Mock HDF5 file
    """

    def __init__(self, scan_path, n_proj, **kwargs):
        super().__init__(output_folder=os.path.dirname(scan_path))
        self._n_proj = n_proj
        self._mocks_params = kwargs
        self._scan_path = scan_path

    def __enter__(self):
        return MockNXtomo(
            scan_path=self._scan_path, n_proj=self._n_proj, **self._mocks_params
        ).scan
