""" A module to manage SSH connections to remote machines. """

# Imports
############################################################################################################
import paramiko


# Class
############################################################################################################
class Connection:
    """
    A class to manage SSH connections to remote machines.

    This class allows establishing an SSH connection to a remote machine using
    the provided connection details (IP address, username, and password). It can
    also be used to execute commands remotely and interact with the machine.

    Attributes:
    ip (str): The IP address of the remote machine.
    username (str): The username for authentication on the remote machine.
    password (str): The password associated with the username for authentication.
    ssh (paramiko.SSHClient): The SSH client instance used to manage the connection.

    Methods:
    __init__(self, ip: str, username: str, password: str): Initializes the Connection object with the provided connection details and establishes an SSH connection.

    set_connection(self): Sets the connection details for a machine.

    get_connection(self): Establishes an SSH connection to a remote machine using the provided connection details.
    
    execute_ssh_command(self, command:str): Executes a command over an established SSH connection.

    """

    def __init__(self, ip:str, username:str, password:str) -> None:
        """ Initializes the Connection object with the provided connection details and establishes an SSH connection.

        Args:
        - ip (str): The IP address of the remote machine.
        - username (str): The username for authentication on the remote machine.
        - password (str): The password associated with the username for authentication.

        Returns:
        - None
        """

        self.ip = ip
        self.username = username
        self.password = password
        self.ssh = self.get_connection()


    def set_connection(self, ip:str, username:str, password:str):
        """ Sets the connection details for a machine.

        This method stores the IP address, username, and password for the machine
        to facilitate further connections or operations requiring authentication.

        Parameters:
        - ip (str): The IP address of the machine.
        - username (str): The username used for authentication on the machine.
        - password (str): The password associated with the provided username.

        Returns:
        - None
        """

        self.ip = ip
        self.username = username
        self.password = password

    def get_connection(self):
        """ Establishes an SSH connection to a remote machine using the provided connection details.

        This method uses the `paramiko` library to establish an SSH connection to the machine
        with the stored IP address, username, and password. If the connection is successful, 
        it stores the SSH client instance for further interaction.

        Args:
        - None

        Raises:
        - RuntimeError: If there is an error during the connection attempt (e.g., invalid credentials or network issues).

        Returns:
        - None
        """

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, username=self.username, password=self.password, timeout=10, look_for_keys=False, allow_agent=False)
            self.ssh = ssh
        except Exception as e:
            raise RuntimeError(f"Erro na conexão: {e}")
        
        return ssh
    
    def execute_ssh_command(self, command:str) -> str:
        """
        Executes a command over an established SSH connection.

        This method sends the specified command to the remote machine via the existing
        SSH connection and retrieves the output. If the command executes successfully, 
        the output is returned as a string, with leading/trailing whitespace removed.

        Args:
        - command (str): The command to be executed on the remote machine.

        Returns:
        - str: The output of the command executed on the remote machine, stripped of leading/trailing whitespace.

        Raises:
        - RuntimeError: If there is an error executing the command (e.g., network issues, invalid command, etc.).
        """

        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            return stdout.read().decode().strip()
        except Exception as e:
            raise RuntimeError(f"Erro ao executar comando '{command}': {e}")
