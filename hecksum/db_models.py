from enum import Enum
import os
from typing import ClassVar, Optional

from pydantic import BaseModel, HttpUrl
import requests

from hecksum import references as refs
from hecksum.functions import create_download_checksum
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
    }

    def check(self) -> 'Check':
        reference_factory = self.REFERENCE_FACTORIES[self.airtable_id]
        ref = reference_factory.make()
        try:
            if not ref.populated():
                raise Exception(f'Reference not populated. {ref}')
            download_checksum = create_download_checksum(ref.download_url, ref.algorithm)
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
