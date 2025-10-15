from dektools.file import remove_path
from dektools.serializer.yaml import yaml
from .package.base import all_package, path_resources
from .installer.base import all_installer


class Repository:
    def __init__(self, typed=None, *args):
        self.packages = {}
        self.load(path_resources / 'index.yaml', typed or 'default', *args)

    def load(self, path, typed, *args):
        package_cls = all_package[typed]
        meta = yaml.load(path)
        for pd in meta.get('packages', []):
            pk = package_cls(pd, *args)
            self.packages[pk.name] = pk

    def pull(self, name, version):
        return self.packages[name].pull(version)

    def install(self, name, version=None, path=None, extra=None):
        path_final = path or self.pull(name, version or 'latest')
        installer_cls = all_installer[name]
        installer_cls(path_final, extra).run()
        if not path:
            remove_path(path_final)
