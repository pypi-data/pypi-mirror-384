from ssm_cli.instances import Instances
from ssm_cli.commands.base import BaseCommand
from ssm_cli.cli_args import ARGS

import logging
logger = logging.getLogger(__name__)

from rich.console import Console

console = Console()

class ShellCommand(BaseCommand):
    HELP = "Connects to instances"
    
    def add_arguments(parser):
        parser.add_argument("group", type=str, help="group to run against")

    def run():
        logger.info("running shell action")

        instances = Instances()
        try:
            instance = instances.select_instance(ARGS.group, "tui")
        except KeyboardInterrupt:
            logger.error("user cancelled")
            console.print(f":x: [bold red]user cancelled[/bold red]")
            return

        if instance is None:
            logger.error("failed to select host")
            console.print(f":x: [bold red]failed to select host[/bold red]")
            return

        logger.info(f"connecting to {repr(instance)}")
        
        instance.start_session()