from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
import os
import re

import requests


@dataclass
class Project(ABC):
    name: str
    airtable_id: str

    @abstractmethod
    def _check(self, check: Check) -> None:
        pass

    def check(self) -> Check:
        check = Check(self)
        try:
            self._check(check)
        except Exception:
            return check
        return check


@dataclass
class Check:
    project: Project
    status: str = 'Error'
    checksum: str = ''
    checksum_url: str = ''
    download: str = ''

    def post(self) -> None:
        headers = {'Authorization': f'Bearer {os.environ["AIRTABLE_API_KEY"]}'}
        payload = {
            'fields': {
                'Project': [self.project.airtable_id],
                'Status': self.status,
                'Checksum URL': self.checksum_url,
                'Download': self.download,
                'Checksum': self.checksum
            },
            'typecast': True
        }
        requests.post('https://api.airtable.com/v0/appPt1p6IWk5Cjv2E/Checks', json=payload, headers=headers)


@dataclass
class TestFailure(Project):
    def _check(self, check: Check) -> None:
        check.download = 'https://hecksum.com/failure.txt'
        check.checksum_url = 'https://hecksum.com/failureSHA512.txt'
        r = requests.get(check.download)
        r.raise_for_status()
        actual_sha = hashlib.sha512(r.content).hexdigest()
        r = requests.get(check.checksum_url)
        r.raise_for_status()
        check.checksum = r.text
        check.status = 'Passing' if actual_sha == check.checksum else 'Failing'


@dataclass
class CodecovBashUploader(Project):
    download = 'https://codecov.io/bash'

    def _check(self, check) -> None:
        check.download = self.download
        r = requests.get(self.download)
        r.raise_for_status()
        actual_sha = hashlib.sha512(r.content).hexdigest()
        version = re.search(r'VERSION="(.*)"', r.text).group(1)
        check.checksum_url = f'https://raw.githubusercontent.com/codecov/codecov-bash/{version}/SHA512SUM'
        r = requests.get(check.checksum_url)
        r.raise_for_status()
        check.checksum = r.text
        check.status = 'Passing' if f'{actual_sha}  codecov' in check.checksum else 'Failing'


@dataclass
class Transmission(Project):
    link_format: str
    sha_key: str
    version_key: str
    constants = 'https://transmissionbt.com/includes/js/constants.js'
    github = 'https://github.com/transmission/transmission-releases/raw/master/'

    def _check(self, check: Check) -> None:
        check.checksum_url = self.constants
        r = requests.get(self.constants)
        r.raise_for_status()
        check.checksum = re.search(f'{self.sha_key}: "(.*)"', r.text).group(1)
        version = re.search(f'{self.version_key}: "(.*)"', r.text).group(1)
        check.download = self.github + self.link_format.format(version)
        r = requests.get(check.download)
        r.raise_for_status()
        actual_sha = hashlib.sha256(r.content).hexdigest()
        check.status = 'Passing' if actual_sha == check.checksum else 'Failing'


def main():
    CodecovBashUploader('Codecov Bash Uploader', 'rec1stqERwHeVoyTr').check().post()
    Transmission(
        name='Transmission Mac OS X',
        airtable_id='recPGEEzOeJ2gNh7u',
        link_format='Transmission-{}.dmg',
        sha_key='sha256_dmg',
        version_key='current_version_dmg'
    ).check().post()
    Transmission(
        name='Transmission Windows x86',
        airtable_id='rec6xk5CUPcjsqIyD',
        link_format='transmission-{}-x86.msi',
        sha_key='sha256_msi32',
        version_key='current_version_msi'
    ).check().post()
    Transmission(
        name='Transmission Windows x64',
        airtable_id='recZOMQpGtd524lsj',
        link_format='transmission-{}-x64.msi',
        sha_key='sha256_msi64',
        version_key='current_version_msi'
    ).check().post()
    Transmission(
        name='Transmission Linux',
        airtable_id='recVSRZVqVDt2SCom',
        link_format='transmission-{}.tar.xz',
        sha_key='sha256_tar',
        version_key='current_version_tar'
    ).check().post()
    TestFailure('Test Failure', 'recU4m6YnYdQ4U76q').check().post()


if __name__ == '__main__':
    main()
