""" Monitor class for system monitoring tasks on a remote machine. """

# Imports
############################################################################################################
from labmonitor.connection import Connection


# Class
############################################################################################################

class Monitor:
    """ The Monitor class performs system monitoring tasks on a remote machine.

    This class provides methods for retrieving system resource usage, managing users,
    and monitoring logged-in sessions via an SSH connection.

    Attributes:
    - connection (Connection): An instance of the `Connection` class used to execute SSH commands.

    Methods:
    - get_usage_cpu: Retrieves CPU usage details.
    - get_usage_gpu: Retrieves GPU usage details.
    - get_usage_ram: Retrieves RAM usage details.
    - get_usage_disk: Retrieves disk usage details.
    - get_users: Retrieves user details.
    - add_new_user: Adds a new user to the system.
    - add_sudo_grup: Adds a user to the `sudo` group.
    - remove_sudo_grup: Removes a user from the `sudo` group.
    - remove_user: Deletes a user and their home directory.
    - logged_users: Retrieves details of currently logged-in users.
    """


    def __init__(self, connection:Connection) -> None:
        """ Initializes the Monitor object with the provided Connection instance.

        Args:
        - connection (Connection): An instance of the Connection class for executing SSH commands.

        Returns:
        - None
        """

        self.connection = connection
    
    def get_usage_cpu(self) -> dict:
        """ Retrieves the current CPU usage percentage on the connected machine.

        The method executes a command via SSH to check the CPU usage, specifically
        the combined percentage of user and system CPU usage.

        Args:
        - None

        Returns:
        - dict: A dictionary containing CPU usage information.

        Raises:
        - Exception: If the SSH command fails or the connection is invalid.
        """

        cpu_usage = float(self.connection.execute_ssh_command("top -bn1 | grep -i 'Cpu(s)' | awk '{print $2+$4}'").replace(',', '.'))
        
        return {"cpu_info": {"cpu_usage_percentage": cpu_usage}}

    def get_usage_gpu(self) -> dict:
        """ Retrieves GPU usage information on the connected machine.

        The method executes commands via SSH to gather details about GPU memory usage, utilization, 
        and processes using the GPU. It associates users with GPU processes when available.

        Returns:
        - dict: A dictionary containing GPU usage information.

        Raises:
        - Exception: If the SSH command fails or the output cannot be parsed.
        """

        gpu_info = []
        gpu_output = self.connection.execute_ssh_command("nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits")
        gpu_lines = gpu_output.split("\n")
        gpu_process_output = self.connection.execute_ssh_command("nvidia-smi --query-compute-apps=pid,name,gpu_name --format=csv,noheader,nounits").split("\n")

        if gpu_process_output[0] != "": 
            pids, process, gnames = zip(*[p.split(",") for p in gpu_process_output])
            gpu_users = [self.connection.execute_ssh_command(f"ps -p {pid} -o user --no-headers") if pid != "[N/A]" else "null" for pid in pids]
        else: 
            gpu_users =  ["null"] * len(gpu_lines);  process = ["null"] * len(gpu_lines)

        if len(gpu_lines) != len(gpu_users):
            name_to_user_process = {gnames[i]: (gpu_users[i], process[i]) for i in range(len(gnames))}
            gpu_users_new = ["null"] * len(gpu_lines)
            process_new = ["null"] * len(gpu_lines)
            for l, gpu in enumerate(gpu_lines):
                gpu_name = gpu.split(",")[1]
                if gpu_name in name_to_user_process:
                    gpu_users_new[l], process_new[l] = name_to_user_process[gpu_name]

            gpu_users, process = gpu_users_new, process_new

        for i, line in enumerate(gpu_lines):
            try:
                gpu_index, name, mem_used, mem_total, gpu_util = line.split(", ")
                gpu_info.append({
                    "gpu_index": int(gpu_index),
                    "name": name,
                    "memory_used": float(mem_used) / 1024,
                    "memory_total": float(mem_total) / 1024,
                    "utilization_gpu": gpu_util,
                    "process": process[i],
                    'user': gpu_users[i],
                })
            except Exception as e:
                print(f"Erro GPU {line}\n{e}")
                
        return {"gpu_info": gpu_info}

    def get_usage_ram(self) -> dict:
        """ Retrieves the current RAM usage information on the remote machine.

        The method executes an SSH command to gather memory usage statistics via the 'free' command 
        and returns the used, free, and total RAM on the system.

        Returns:
        - dict: A dictionary containing the RAM usage information.

        Raises:
        - Exception: If the SSH command fails or there is an issue with the connection.
        """

        ram_command = "free -g | awk '/^Mem/ {print $3, $4, $2}'"
        ram_data = self.connection.execute_ssh_command(ram_command).split()
        ram_used = float(ram_data[0])
        ram_free = float(ram_data[1])
        total_ram = float(ram_data[2])

        return {
            "ram_info": {
                "ram_used": ram_used,
                "ram_free": ram_free,
                "total_ram": total_ram
            }
        }
    

    def get_usage_disk(self) -> dict:
        """ Retrieves disk usage information from the remote machine.

        The method executes an SSH command to gather disk space usage details, 
        including total size, used space, available space, and usage percentage. 
        It filters out certain common system directories to provide information 
        about user-mounted disks.

        Returns:
        - dict: A dictionary containing disk usage information.

        Raises:
        - Exception: If the SSH command fails or there is an issue with the connection.
        """

        disk_command = "df -h --output=target,size,used,avail,pcent"
        disk_output = self.connection.execute_ssh_command(disk_command)
        lines = disk_output.split("\n")
        disk_info = []
        for line in lines[1:]:
            values = line.split()
            if len(values) >= 5 and not "snap" in values[0] and not "run" in values[0] and not "dev" in values[0] and not "tmp" in values[0] and not "boot" in values[0] and not "var" in values[0] and not "sys" in values[0]:
                disk_info.append({
                    "mount_point": values[0],
                    "total_size": values[1],
                    "used": values[2],
                    "available": values[3],
                    "usage_percentage": values[4]
                })
                
        return {"disk_info": disk_info}

    def get_users(self) -> dict:
        """ Retrieves a list of users on the remote machine with their associated groups.

        This method executes an SSH command to gather a list of users whose user ID (UID) 
        is greater than or equal to 1000 and less than 65534 (which typically corresponds to 
        non-system users on most Unix-like systems). Then, it retrieves the groups each user belongs to.

        Returns:
        - dict: A dictionary where the keys are the usernames and the values are lists of groups the user belongs to.

        Raises:
        - Exception: If the SSH command fails or there is an issue with the connection.
        """

        result = {}
        users_command = "awk -F: '$3 >= 1000 && $3 < 65534 {print $1}' /etc/passwd"
        users_output = self.connection.execute_ssh_command(users_command)
        users = users_output.split()
        grups = list(map(lambda u: self.connection.execute_ssh_command(f"groups {u}").split()[2:], users))
        for u, g in zip(users, grups): result[u]=g
        return result

    def add_new_user(self, username: str, password: str, sudo_password: str) -> str:
        """ Adds a new user to the system with the specified username and password.

        This method first uses 'sudo' to create a new user with the 'useradd' command and then sets the user's password 
        using 'chpasswd'. The password is set for the newly created user.

        Args:
        - username (str): The username for the new user to be created.
        - password (str): The password for the new user.
        - sudo_password (str): The sudo password for authentication to execute privileged commands.

        Returns:
        - str: The output of the command execution, which can indicate success or failure.

        Raises:
        - Exception: If the command execution fails or there is an issue with the connection.
        """

        new_user_cmd = f"""
                        echo '{sudo_password}' | sudo -S useradd -m {username} && \
                        echo '{password}:{password}' | sudo -S chpasswd"""
        useradd_output = self.connection.execute_ssh_command(new_user_cmd)
        return useradd_output

    def add_sudo_grup(self, username: str, sudo_password: str) -> str:
        """ Adds the specified user to the 'sudo' group, granting them sudo privileges.

        This method executes a command to add the user to the 'sudo' group, which allows the user to perform administrative 
        tasks by using 'sudo' to execute commands with elevated privileges.

        Args:
        - username (str): The username of the user to be added to the 'sudo' group.
        - sudo_password (str): The password for the current user (who has 'sudo' privileges) to authenticate the 'sudo' command.

        Returns:
        - str: The output of the command execution, which can indicate success or failure.

        Raises:
        - Exception: If the command execution fails or there is an issue with the connection.
        """

        sudo_user_cmd = f"""echo '{sudo_password}' | sudo -S usermod -aG sudo {username}"""
        addsudo_output = self.connection.execute_ssh_command(sudo_user_cmd)

        return addsudo_output

    def remove_sudo_grup(self, username: str, sudo_password: str) -> str:
        """ Removes the specified user from the 'sudo' group, revoking their sudo privileges.

        This method executes a command to remove the user from the 'sudo' group, thus preventing the user from performing 
        administrative tasks with 'sudo' on the system.

        Args:
        - username (str): The username of the user to be removed from the 'sudo' group.
        - sudo_password (str): The password for the current user (who has 'sudo' privileges) to authenticate the 'sudo' command.

        Returns:
        - str: The output of the command execution, which can indicate success or failure.

        Raises:
        - Exception: If the command execution fails or there is an issue with the connection.
        """

        sudo_user_cmd = f"echo '{sudo_password}' | sudo -S deluser {username} sudo"
        removesudo_output = self.connection.execute_ssh_command(sudo_user_cmd)
        
        return removesudo_output

    def remove_user(self, username: str, sudo_password: str) -> str:
        """ Removes a specified user and their home directory from the system.

        This method executes a command to delete the user account and its associated home directory 
        from the system. The 'sudo' password is required to authenticate the command.

        Args:
        - username (str): The username of the user to be deleted.
        - sudo_password (str): The password for the current user (who has 'sudo' privileges) to authenticate the 'sudo' command.

        Returns:
        - str: The output of the command execution, which can indicate success or failure.

        Raises:
        - Exception: If the command execution fails or there is an issue with the connection.
        """

        remove_cmd = f"echo '{sudo_password}' | sudo -S userdel -r {username}"
        remove_output = self.connection.execute_ssh_command(remove_cmd)
        
        return remove_output

    def logged_users(self) -> dict:
        """ Retrieves a list of currently logged-in users and their session information.

        The method executes the `w` command via SSH to gather details about logged-in users, 
        including username, terminal, source IP, login time, and CPU usage.

        Returns:
        - dict: A dictionary containing logged-in user details.

        Raises:
        - Exception: If the SSH command fails or the output format is invalid.
        """

        res = []
        w_cmd = f"w -h"
        w_output = self.connection.execute_ssh_command(w_cmd)
        line = w_output.split("\n")

        try: 
            for usr in line:
                info = usr.split()
                res.append(
                        {
                            'user': info[0],
                            'TTY': info[1],
                            'from': info[2],
                            'login_time': info[3],
                            'jcpu': info[5],
                        })
                        
        except Exception as e:
            res.append({'user': "", 'TTY': "", 'from': "", 'login_time':"", 'jcpu': "",})
            print(f"Erro: {e}")
            return {'logged_users': res}
        
        return {'logged_users': res}
