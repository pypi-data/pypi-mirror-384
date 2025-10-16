from __future__ import annotations
import logging
import os
import shutil
from urllib.request import ProxyHandler, build_opener, urlopen

try:
    import gitlab
except ImportError:
    __has_gitlab__ = False
else:
    __has_gitlab__ = True


_logger = logging.getLogger(__name__)


def wget_file(url, output, timeout=1000):
    """
    straight wget on a file - required for LFS files
    """
    _logger.info(f"Trying to download scan {url}, timeout set to {timeout}s")
    dictProxies = {}
    if "http_proxy" in os.environ:
        dictProxies["http"] = os.environ["http_proxy"]
        dictProxies["https"] = os.environ["http_proxy"]
    if "https_proxy" in os.environ:
        dictProxies["https"] = os.environ["https_proxy"]
    if dictProxies:
        proxy_handler = ProxyHandler(dictProxies)
        opener = build_opener(proxy_handler).open
    else:
        opener = urlopen
    _logger.info(f"wget {url}")
    data = opener(url, data=None, timeout=timeout).read()
    _logger.info(f"{url} successfully downloaded.")

    try:
        with open(output, "wb") as outfile:
            outfile.write(data)
    except IOError as e:
        raise IOError(
            f"unable to write downloaded data to disk at {output}. Error is {e}"
        )


class GitlabProject:
    """
    simple manager to download a file or a folder from a gitlab project.
    If the project is not public then a token must be provided.

    All downloaded files will be stored in __cache__ folder.
    If the file is already in the __cache__ then it will be picked drectly from there.
    """

    def __init__(
        self, host, project_id, cache_dir, token=None, branch_name="main"
    ) -> None:
        self._host = host
        self._project_id = project_id
        self._token = token
        self._branch_name = branch_name
        self._cache_dir = cache_dir
        self._project = None
        self._lfs_file_extension = None

    @property
    def project(self):
        if self._project is None:
            self._check_has_gitlab()
            gl = gitlab.Gitlab(self.host, private_token=self.token)
            self._project = gl.projects.get(self.project_id)
        return self._project

    @property
    def host(self) -> str:
        return self._host

    @property
    def project_id(self) -> int:
        return self._project_id

    @property
    def token(self):
        return self._token

    @property
    def branch_name(self) -> str:
        return self._branch_name

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    def clear_cache(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def _check_has_gitlab(self):
        if not __has_gitlab__:
            raise ImportError(
                "gitlab not install. Did you install the 'test' extra requirements ? (pip install tomoscan[test])"
            )

    def is_file(self, file_path):
        self._check_has_gitlab()
        try:
            self.project.files.raw(file_path, ref=self.branch_name, iterator=True)
        except gitlab.GitlabError:
            # case File not found
            return False
        else:
            return True

    @staticmethod
    def parse_lfs_extensions(attributes: str):
        """parse content of .gitattributes to retrieve files using lfs extension"""
        lfs_extensions = []
        for line in attributes.splitlines():
            if "filter=lfs" in line:
                extension = line.split(" ")[0]
                assert extension.startswith("*.")
                lfs_extensions.append(extension[1:])
        return lfs_extensions

    def get_lfs_extensions(self) -> tuple:
        """
        return file extension using LFS
        """
        if self._lfs_file_extension is None:
            self._check_has_gitlab()
            try:
                gitattributes = self.project.files.raw(
                    file_path=".gitattributes", ref=self.branch_name, streaming=True
                )
            except gitlab.GitlabError:
                # if file doesn't exists
                self._lfs_file_extension = tuple()
            else:
                self._lfs_file_extension = self.parse_lfs_extensions(
                    gitattributes.decode()
                )
        return self._lfs_file_extension

    def get_dataset(self, name) -> str | None:
        """
        download dataset. Name is the path to the dataset.
        for now user must notify if the dataset is a folder or not
        I guess we can get this information from gitlab and the REST API
        but to be done latter as an improvement
        """
        file_archive_location = os.path.join(self.cache_dir, name)
        is_folder = not self.is_file(name)

        if is_folder:
            try:
                self.download_folder(
                    folder=name,
                    output=self.cache_dir,
                    overwrite=False,
                )
            except Exception as e:
                _logger.error(str(e))
                return None
            else:
                return file_archive_location
        elif os.path.exists(file_archive_location):
            # if exists, avoid redownloading it
            return file_archive_location
        else:
            try:
                self.download_file(
                    file_path=name,
                    output=file_archive_location,
                )
            except Exception as e:
                _logger.error(str(e))
                return None
            else:
                return file_archive_location

    def download_file(
        self,
        file_path: str,
        output: str,
    ):
        """
        if the download / REST API fails the backup is to do a git clone of the project
        with the requested branch under nxtomomill/test/utils/__archive__
        """
        # if needed create output folder
        os.makedirs(os.path.dirname(output), exist_ok=True)
        # get information if LFS is used or not
        _, file_extension = os.path.splitext(file_path)
        use_lfs = file_extension in self.get_lfs_extensions()

        if use_lfs:
            # don't know why but for now the REST API does not return the information about the file.
            # so go trhough get for now...
            project_web_url = self.project.web_url
            wget_file(
                url=f"{project_web_url}/-/raw/{self.branch_name}/{file_path}?ref_type=heads",
                output=output,
            )
        else:
            # save the file
            with open(output, "wb") as f:
                self.project.files.raw(
                    file_path=file_path,
                    ref=self.branch_name,
                    streamed=True,
                    action=f.write,
                )
        return output

    def download_folder(
        self,
        folder: str,
        output: str,
        overwrite: bool = True,
    ):
        """

        :param overwrite: if the file already exists overwrite it
            if the download / REST API fails the backup is to do a git clone of the project
            with the requested branch under nxtomomill/test/utils/__archive__

        """
        tree = self.project.repository_tree(
            path=folder,
            ref=self.branch_name,
            get_all=True,  # if false not all items will be return
        )
        for item in tree:
            if item.get("type") == "tree":
                # if this is a folder
                self.download_folder(
                    folder=item.get("path"),
                    output=output,
                    overwrite=overwrite,
                )
            elif not overwrite and os.path.exists(
                os.path.join(output, item.get("path"))
            ):
                continue
            else:
                self.download_file(
                    file_path=item.get("path"),
                    output=os.path.join(output, item.get("path")),
                )


GitlabDataset = GitlabProject(
    branch_name="tomoscan",
    host="https://gitlab.esrf.fr",
    cache_dir=os.path.join(
        os.path.dirname(__file__),
        "__archive__",
    ),
    token=None,
    project_id=4299,  # https://gitlab.esrf.fr/tomotools/ci_datasets
)
