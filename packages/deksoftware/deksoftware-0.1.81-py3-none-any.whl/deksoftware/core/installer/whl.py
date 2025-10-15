import sys
from dektools.file import list_dir
from dektools.shell import shell_wrapper, shell_exitcode
from dektools.py import get_whl_name
from .base import InstallerBase, register_installer


@register_installer('whl')
class WhlInstaller(InstallerBase):
    def run(self):
        for whl_file in list_dir(self.path):
            if whl_file.endswith('.whl'):
                shell_exitcode(f"{sys.executable} -m pip uninstall -y {get_whl_name(whl_file)}")
                optional = f"[{self.extra}]" if self.extra else ''
                shell_wrapper(f"{sys.executable} -m pip install {whl_file}{optional}")
