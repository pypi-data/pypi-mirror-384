from ssm_cli.instances import Instances
from ssm_cli.commands.base import BaseCommand
from ssm_cli.cli_args import ARGS
import logging
from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)

class ListCommand(BaseCommand):
    HELP = """List all instances in a group, if no group provided, will list all available groups"""

    def add_arguments(parser):
        parser.add_argument("group", type=str, nargs="?", help="group to run against")
    
    def run():
        logger.info("running list action")
        
        instances = Instances()

        if ARGS.group:
            table = Table()
            table.add_column("ID")
            table.add_column("Name")
            table.add_column("IP")
            table.add_column("Ping")
            for instance in instances.list_instances(ARGS.group, True):
                table.add_row(instance.id, instance.name, instance.ip, instance.ping)
            console.print(table)
        else:
            table = Table()
            table.add_column("Group")
            table.add_column("Total")
            table.add_column("Online")
            for group in sorted(instances.list_groups(), key=lambda x: x['name']):
                table.add_row(group['name'], str(group['total']), str(group['online']))
            console.print(table)
