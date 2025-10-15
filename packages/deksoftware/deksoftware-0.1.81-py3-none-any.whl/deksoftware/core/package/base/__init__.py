import os
import re
import json
import functools
from pathlib import Path
from dektools.shell import shell_output
from dektools.file import write_file
from dektools.download import download_http_exist
from dektools.version import version_is_release, version_extract, version_cmp_key
from dekartifacts.artifacts.staticfiles import StaticfilesArtifact

path_resources = Path(__file__).resolve().parent.parent.parent.parent / 'resources'


class PackageBase:
    artifact_cls = StaticfilesArtifact

    def __init__(self, meta, *args):
        self.meta = meta
        self.args = args
        self.artifact = self.artifact_cls()

    def pull(self, version):
        if self.is_remote:
            path_out = self.artifact.pull(self.location(version))
            return write_file(self.filename, t=True, m=path_out)
        else:
            return write_file(self.filename, t=True, c=self.location(version))

    def exist(self, version):
        return download_http_exist(self.location(version))

    @property
    def name(self):
        return self.meta['name']

    @property
    def ext(self):
        ext = self.meta.get('ext')
        if ext is None:
            return os.path.splitext(self.meta['release'])[-1]
        return ext

    @property
    def filename(self):
        return self.name + self.ext

    @property
    def is_remote(self):
        return not self.meta['release'].startswith('/')

    def location(self, version):
        result = self.meta['release'].format(version=version)
        if not self.is_remote:
            return str(path_resources) + result
        return result

    @property
    @functools.lru_cache(None)
    def versions(self):
        version_b = []
        version_d = []
        for x in self.versions_all:
            is_release = version_is_release(x)
            if is_release is not None:
                if is_release:
                    version_d.append(version_extract(x))
            else:
                version_b.append(x)
        return [*sorted(version_b), *sorted(version_d, key=version_cmp_key(), reverse=True)]

    @property
    @functools.lru_cache(None)
    def versions_all(self):
        for key, value in (self.meta.get('versions') or {}).items():
            if key == 'github':
                path = value['path']
                match = value.get('match')
                content = shell_output(f"curl -sL https://api.github.com/repos/{path}/tags")
                result = [x['name'].lstrip('v') for x in json.loads(content)]
                if match:
                    result = [x for x in result if re.match(match, x)]
                return result
            elif key == 'value':
                return value
        return []


all_package = {}


def register_package(name):
    def wrapper(cls):
        all_package[name] = cls

    return wrapper
