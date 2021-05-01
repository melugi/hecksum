from enum import Enum
import os
from typing import ClassVar, Optional

from pydantic import BaseModel, HttpUrl
import requests

from hecksum import references as refs
from settings import IGNORED_EXCEPTIONS


class Project(BaseModel):
    name: str
    airtable_id: str
    REFERENCE_FACTORIES: ClassVar[dict[str, refs.ReferenceFactory]] = {
        'rec1stqERwHeVoyTr': refs.codecov_bash_uploader,
        'recU4m6YnYdQ4U76q': refs.test_failure,
        'recPGEEzOeJ2gNh7u': refs.transmission_mac,
        'rec6xk5CUPcjsqIyD': refs.transmission_win_32,
        'recZOMQpGtd524lsj': refs.transmission_win_64,
        'recVSRZVqVDt2SCom': refs.transmission_linux,
        'recAbyXIsNXtCTqG0': refs.doppler_linux_amd64,
        'recSYll22rCAOJxeZ': refs.doppler_linux_i386,
        'recfduW1SngHHYh5E': refs.doppler_linux_armv7,
        'rec5y2KWOIsmOzvvR': refs.doppler_openbsd_arm64,
        'rec613Kd84C8LDG5J': refs.doppler_linux_armv6,
        'recGsPwOjP0NlJuLf': refs.doppler_openbsd_armv6,
        'recrUUgD10DkaOtmx': refs.doppler_macOS_amd64,
        'recmnF2Khz6oC7V19': refs.doppler_macOS_arm64,
        'rec0u2DXEAU6YKfiH': refs.doppler_freebsd_armv7,
        'reckOzKhl10nkgSzd': refs.doppler_openbsd_amd64,
        'rec7YQ94cDVtApU5J': refs.doppler_openbsd_i386,
        'recF7Wi9E0pz4eniA': refs.doppler_linux_arm64,
        'recwhoNNXgerQa6Or': refs.doppler_openbsd_armv7,
        'recywBFflOyzTDbki': refs.doppler_freebsd_amd64,
        'rec178Xu6xwR5gyi9': refs.doppler_netbsd_amd64,
        'recsEXYvQtRrkc9ax': refs.doppler_windows_amd64,
        'recMxKQLHnRjENMmw': refs.doppler_netbsd_armv7,
        'rec4OjI4l1DLYkOXo': refs.doppler_freebsd_arm64,
        'reccc1BO9ICulnVJ6': refs.doppler_netbsd_i386,
        'recRAn5yVy1LGHZ1E': refs.doppler_netbsd_armv6,
        'recBheQ4Z6ikftKXU': refs.doppler_freebsd_armv6,
        'recj96T0Pbp5wWuRX': refs.doppler_windows_armv7,
        'recIuYEZhjk5he8Dw': refs.doppler_windows_armv6,
    }

    def check(self) -> 'Check':
        reference_factory = self.REFERENCE_FACTORIES[self.airtable_id]
        ref = reference_factory.make()
        try:
            if not ref.populated():
                raise Exception(f'Reference not populated. {ref}')
            download_checksum = ref.get_download_checksum()
        except IGNORED_EXCEPTIONS:
            status = Status.error
        else:
            status = Status.passing if ref.checksum == download_checksum else Status.failing
        return Check(
            project=self,
            status=status,
            checksum=ref.checksum,
            checksum_url=ref.checksum_url,
            download_url=ref.download_url,
        )


class Status(str, Enum):
    passing = 'Passing'
    error = 'Error'
    failing = 'Failing'


class Check(BaseModel):
    project: Project
    status: Status
    checksum: Optional[str]
    checksum_url: Optional[HttpUrl]
    download_url: Optional[HttpUrl]

    class Config:
        use_enum_values = True

    def post(self) -> requests.Response:
        headers = {'Authorization': f'Bearer {os.environ["AIRTABLE_API_KEY"]}'}
        payload = {
            'fields': {
                'Project': [self.project.airtable_id],
                'Status': self.status,
                'Checksum URL': self.checksum_url,
                'Download': self.download_url,
                'Checksum': self.checksum
            },
            'typecast': True
        }
        return requests.post('https://api.airtable.com/v0/appPt1p6IWk5Cjv2E/Checks', json=payload, headers=headers)
