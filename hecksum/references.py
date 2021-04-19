import re
from typing import cast, Optional

from pydantic import BaseModel, constr, HttpUrl

from hecksum.functions import get_raised
from settings import IGNORED_EXCEPTIONS


class BaseReference(BaseModel):
    algorithm: str
    checksum_url: Optional[HttpUrl] = None
    download_url: Optional[HttpUrl] = None
    checksum: Optional[constr(strip_whitespace=True)] = None


class Reference(BaseReference):
    class Config:
        validate_assignment = True

    def populated(self) -> bool:
        return all(self.dict().values())


class ReferenceFactory(BaseReference):
    class Config:
        allow_mutation = False

    def make(self) -> Reference:
        ref = Reference(**self.dict())
        try:
            self._populate(ref)
        except IGNORED_EXCEPTIONS:
            pass
        return ref

    def _populate(self, ref: Reference) -> None:
        ref.checksum = get_raised(ref.checksum_url).text


class CodecovBashUploader(ReferenceFactory):
    algorithm = 'sha512'
    download_url: HttpUrl = 'https://codecov.io/bash'

    def _populate(self, ref: Reference) -> None:
        script = get_raised(ref.download_url).text
        version = re.search(r'VERSION="(.*)"', script).group(1)
        ref.checksum_url = f'https://raw.githubusercontent.com/codecov/codecov-bash/{version}/SHA512SUM'
        checksum = get_raised(ref.checksum_url).text
        ref.checksum = re.search(r'(.*) {2}codecov', checksum).group(1)


class Transmission(ReferenceFactory):
    algorithm = 'sha256'
    checksum_url: HttpUrl = 'https://transmissionbt.com/includes/js/constants.js'
    file_name_template: str
    sha_key: str
    version_key: str

    def _populate(self, ref: Reference) -> None:
        constants = get_raised(ref.checksum_url).text
        ref.checksum = re.search(f'{self.sha_key}: "(.*)"', constants).group(1)
        version = re.search(f'{self.version_key}: "(.*)"', constants).group(1)
        file_name = self.file_name_template.format(version=version)
        ref.download_url = f'https://github.com/transmission/transmission-releases/raw/master/{file_name}'


codecov_bash_uploader = CodecovBashUploader()
test_failure = ReferenceFactory(
    download_url=cast(HttpUrl, 'https://hecksum.com/failure.txt'),
    checksum_url=cast(HttpUrl, 'https://hecksum.com/failureSHA512.txt'),
    algorithm='sha512'
)
transmission_mac = Transmission(
    file_name_template='Transmission-{version}.dmg',
    sha_key='sha256_dmg',
    version_key='current_version_dmg'
)
transmission_win_32 = Transmission(
    file_name_template='transmission-{version}-x86.msi',
    sha_key='sha256_msi32',
    version_key='current_version_msi',
)
transmission_win_64 = Transmission(
    file_name_template='transmission-{version}-x64.msi',
    sha_key='sha256_msi64',
    version_key='current_version_msi',
)
transmission_linux = Transmission(
    file_name_template='transmission-{version}.tar.xz',
    sha_key='sha256_tar',
    version_key='current_version_tar',
)
