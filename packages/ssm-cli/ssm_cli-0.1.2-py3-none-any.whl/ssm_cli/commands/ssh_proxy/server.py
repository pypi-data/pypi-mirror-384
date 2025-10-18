import threading
import paramiko

from ssm_cli.commands.ssh_proxy.transport import StdIoSocket
from ssm_cli.commands.ssh_proxy.shell import ShellThread
from ssm_cli.commands.ssh_proxy.forward import ForwardThread
from ssm_cli.commands.ssh_proxy.channels import Channels
from ssm_cli.xdg import get_ssh_hostkey

import logging
logger = logging.getLogger(__name__)

class SshServer(paramiko.ServerInterface):
    """
    Creates ssh server using StdIoSocket
    """
    event: threading.Event
    direct_tcpip_callback: callable # We use a callback to keep server and session manager plugin code separate
    
    def __init__(self, direct_tcpip_callback: callable):
        """
        Creates ssh server using StdIoSocket
        
        Args:
            direct_tcpip_callback (callable): Callback to create a connection via the session manager plugin
        """
        logger.debug("creating server")
        self.event = threading.Event()
        self.direct_tcpip_callback = direct_tcpip_callback
    
    def start(self):
        logger.info("starting server")

        sock = StdIoSocket()
        self.transport = paramiko.Transport(sock)
        self.channels = Channels(self.transport)

        key_path = get_ssh_hostkey()
        host_key = paramiko.RSAKey(filename=key_path)
        logger.info("Loaded existing host key")
        
        self.transport.add_server_key(host_key)
        self.transport.start_server(server=self)

        self.event.wait()

    # Auth handlers, just allow anything. The only use of this code is ProxyCommand and auth is not needed
    def get_allowed_auths(self, username):
        logger.info(f"allowing all auths: username={username}")
        return "password,publickey,none"
    def check_auth_none(self, username):
        logger.info(f"accepting auth none: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    def check_auth_password(self, username, password):
        logger.info(f"accepting auth password: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    def check_auth_publickey(self, username, key):
        logger.info(f"accepting auth public key: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    
    # Allow sessions
    def check_channel_request(self, kind, chanid):
        logger.info(f"received channel request: kind={kind} chanid={chanid}")
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        logger.error(f"we only accept session")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY
    
    # Just accept the PTY request
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    # Start a echo shell if requested
    def check_channel_shell_request(self, channel):
        logger.info(f"shell request: {channel.get_id()}")
        t = ShellThread(channel, self.channels)
        t.start()
        return True

    # Handle direct-tcpip requests when they come in, this will only be triggered when a connection is made.
    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        logger.info(f"direct TCP/IP request: chan={chanid} origin={origin} destination={destination}")
        host = destination[0]
        remote_port = destination[1]

        sock = self.direct_tcpip_callback(host, remote_port)
        
        if not sock:
            logger.error("failed to connect to session manager plugin")
            return paramiko.OPEN_FAILED_CONNECT_FAILED
        
        # Start thread to open the channel and forward data
        t = ForwardThread(sock, chanid, self.channels)
        t.start()
        
        logger.debug("started forwarding thread")
        return paramiko.OPEN_SUCCEEDED
    
    def get_banner(self):
        return ("SSM CLI - ProxyCommand SSH server\r\n", "en-US")

