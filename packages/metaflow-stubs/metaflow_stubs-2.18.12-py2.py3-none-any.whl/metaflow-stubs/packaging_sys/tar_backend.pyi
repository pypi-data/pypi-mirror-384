######################################################################################################
#                                 Auto-generated Metaflow stub file                                  #
# MF version: 2.18.12                                                                                #
# Generated on 2025-10-15T20:44:18.098053                                                            #
######################################################################################################

from __future__ import annotations

import typing
import abc
import metaflow
if typing.TYPE_CHECKING:
    import tarfile
    import abc
    import metaflow.packaging_sys.backend
    import typing
    import _io

from .backend import PackagingBackend as PackagingBackend

class TarPackagingBackend(metaflow.packaging_sys.backend.PackagingBackend, metaclass=abc.ABCMeta):
    @classmethod
    def get_extract_commands(cls, archive_name: str, dest_dir: str) -> typing.List[str]:
        ...
    def __init__(self):
        ...
    def create(self):
        ...
    def add_file(self, filename: str, arcname: typing.Optional[str] = None):
        ...
    def add_data(self, data: _io.BytesIO, arcname: str):
        ...
    def close(self):
        ...
    def get_blob(self) -> typing.Union[bytes, bytearray, None]:
        ...
    @classmethod
    def cls_open(cls, content: typing.IO[bytes]) -> tarfile.TarFile:
        ...
    @classmethod
    def cls_member_name(cls, member: typing.Union[tarfile.TarInfo, str]) -> str:
        """
        Returns the name of the member as a string.
        """
        ...
    @classmethod
    def cls_has_member(cls, archive: tarfile.TarFile, name: str) -> bool:
        ...
    @classmethod
    def cls_get_member(cls, archive: tarfile.TarFile, name: str) -> typing.Optional[bytes]:
        ...
    @classmethod
    def cls_extract_members(cls, archive: tarfile.TarFile, members: typing.Optional[typing.List[typing.Any]] = None, dest_dir: str = '.'):
        ...
    @classmethod
    def cls_list_members(cls, archive: tarfile.TarFile) -> typing.Optional[typing.List[tarfile.TarInfo]]:
        ...
    @classmethod
    def cls_list_names(cls, archive: tarfile.TarFile) -> typing.Optional[typing.List[str]]:
        ...
    ...

