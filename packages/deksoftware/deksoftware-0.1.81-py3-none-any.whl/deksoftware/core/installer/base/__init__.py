import os
from dektools.shell import shell_wrapper
from dektools.file import normal_path


class InstallerBase:
    def __init__(self, path, extra=None):
        self.path = normal_path(path)
        self.extra = extra

    def run(self):
        raise NotImplementedError

    @staticmethod
    def exe(path, target=None, ext=True):
        target = target or '/usr/local/bin'
        filename = os.path.basename(path)
        if not ext:
            filename = os.path.splitext(filename)[0]
        shell_wrapper(
            f'install {path} '
            f'{target}/{filename}'
        )


class InstallerBash(InstallerBase):
    def run(self):
        self.exe(self.path, ext=True)


all_installer = {}


def register_installer(name):
    def wrapper(cls):
        all_installer[name] = cls

    return wrapper


def register_installer_bash(*name_list):
    for name in name_list:
        register_installer(name)(type(name, (InstallerBash,), {}))
