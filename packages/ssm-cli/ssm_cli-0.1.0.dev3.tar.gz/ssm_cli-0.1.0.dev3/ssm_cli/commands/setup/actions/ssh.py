from ssm_cli.commands.setup.definition import action
from ssm_cli.xdg import get_ssh_hostkey
import paramiko
from rich.text import Text


@action
class SshHostKeyGenAction:
    action_name = "ssh.host-keygen"
    action_depends = ["base.conf-dir"]

    def run(self):
        path = get_ssh_hostkey(False)
        if path.exists():
            yield Text(f"{path} - skipping (already exists)", style="cyan")
        else:
            host_key = paramiko.RSAKey.generate(1024)
            host_key.write_private_key_file(path)
            yield Text(f"{path} - created", style="cyan")

        return True