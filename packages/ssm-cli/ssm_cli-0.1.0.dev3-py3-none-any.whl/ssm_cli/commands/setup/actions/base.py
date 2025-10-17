from ssm_cli.commands.setup.definition import action
from ssm_cli.xdg import get_conf_root, get_conf_file
from ssm_cli.config import CONFIG
from confclasses import from_dict, save, load
import logging
from rich.text import Text

logger = logging.getLogger(__name__)

@action
class ConfDirAction:
    action_name = "base.conf-dir"

    def run(self):
        root = get_conf_root(False)
        yield Text(f"Checking for {root}", style="cyan")
        if not root.exists():
            yield Text(f"creating directory", style="green")
            root.mkdir(511, True, True)
        else:
            if not root.is_dir():
                yield Text(f"{root} already exists and is not a directory. Cleanup is likely needed.", style="red")
                return False
            yield Text(f"already exists", style="cyan")
        
        return True

@action
class ConfFileAction:
    action_name = "base.conf-file"
    action_depends = ["base.conf-dir"]

    group_tag_key: str
    replace: bool = False
    
    def pre(self):
        path = get_conf_file(False)
        if path.exists():
            yield Text(f"Found existing config", style="cyan")
            if not self.replace:
                yield Text(f"Pulling in config from {path}", style="cyan")
                with path.open('r') as file:
                    load(CONFIG, file)
            else:
                yield Text(f"Replacing existing config, so we will use defaults instead", style="cyan")
                from_dict(CONFIG, {})
                self.apply_config()
        else:
            yield Text(f"No existing config found, so we will use defaults", style="cyan")
            from_dict(CONFIG, {})
            self.apply_config()

        return True

    def apply_config(self):
        if self.group_tag_key:
            CONFIG.group_tag_key = self.group_tag_key
        
    def run(self):
        path = get_conf_file(False)
        if path.exists() and not self.replace:
            yield Text(f"{path} - skipping (already exists)", style="cyan")
            return True

        try:
            with path.open("w+") as file:
                save(CONFIG, file)
                yield Text(f"{path} - created", style="cyan")
            return True
        except Exception as e:
            logger.error(e)
            path.unlink(True)
            yield Text(f"{path} - failed", style="red")
            return False