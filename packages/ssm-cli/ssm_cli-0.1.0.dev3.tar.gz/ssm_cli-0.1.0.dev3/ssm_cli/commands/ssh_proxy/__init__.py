import socket
import time

from ssm_cli.commands.ssh_proxy.server import SshServer
from ssm_cli.instances import Instance, Instances
from ssm_cli.config import CONFIG
from ssm_cli.commands.base import BaseCommand
from ssm_cli.cli_args import ARGS

import logging
logger = logging.getLogger(__name__)


class SshProxyCommand(BaseCommand):
    HELP="SSH ProxyCommand feature"
    def add_arguments(parser):
        parser.add_argument("group", type=str, help="group to run against")

    def run():
        logger.info("running proxycommand action")


        instances = Instances()
        instance = instances.select_instance(ARGS.group, CONFIG.actions.proxycommand.selector)

        if instance is None:
            logger.error("failed to select host")
            raise RuntimeError("failed to select host")

        logger.info(f"connecting to {repr(instance)}")
        
        connections = {}
        server = SshServer(direct_tcpip_callback(instance, connections))
        server.start()

def direct_tcpip_callback(instance: Instance, connections: dict) -> callable:
    def callback(host, remote_port) -> socket.socket:
        if (host, remote_port) not in connections:
            logger.debug(f"connect to {host}:{remote_port}")
            internal_port = get_next_free_port(remote_port + 3000, 20)
            logger.debug(f"got internal port {internal_port}")
            try:
                instance.start_port_forwarding_session_to_remote_host(host, remote_port, internal_port)
                connections[(host, remote_port)] = internal_port
            except Exception as e:
                logger.error(f"failed to open port forward: {e}")
                return None
        else:
            internal_port = connections[(host, remote_port)]
        
        logger.debug(f"connecting to session manager plugin on 127.0.0.1:{internal_port}")
        # Even though we wait for the process to say its connected, we STILL need to wait for it
        for attempt in range(10):
            try:
                sock = socket.create_connection(('127.0.0.1', internal_port))
                logger.info(f"connected to 127.0.0.1:{internal_port}")
            except Exception as e:
                logger.warning(f"connection attempt {attempt} failed: {e}")
                time.sleep(0.1)
        
        return sock

    return callback

def get_next_free_port(port: int, tries: int) -> int:
    """
    Get the next free port after the given port, TODO: investigate if we can use socket files
    """
    max_port = port + tries
    while port < max_port:
        logger.debug(f"attempting port {port}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        if result != 0:
            return port
        port += 1