import os
from pathlib import Path
from dektools.shell import shell_wrapper
from dektools.file import sure_dir, merge_assign, remove_path
from dektools.zip import decompress_files
from .base import InstallerBase, register_installer


@register_installer('nerdctl')
class NerdctlInstaller(InstallerBase):
    def run(self):
        path_out = Path(decompress_files(self.path)).resolve()
        path_bin = path_out / 'bin'
        for exe in os.listdir(path_bin):
            if not exe.endswith('.sh'):
                self.exe(path_bin / exe)
        sure_dir('/opt/cni/bin')
        sure_dir('/etc/systemd/system')
        path_bin = path_out / 'libexec/cni'
        for exe in os.listdir(path_bin):
            self.exe(path_bin / exe, '/opt/cni/bin')
        merge_assign('/etc/systemd/system', path_out / 'lib/systemd/system')
        shell_wrapper('systemctl enable buildkit containerd')
        shell_wrapper('systemctl restart buildkit containerd')
        shell_wrapper('systemctl --no-pager status buildkit.service')
        shell_wrapper('systemctl --no-pager status containerd.service')
        remove_path(path_out)
