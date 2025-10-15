from dektools.download import curl_auth_args
from dektools.shell import shell_wrapper
from .base import PackageBase, register_package


@register_package('coding')
class CodingPackage(PackageBase):
    @property
    def registry(self):
        return self.args[0]

    @property
    def auth(self):
        return dict(username=self.args[1], password=self.args[2])

    @property
    def is_remote(self):
        return True

    def location(self, version):
        return f"{self.registry}/{self.name}?version={version}"

    def push(self, path, version):
        shell_wrapper(f"curl -T {path}  {self.location(version)}{curl_auth_args(**self.auth)}")
