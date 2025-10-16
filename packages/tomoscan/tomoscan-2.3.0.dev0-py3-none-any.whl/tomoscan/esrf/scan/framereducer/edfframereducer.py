# coding: utf-8

from __future__ import annotations

import logging
import os
import re
from glob import glob

import fabio
import numpy
from lxml import etree

from tomoscan.framereducer.target import REDUCER_TARGET
from tomoscan.framereducer.framereducerbase import FrameReducerBase
from tomoscan.framereducer.method import ReduceMethod
from tomoscan.scanbase import ReducedFramesInfos, TomoScanBase
from tomoscan.esrf.scan.utils import get_parameters_frm_par_or_info

_logger = logging.getLogger(__name__)


__all__ = [
    "EDFFrameReducer",
]


class EDFFrameReducer(FrameReducerBase):
    RAW_FLAT_RE = "ref*.*[0-9]{3,4}_[0-9]{3,4}"
    """regular expression to discover flat files"""

    RAW_DARK_RE = "darkend[0-9]{3,4}"
    """regular expression to discover raw dark files"""

    REFHST_PREFIX = "refHST"

    DARKHST_PREFIX = "dark.edf"

    def __init__(
        self,
        scan: TomoScanBase,
        reduced_method: ReduceMethod,
        target: REDUCER_TARGET,
        output_dtype: numpy.dtype | None,
        input_flat_pattern=RAW_FLAT_RE,
        input_dark_pattern=RAW_DARK_RE,
        flat_output_prefix=REFHST_PREFIX,
        dark_output_prefix=DARKHST_PREFIX,
        overwrite=False,
        file_ext=".edf",
    ):
        super().__init__(
            scan, reduced_method, target, overwrite=overwrite, output_dtype=output_dtype
        )
        self._input_flat_pattern = input_flat_pattern
        self._input_dark_pattern = input_dark_pattern
        self._dark_output_prefix = dark_output_prefix
        self._flat_output_prefix = flat_output_prefix
        self._file_ext = file_ext

    @property
    def input_flat_pattern(self):
        return self._input_flat_pattern

    @property
    def input_dark_pattern(self):
        return self._input_dark_pattern

    @staticmethod
    def _getInformation(scan, refFile, information, _type, aliases=None):
        """
        Parse files contained in the given directory to get the requested
        information

        :param scan: directory containing the acquisition. Must be an absolute path
        :param refFile: the refXXXX_YYYY which should contain information about the
                        scan.
        :return: the requested information or None if not found
        """

        def parseRefFile(filePath):
            header = fabio.open(filePath).header
            for k in aliases:
                if k in header:
                    return _type(header[k])
            return None

        def parseXMLFile(filePath):
            try:
                for alias in info_aliases:
                    tree = etree.parse(filePath)
                    elmt = tree.find("acquisition/" + alias)
                    if elmt is None:
                        continue
                    else:
                        info = _type(elmt.text)
                        if info == -1:
                            return None
                        else:
                            return info
            except etree.XMLSyntaxError as e:
                _logger.warning(e)
                return None

        def parseInfoFile(filePath):
            metadata = get_parameters_frm_par_or_info(filePath)
            # convert metadata to lower case
            for alias in info_aliases:
                if alias in metadata:
                    return _type(metadata[alias])
            return None

        info_aliases = [information.lower()]
        if aliases is not None:
            assert type(aliases) in (tuple, list)
            [info_aliases.append(alias.lower()) for alias in aliases]

        if not os.path.isdir(scan):
            return None

        if refFile is not None and os.path.isfile(refFile):
            try:
                info = parseRefFile(refFile)
            except IOError as e:
                _logger.warning(e)
            else:
                if info is not None:
                    return info

        baseName = os.path.basename(scan)
        infoFiles = [os.path.join(scan, baseName + ".info")]
        infoOnDataVisitor = infoFiles[0].replace("lbsram", "", 1)
        # hack to check in lbsram, would need to be removed to add some consistency
        if os.path.isfile(infoOnDataVisitor):
            infoFiles.append(infoOnDataVisitor)
        for infoFile in infoFiles:
            if os.path.isfile(infoFile) is True:
                info = parseInfoFile(infoFile)
                if info is not None:
                    return info

        xmlFiles = [os.path.join(scan, baseName + ".xml")]
        xmlOnDataVisitor = xmlFiles[0].replace("lbsram", "", 1)
        # hack to check in lbsram, would need to be removed to add some consistency
        if os.path.isfile(xmlOnDataVisitor):
            xmlFiles.append(xmlOnDataVisitor)
        for xmlFile in xmlFiles:
            if os.path.isfile(xmlFile) is True:
                info = parseXMLFile(xmlFile)
                if info is not None:
                    return info

        return None

    @staticmethod
    def getDARK_N(scan):
        return EDFFrameReducer._getInformation(
            os.path.abspath(scan),
            refFile=None,
            information="DARK_N",
            _type=int,
            aliases=["dark_N"],
        )

    @staticmethod
    def getTomo_N(scan):
        return EDFFrameReducer._getInformation(
            os.path.abspath(scan),
            refFile=None,
            information="TOMO_N",
            _type=int,
            aliases=["tomo_N"],
        )

    @staticmethod
    def get_closest_SR_current(scan_dir, refFile=None):
        """
        Parse files contained in the given directory to get information about the
        incoming energy for the serie `iSerie`

        :param scan_dir: directory containing the acquisition
        :param refFile: the refXXXX_YYYY which should contain information about the
                        energy.
        :return: the energy in keV or none if no energy found
        """
        return EDFFrameReducer._getInformation(
            os.path.abspath(scan_dir),
            refFile,
            information="SrCurrent",
            aliases=["SRCUR", "machineCurrentStart"],
            _type=float,
        )

    @staticmethod
    def get_closest_count_time(scan_dir, refFile=None):
        return EDFFrameReducer._getInformation(
            os.path.abspath(scan_dir),
            refFile,
            information="Count_time",
            aliases=tuple(),
            _type=float,
        )

    def get_info(self, keyword: str):
        with open(self.infofile) as file:
            infod = file.readlines()
            for line in infod:
                if keyword in line:
                    return int(line.split("=")[1])
        # not found:
        return 0

    def run(self) -> dict:
        self._raw_darks = []
        self._raw_flats = []
        infos = ReducedFramesInfos()
        directory = self.scan.path
        res = {}
        if not self.preprocess():
            _logger.warning(f"preprocessing of {self.scan} failed")
        else:
            _logger.info(f"start proccess darks and flat fields for {self.scan}")
            if self.reduced_method is ReduceMethod.NONE:
                return None
            shape = fabio.open(self.filelist_fullname[0]).shape
            for i in range(len(self.serievec)):
                largeMat = numpy.zeros(
                    (self.nframes * self.nFilePerSerie, shape[0], shape[1])
                )

                if (
                    self.reducer_target is REDUCER_TARGET.DARKS
                    and len(self.serievec) == 1
                ):
                    fileName = self.out_prefix
                    if fileName.endswith(self._file_ext) is False:
                        fileName = fileName + self._file_ext
                else:
                    fileName = (
                        self.out_prefix.rstrip(self._file_ext)
                        + self.serievec[i]
                        + self._file_ext
                    )
                fileName = os.path.join(directory, fileName)
                if os.path.isfile(fileName):
                    if self.overwrite is False:
                        _logger.info(f"skip creation of {fileName}, already existing")
                        continue

                if self.nFilePerSerie == 1:
                    fSerieName = os.path.join(directory, self.series[i])
                    header = {"method": f"{self.reduced_method.name} on 1 image"}
                    header["SRCUR"] = self.get_closest_SR_current(
                        scan_dir=directory, refFile=fSerieName
                    )
                    header["Count_time"] = self.get_closest_count_time(
                        scan_dir=directory,
                        refFile=fSerieName,
                    )

                    if self.nframes == 1:
                        largeMat[0] = fabio.open(fSerieName).data
                    else:
                        handler = fabio.open(fSerieName)
                        dShape = (self.nframes, handler.dim2, handler.dim1)
                        largeMat = numpy.zeros(dShape)
                        for iFrame in range(self.nframes):
                            largeMat[iFrame] = handler.getframe(iFrame).data
                else:
                    header = {
                        "method": self.reduced_method.name
                        + " on %d images" % self.nFilePerSerie
                    }
                    header["SRCUR"] = self.get_closest_SR_current(
                        scan_dir=directory, refFile=self.series[i][0]
                    )
                    header["Count_time"] = self.get_closest_count_time(
                        scan_dir=directory,
                        refFile=self.series[i][0],
                    )
                    for j, fName in zip(
                        range(self.nFilePerSerie), self.filesPerSerie[self.serievec[i]]
                    ):
                        file_BigMat = fabio.open(fName)
                        if self.nframes > 1:
                            for fr in range(self.nframes):
                                jfr = fr + j * self.nframes
                                largeMat[jfr] = file_BigMat.getframe(fr).getData()
                        else:
                            largeMat[j] = file_BigMat.data

                # update electrical machine current
                if header["SRCUR"] is not None:
                    if infos.machine_current is None:
                        infos.machine_current = []
                    infos.machine_current.append(header["SRCUR"])
                if header["Count_time"] is not None:
                    if infos.count_time is None:
                        infos.count_time = []
                    infos.count_time.append(header["Count_time"])

                if self.reduced_method is ReduceMethod.MEDIAN:
                    data = numpy.median(largeMat, axis=0)
                elif self.reduced_method is ReduceMethod.MEAN:
                    data = numpy.mean(largeMat, axis=0)
                elif self.reduced_method is ReduceMethod.FIRST:
                    data = largeMat[0]
                elif self.reduced_method is ReduceMethod.LAST:
                    data = largeMat[-1]
                elif self.reduced_method is ReduceMethod.NONE:
                    return
                else:
                    raise ValueError(
                        f"Unrecognized calculation type request {self.reduced_method}"
                    )

                if (
                    self.reducer_target is REDUCER_TARGET.DARKS and self.nacq > 1
                ):  # and self.nframes == 1:
                    nacq = self.getDARK_N(directory) or 1
                    data = data / nacq
                if self.output_dtype is not None:
                    data = data.astype(self.output_dtype)
                file_desc = fabio.edfimage.EdfImage(data=data, header=header)
                res[int(self.serievec[i])] = data
                i += 1
                file_desc.write(fileName)
            _logger.info("end proccess darks and flat fields")
        return res, infos

    def preprocess(self):
        # start setup function
        if self.reduced_method is ReduceMethod.NONE:
            return False
        if self.reducer_target is REDUCER_TARGET.DARKS:
            self.out_prefix = self._dark_output_prefix
            self.info_nacq = "DARK_N"
        else:
            self.out_prefix = self._flat_output_prefix
            self.info_nacq = "REF_N"

        # init
        self.nacq = 0
        """Number of acquisition runned"""
        self.files = 0
        """Ref or dark files"""
        self.nframes = 1
        """Number of frame per ref/dark file"""
        self.serievec = ["0000"]
        """List of series discover"""
        self.filesPerSerie = {}
        """Dict with key the serie id and values list of files to compute
        for median or mean"""
        self.infofile = ""
        """info file of the acquisition"""

        # sample/prefix and info file
        directory = self.scan.path
        self.prefix = os.path.basename(directory)
        extensionToTry = (".info", "0000.info")
        for extension in extensionToTry:
            infoFile = os.path.join(directory, self.prefix + extension)
            if os.path.exists(infoFile):
                self.infofile = infoFile
                break

        if self.infofile == "":
            _logger.debug(f"fail to found .info file for {self.scan}")

        """
        Set filelist
        """
        # do the job only if not already done and overwrite not asked
        self.out_files = sorted(glob(directory + os.sep + "*." + self._file_ext))

        self.filelist_fullname = self.get_originals()
        self.fileNameList = []
        [
            self.fileNameList.append(os.path.basename(_file))
            for _file in self.filelist_fullname
        ]
        self.fileNameList = sorted(self.fileNameList)
        self.nfiles = len(self.filelist_fullname)
        # if nothing to process
        if self.nfiles == 0:
            _logger.info(
                f"no {self.reducer_target} for {directory}, because no file to compute found"
            )
            return False

        self.fid = fabio.open(self.filelist_fullname[0])
        self.nframes = self.fid.nframes
        self.nacq = 0
        # get the info of number of acquisitions
        if self.infofile != "":
            self.nacq = self.get_info(self.info_nacq)

        if self.nacq == 0:
            self.nacq = self.nfiles

        self.nseries = 1
        if self.nacq > self.nfiles:
            # get ready for accumulation and/or file multiimage?
            self.nseries = self.nfiles
        if (
            self.nacq < self.nfiles
            and self.get_n_digits(self.fileNameList[0], directory=directory) < 2
        ):
            self.nFilePerSerie = self.nseries
            self.serievec, self.filesPerSerie = self.preprocess_PCOTomo()
        else:
            self.series = self.fileNameList
            self.serievec = self.get_series_value(self.fileNameList, self._file_ext)
            self.filesPerSerie, self.nFilePerSerie = self.group_files_per_serie(
                self.filelist_fullname, self.serievec
            )

        if self.filesPerSerie is not None:
            for serie in self.filesPerSerie:
                for _file in self.filesPerSerie[serie]:
                    if self.reducer_target is REDUCER_TARGET.DARKS:
                        self._raw_darks.append(os.path.join(self.scan.path, _file))
                    if self.reducer_target is REDUCER_TARGET.FLATS:
                        self._raw_flats.append(os.path.join(self.scan.path, _file))

        return self.serievec is not None and self.filesPerSerie is not None

    @staticmethod
    def get_series_value(fileNames, file_ext):
        assert len(fileNames) > 0
        is_there_digits = len(re.findall(r"\d+", fileNames[0])) > 0
        series = set()
        i = 0
        for fileName in fileNames:
            if is_there_digits:
                name = fileName.rstrip(file_ext)
                file_index = name.split("_")[-1]
                rm_not_numeric = re.compile(r"[^\d.]+")
                file_index = rm_not_numeric.sub("", file_index)
                series.add(file_index)
            else:
                series.add("%04d" % i)
                i += 1
        return list(series)

    @staticmethod
    def group_files_per_serie(files, series):
        def findFileEndingWithSerie(poolFiles, serie):
            res = []
            for _file in poolFiles:
                _f = _file.rstrip(".edf")
                if _f.endswith(serie):
                    res.append(_file)
            return res

        def checkSeriesFilesLength(serieFiles):
            length = -1
            for serie in serieFiles:
                if length == -1:
                    length = len(serieFiles[serie])
                elif len(serieFiles[serie]) != length:
                    _logger.error("Series with inconsistant number of ref files")

        assert len(series) > 0
        if len(series) == 1:
            return {series[0]: files}, len(files)
        assert len(files) > 0

        serieFiles = {}
        unattributedFiles = files.copy()
        for serie in series:
            serieFiles[serie] = findFileEndingWithSerie(unattributedFiles, serie)
            [unattributedFiles.remove(_f) for _f in serieFiles[serie]]

        if len(unattributedFiles) > 0:
            _logger.error(f"Failed to associate {unattributedFiles} to any serie")
            return {}, 0

        checkSeriesFilesLength(serieFiles)

        return serieFiles, len(serieFiles[list(serieFiles.keys())[0]])

    @staticmethod
    def get_n_digits(_file, directory):
        file_without_scanID = _file.replace(os.path.basename(directory), "", 1)
        return len(re.findall(r"\d+", file_without_scanID))

    def preprocess_PCOTomo(self):
        filesPerSerie = {}
        if self.nfiles % self.nacq == 0:
            assert self.nacq < self.nfiles
            self.nseries = self.nfiles // self.nacq
            self.series = self.fileNameList
        else:
            _logger.warning("Fail to deduce series")
            return None, None

        linear = (
            self.get_n_digits(self.fileNameList[0], directory=self.scan.scan_path) < 2
        )
        if linear is False:
            # which digit pattern contains the file number?
            lastone = True
            penulti = True
            for first_files in range(self.nseries - 1):
                digivec_1 = re.findall(r"\d+", self.fileNameList[first_files])
                digivec_2 = re.findall(r"\d+", self.fileNameList[first_files + 1])
                if lastone:
                    lastone = (int(digivec_2[-1]) - int(digivec_1[-1])) == 0
                if penulti:
                    penulti = (int(digivec_2[-2]) - int(digivec_1[-2])) == 0

            linear = not penulti

        if linear is False:
            digivec_1 = re.findall(r"\d+", self.fileNameList[self.nseries - 1])
            digivec_2 = re.findall(r"\d+", self.fileNameList[self.nseries])
            # confirm there is 1 increment after self.nseries in the uperlast last digit patern
            if (int(digivec_2[-2]) - int(digivec_1[-2])) != 1:
                linear = True

        # series are simple sublists in main filelist
        # self.series = []
        if linear is True:
            is_there_digits = len(re.findall(r"\d+", self.fileNameList[0])) > 0
            if is_there_digits:
                serievec = set([re.findall(r"\d+", self.fileNameList[0])[-1]])
            else:
                serievec = set(["0000"])
            for i in range(self.nseries):
                if is_there_digits:
                    serie = re.findall(r"\d+", self.fileNameList[i * self.nacq])[-1]
                    serievec.add(serie)
                    filesPerSerie[serie] = self.fileNameList[
                        i * self.nacq : (i + 1) * self.nacq
                    ]
                else:
                    serievec.add("%04d" % i)
            # in the sorted filelist, the serie is incremented, then the acquisition number:
        else:
            self.series = self.fileNameList[0 :: self.nseries]
            serievec = set([re.findall(r"\d+", self.fileNameList[0])[-1]])
            for serie in serievec:
                filesPerSerie[serie] = self.fileNameList[0 :: self.nseries]
        serievec = list(sorted(serievec))

        if len(serievec) > 2:
            _logger.error(
                f"DarkRefs do not deal with multiple scan. (scan {self.scan})"
            )
            return None, None
        assert len(serievec) <= 2
        if len(serievec) > 1:
            key = serievec[-1]
            tomoN = self.getTomo_N(self.scan)
            if tomoN is None:
                _logger.error("Fail to found information TOMO_N")
            del serievec[-1]
            serievec.append(str(tomoN).zfill(4))
            filesPerSerie[serievec[-1]] = filesPerSerie[key]
            del filesPerSerie[key]
            assert len(serievec) == 2
            assert len(filesPerSerie) == 2

        return serievec, filesPerSerie

    def get_originals(self) -> list:
        """compute the list of originals files to be used to compute the reducer target."""
        if self.reducer_target is REDUCER_TARGET.FLATS:
            try:
                pattern = re.compile(self.input_flat_pattern)
            except Exception:
                pattern = None
                _logger.error(
                    f"Fail to compute regular expresion for {self.input_flat_pattern}"
                )
        elif self.reducer_target is REDUCER_TARGET.DARKS:
            re.compile(self.input_dark_pattern)
            try:
                pattern = re.compile(self.input_dark_pattern)
            except Exception:
                pattern = None
                _logger.error(
                    f"Fail to compute regular expresion for {self.input_dark_pattern}"
                )
        else:
            raise ValueError(f"reducer target not handled ({self.reducer_target})")

        filelist_fullname = []
        if pattern is None:
            return filelist_fullname
        directory = self.scan.path
        for file in os.listdir(directory):
            if pattern.match(file) and file.endswith(self._file_ext):
                if (
                    file.startswith(self._flat_output_prefix)
                    or file.startswith(self._dark_output_prefix)
                ) is False:
                    filelist_fullname.append(os.path.join(directory, file))
        return sorted(filelist_fullname)

    def remove_raw_files(self):
        """Remove orignals files fitting the target (dark or flat files)"""
        if self.reducer_target is REDUCER_TARGET.DARKS:
            # In the case originals has already been found for the median
            # calculation
            if len(self._raw_darks) > 0:
                files = self._raw_darks
            else:
                files = self.get_originals()
        elif self.reducer_target is REDUCER_TARGET.FLATS:
            if len(self._raw_flats) > 0:
                files = self._raw_flats
            else:
                files = self.get_originals()
        else:
            _logger.error(
                f"the requested what (reduce {self.reducer_target}) is not recognized. "
                "Can't remove corresponding file"
            )
            return

        _files = set(files)
        for _file in _files:
            try:
                os.remove(_file)
            except Exception as e:
                _logger.error(e)
