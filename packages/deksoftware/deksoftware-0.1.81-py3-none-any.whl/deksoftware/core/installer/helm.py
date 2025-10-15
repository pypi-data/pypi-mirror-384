from pathlib import Path
from dektools.file import remove_path
from dektools.zip import decompress_files
from .base import InstallerBase, register_installer


@register_installer('helm')
class HelmInstaller(InstallerBase):
    def run(self):
        path_out = Path(decompress_files(self.path)).resolve()
        path_bin = path_out / 'linux-amd64/helm'
        self.exe(path_bin)
        remove_path(path_out)
