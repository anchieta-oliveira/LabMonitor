""" QueueJob class for managing job queue information and interacting with machine configurations. """

# Imports
############################################################################################################

import os
import time
import smtplib
import threading
import pandas as pd

from datetime import datetime
from labmonitor.data import Data
from email.mime.text import MIMEText
from labmonitor.monitor import Monitor
from labmonitor.connection import Connection
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed


# Class
############################################################################################################



class QueueJob:
    """ QueueJob class for managing job queue information and interacting with machine configurations.

    Class that manages job queue information and interacts with data regarding machine configurations 
    and job submissions. It allows reading job data from an csv file, managing job states, and interacting 
    with the machine configurations to update job status.

    Attributes:
    - df (pd.DataFrame): DataFrame containing the job queue information, read from the specified csv file.
    - path (str): The path to the csv file containing the queue job data (default: 'queue_job.csv').
    - data (Data): The data object containing machine and email configurations.
    - machines (pd.DataFrame): DataFrame containing machine configurations from `data.machines`.

    Methods:
    - __init__(self, data: Data, path: str = "queue_job.csv"): Constructor for initializing the QueueJob object.
    - read_csv(self, path: str) -> pd.DataFrame: Reads job queue data from an csv file and returns it as a DataFrame.
    """

    def __init__(self, data: Data, path: str = "queue_job.csv") -> None:
        """ Constructor for the QueueJob class.

        Initializes the QueueJob object with the specified Data object and csv file path.

        Args:
        data (Data): An instance of the Data class that holds machine and email information.
        path (str): The file path for the csv file storing the queue data. Defaults to "queue_job.csv".

        Returns:
        None
        """

        self.df = self.read_csv(path)
        self.path = path
        self.data = data
        self.machines = data.machines

    def read_csv(self, path: str = "queue_job.csv") -> pd.DataFrame:
        """ Reads an csv file and processes its contents into a DataFrame.
        
        Parameters:
        - path (str): The file path to the csv file. Defaults to "queue_job.csv".
        
        Returns:
        - pd.DataFrame: A DataFrame containing the contents of the csv file.
        
        Behavior:
        - If the file specified by `path` exists, it reads the file into a DataFrame.
        - Converts the 'fim' and 'inicio' columns to datetime objects for proper handling of date and time data.
        - If the file does not exist, it resets the DataFrame using the `reset` method.
        """

        if os.path.exists(path):
            try:
                self.df = pd.read_csv(path)
                self.df['fim'] = pd.to_datetime(self.df['fim'])
                self.df['inicio'] = pd.to_datetime(self.df['inicio'])
                self.df['submit'] = pd.to_datetime(self.df['submit'])
            except Exception as e:
                print(f"Error reading the file {path}: {e}", flush=True)
                backup_path = f"{os.path.splitext(path)[0]}_old{os.path.splitext(path)[1]}"
                try:
                    self.df = pd.read_csv(backup_path)
                    self.df['fim'] = pd.to_datetime(self.df['fim'])
                    self.df['inicio'] = pd.to_datetime(self.df['inicio'])
                    self.df['submit'] = pd.to_datetime(self.df['submit'])
                    print(f"Backup file {backup_path} uploaded successfully.", flush=True)
                except Exception as e_backup:
                    print(f"Error reading the backup file{backup_path}: {e_backup}", flush=True)
                    self.reset()
        else:
            self.reset()

        return self.df

    def save(self) -> None:
        """ Saves the current DataFrame to an csv file.

        Args:
        - None

        Returns:
        - None
        
        Behavior:
        - Writes the contents of the DataFrame `self.df` to an csv file specified by `self.path`.
        - The file is saved without including the index.
        """
        backup_path = f"{os.path.splitext(self.path)[0]}_old{os.path.splitext(self.path)[1]}"
        
        try:
            if os.path.exists(self.path):
                os.rename(self.path, backup_path)

            self.df.to_csv(self.path, index=False)
        except Exception as e:
            print("Error saving the file: ", e, flush=True)

        

    def reset(self) -> pd.DataFrame:
        """ Resets the DataFrame to a default structure and saves it to an csv file.

        Args:
        - None

        Returns:
        - pd.DataFrame: A new DataFrame with predefined columns and no data.
        
        Behavior:
        - Initializes a new DataFrame with a specified set of columns, representing job information and metadata.
        - Saves the newly created empty DataFrame to an csv file named "queue_job.csv" without including the index.
        - Returns the new empty DataFrame.
        """

        columns = ["ip", "name", "username", "job_name", "status", "pid", "path_exc", "path_origin", "machine_origin", "script_name", "submit", "inicio", "fim", "n_cpu", "taskset", "gpu_requested", "gpu_name", "gpu_index", "e-mail", "notification_start", "notification_end"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_csv("queue_job.csv", index=False)
        return self.df  

    def submit(self, username: str, job_name: str, machine_origin: str, script_name: str, path_origin: str, n_cpu: int, email: str, gpus: list = ['all']) -> None:
        """ Submits a new job by adding its details to the DataFrame and saving the updated DataFrame to an csv file.

        Args:
        - username (str): The username of the individual submitting the job.
        - job_name (str): The name of the job being submitted.
        - machine_origin (str): The origin machine from where the job is submitted.
        - script_name (str): The name of the script associated with the job.
        - path_origin (str): The origin path of the job's script.
        - n_cpu (int): The number of CPUs requested for the job.
        - email (str): The email address for job notifications.
        - gpus (list): A list of GPUs requested for the job, defaults to `['all']`.

        Returns:
        - None

        Behavior:
        - Creates a dictionary with the job details, including the current timestamp as the submission time.
        - Converts the list of GPUs into a comma-separated string.
        - Adds the new job to the DataFrame.
        - Saves the updated DataFrame to an csv file using the `save` method.
        """

        new_job = {
            "username": username,
            "machine_origin": machine_origin,
            "job_name": job_name,
            "script_name": script_name,
            "path_origin": path_origin,
            "n_cpu": n_cpu,
            "e-mail": email,
            "gpu_requested": ",".join(gpus),
            "submit": datetime.now(),
            "notification_start": "N",
            "notification_end": "N",
        }

        self.df = pd.concat([self.df, pd.DataFrame([new_job])], ignore_index = True)
        self.save()
        print(self.df, flush=True)
    
    def update_gpu(self) -> None:
        """ Updates the GPU information for each machine listed in the 'machines' DataFrame.

        This method connects to each machine, retrieves the GPU usage statistics, and updates
        the 'machines' DataFrame with the latest GPU information. It then saves the updated 
        DataFrame to ensure the information is persistent.

        Args:
        - None

        Returns:
        - None
        """

        def run(ip: str, name: str, user: str, pw: str) -> tuple[str, dict]:
            """ Connects to a machine and retrieves GPU usage statistics.

            This function connects to a remote machine using SSH and retrieves the GPU usage statistics.
            It returns the machine name and a dictionary containing the GPU information.

            Args:
            - ip (str): The IP address of the machine.
            - name (str): The name of the machine.
            - user (str): The username for the SSH connection.
            - pw (str): The password for the SSH connection.

            Returns:
            - tuple[str, dict]: A tuple containing the machine name and a dictionary of GPU information.
            """

            try:
                print(f"Connecting to  {ip}...", flush=True)
                results = {}
                c = Connection(ip, user, pw)
                m = Monitor(c)
            except Exception as e:
                print(f"Error connecting to {ip}: {e}", flush=True)
                return name, None
            try:
                results.update(m.get_usage_gpu())
            except Exception as e:
                results.update({"gpu_info": []})
                print(f"Error getting GPU information from {ip}: {e}", flush=True)

            return name, results
        
        ips = self.data.machines['ip'].to_list()
        names = self.data.machines['name'].to_list()
        usernames = self.data.machines['username'].to_list()
        passwords = self.data.machines['password'].to_list()

        results = {}

        with ThreadPoolExecutor(max_workers=len(ips)) as executor:
            futures = [
                executor.submit(run, ip, name, user, pw)
                for ip, name, user, pw in zip(ips, names, usernames, passwords)
            ]
            for future in as_completed(futures):
                name, stats = future.result()
                if stats:
                    results[name] = stats

        data_gpu = []

        for name, stats in results.items():
            row = {"name": name}
            for gpu in stats["gpu_info"]:
                gpu_index = gpu["gpu_index"]
                row[f"GPU_{gpu_index}_Name"] = gpu["name"]
                sts = ""
                if f"GPU_{gpu_index}_status" in self.data.machines.columns: 
                    if self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0] != "": sts = self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0]
                row[f"GPU_{gpu_index}_status"] = sts

            if len(row.keys()) == 1:
                row['GPU_0_Name'] = "Null"; row['GPU_0_status'] = ""
                if f"GPU_0_status" in self.data.machines.columns: 
                    if self.data.machines[self.data.machines['name'] == name][f"GPU_0_status"].iloc[0] != "": sts = self.data.machines[self.data.machines['name'] == name][f"GPU_0_status"].iloc[0]
                row[f"GPU_0_status"] = sts

            data_gpu.append(row)

        self.data.machines = pd.merge(self.data.machines[['ip','name', 'username', 'password', 'status', 'allowed_cpu','cpu_used', 'name_allowed_gpu', 'path_exc']], pd.DataFrame(data_gpu), on="name")
        self.data.save_machines()

    def __allowed_gpu(self) -> None:
        """ Updates the GPU status for each machine based on the allowed GPUs.

        This method checks which GPUs are allowed for each machine and updates their status 
        to 'available' (available) if they match the allowed GPU names. If a GPU does not match
        or is not listed, its status is set to 'bloqueada' (blocked).

        The allowed GPU names are specified in the 'name_allowed_gpu' column, while the GPU names
        and their statuses are updated in corresponding columns in the 'machines' DataFrame.

        Args:
        - None

        Returns:
        - None
        """

        g_names = [e.split(",") for e in self.data.machines['name_allowed_gpu'].to_list()]
        col = self.data.machines.loc[:, self.data.machines.columns.str.contains(r"gpu_.*_name", case=False, regex=True)]

        for i, row in self.data.machines.iterrows():
            for c in col:
                for name in g_names[i]:
                    if name == self.data.machines[c].iloc[i]:
                        self.data.machines.loc[i, c.replace("Name", "status")] = "available"
                    elif name != self.data.machines[c].iloc[i]: 
                        self.data.machines.loc[i, c.replace("Name", "status")] = "bloqueada"
                    elif pd.isna(self.data.machines[c].iloc[i]):
                        self.data.machines.loc[i, c.replace("Name", "status")] = "bloqueada"

    def __status_in_queue(self) -> None:
        """ Updates the status of GPUs in the machines DataFrame to 'running' (executing) for jobs that are currently running.

        This method checks the DataFrame for jobs with a status of 'running' and updates the corresponding GPU status
        in the machines DataFrame. If the 'gpu_index' is NaN for any job, it is set to 0 by default.

        Args:
        - None

        Returns:
        - None
        """

        v = self.df[self.df['status'] == "running"]
        for i, maq in v.iterrows():
            if pd.isna(maq['gpu_index']): self.df.loc[i, ['gpu_index']] = 0; maq['gpu_index'] = 0
            self.data.machines.loc[
                    (self.data.machines['name'] == maq['name']) & 
                    (self.data.machines['ip'] == maq['ip']) & 
                    (self.data.machines[f"GPU_{int(maq['gpu_index'])}_Name"] == maq['gpu_name']),
                    f"GPU_{int(maq['gpu_index'])}_status"
                ] = "running"
     
    def __update_cpu_used(self) -> None:
        """ Updates the 'cpu_used' column in the machines DataFrame based on the number of CPUs allocated to currently running jobs.

        This method resets the 'cpu_used' column to 0 and then iterates over the jobs with the status
        'running', incrementing the 'cpu_used' count for each corresponding machine.

        Args:
        - None

        Returns:
        - None
        """

        v = self.df[self.df['status'] == "running"]
        self.data.machines.loc[:,'cpu_used'] = 0
        for i, maq in v.iterrows():
            self.data.machines.loc[
                    (self.data.machines['name'] == maq['name']) & 
                    (self.data.machines['ip'] == maq['ip']),
                    "cpu_used"
                ] += maq['n_cpu']

    def update_status_machines(self) -> None:
        """ Updates the status of machines by reading machine data, updating GPU and CPU usage,
        and modifying the job status for each machine.

        This method:
        - Reads the current machine data from a specified file.
        - Updates GPU status using the `update_gpu` method.
        - Updates the allowed GPU status with the `__allowed_gpu` method.
        - Updates CPU usage based on currently executing jobs using the `__update_cpu_used` method.
        - Updates the job status in the queue with the `__status_in_queue` method.
        - Saves the updated machine data to the specified path.

        Args:
        - None

        Returns:
        - None
        """

        self.data.read_machines(self.data.path_machines)
        self.update_gpu()
        self.__allowed_gpu()
        self.__update_cpu_used()
        self.__status_in_queue()
        self.data.save_machines()

    def search_available_machine(self, n_cpu: int, gpu: bool = False, gpu_name: list = ["all"], cpu_reserve: bool = True, n_cpu_reserve: int = 0) -> pd.DataFrame:
        """ Searches for available machines based on CPU and GPU requirements.
        
        Searches for available machines based on CPU and GPU requirements. Filters machines with:
        - Sufficient available CPU considering possible reservations.
        - Optional GPU requirements, including the ability to filter by GPU names.
        
        Args:
        - n_cpu (int): Number of CPUs required for the task.
        - gpu (bool): Whether GPU filtering is enabled (default is False).
        - gpu_name (list): List of GPU names to filter. If "all", all GPUs are considered (default is ["all"]).
        - cpu_reserve (bool): Whether to consider CPU reservations (default is True).
        - n_cpu_reserve (int): Number of CPUs reserved for other tasks (default is 0).
        
        Returns:
        - filtered_machines (pd.DataFrame): DataFrame of available machines based on the given criteria.
        """

        self.data.read_machines(self.data.path_machines)
    
        if cpu_reserve:
            available_cpu = self.data.machines.loc[
                (
                    ((self.data.machines['allowed_cpu'] - n_cpu_reserve) - self.data.machines['cpu_used']) >= n_cpu
                ) | (
                    (
                        self.data.machines.loc[:, self.data.machines.columns.str.contains(r"gpu.*name", case=False, regex=True)]
                        .apply(lambda col: col.str.contains("Null", case=False, na=False))
                        .any(axis=1)
                    ) &
                    ((self.data.machines['allowed_cpu'] - self.data.machines['cpu_used']) >= n_cpu)
                )
            ]

        else:
            available_cpu = self.data.machines.loc[(((self.data.machines['allowed_cpu']) - self.data.machines['cpu_used']) >= n_cpu)]

        if gpu:
            if cpu_reserve and n_cpu_reserve >= n_cpu: 
                available_cpu = self.data.machines.loc[(((self.data.machines['allowed_cpu']) - self.data.machines['cpu_used']) >= n_cpu)]

            gpu_status_cols = self.data.machines.loc[:,self.data.machines.columns.str.contains(r"gpu.*status", case=False, regex=True)].columns
            gpu_name_cols = self.data.machines.loc[:,self.data.machines.columns.str.contains(r"gpu.*name", case=False, regex=True)].columns
            
            gpu_status_available = self.data.machines[gpu_status_cols].eq("available").any(axis=1)

            if gpu_name[0] != "all":
                gpu_name_match = self.data.machines[gpu_name_cols].isin(gpu_name).any(axis=1) 
            else:
                gpu_name_match = self.data.machines[gpu_name_cols].any(axis=1) 
            
            if gpu_name[0] == "all" or gpu_name != ["Null"]:
                filtered_machines = self.data.machines.loc[self.data.machines['name'].isin(available_cpu['name'].to_list()) &
                                                        gpu_status_available & 
                                                        gpu_name_match & 
                                                        ~self.data.machines[gpu_name_cols].eq("Null").any(axis=1)]
            else:                 
                filtered_machines = self.data.machines.loc[self.data.machines['name'].isin(available_cpu['name'].to_list()) &
                                                        gpu_status_available & 
                                                        gpu_name_match
                                                        ]

            return filtered_machines
        
        else:
            return available_cpu

    def update_status_jobs(self) -> None:
        """ Updates the status and PID of jobs in the DataFrame.

        For each job in the `self.df` DataFrame:
        - If the status is 'executing', the `get_status_job` method is called to fetch the updated status and PID.
        - If the status is missing (NaN), it is set to 'waiting'.
        
        After the updates, the changes are saved by calling the `save` method.

        This function modifies the `self.df` DataFrame directly and does not return any value.

        Args:
        - None.

        Returns:
        - None.
        """

        for i, job in self.df.iterrows():
            if job['status'] == 'running': 
                self.df.loc[i, ['status', 'pid']] = self.get_status_job(job['name'], job['path_exc'])
            if pd.isna(job['status']): 
                self.df.loc[i, ['status']] = 'pending'
        self.save()

    def copy_dir(self, ip_origin, username_origin, password_origin, ip_exc, username_exc, password_exc, path_origin: str, path_exc: str, inverse: bool = False) -> None:
        """ Copies a directory between two remote machines using SCP, with an optional inverse operation.

        This method connects to a source machine (origin) via SSH, and then uses `sshpass` and `scp` 
        to copy the directory from the origin machine to the destination machine (execution machine). 
        The `inverse` parameter determines the direction of the copy operation:
        - If `inverse` is False (default), the directory is copied from the origin to the execution machine.
        - If `inverse` is True, the directory is copied from the execution machine to the origin.

        Args:
        - ip_origin (str): The IP address of the origin machine.
        - username_origin (str): The SSH username for the origin machine.
        - password_origin (str): The SSH password for the origin machine.
        - ip_exc (str): The IP address of the execution machine (destination).
        - username_exc (str): The SSH username for the execution machine.
        - password_exc (str): The SSH password for the execution machine.
        - path_origin (str): The path of the directory on the origin machine to be copied.
        - path_exc (str): The path on the execution machine to copy the directory to.
        - inverse (bool, optional): If True, the directory is copied from the execution machine to the origin machine. Default is False.

        Returns:
        - None.

        Raises:
        - Exception: If there is an error connecting to the origin machine or executing the copy command, an exception is raised.
        """

        try:
            print(f"Connecting to {ip_origin}...", flush=True)
            c = Connection(ip_origin, username_origin, password_origin)
            if inverse:
                cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass && echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {username_exc}@{ip_exc}:{path_exc}/ {path_origin}/ && echo '{password_origin}' | sudo -S chmod -R 777 {path_origin}/{os.path.basename(os.path.normpath(path_exc))}"""
            else: 
                cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass && echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {path_origin}/ {username_exc}@{ip_exc}:{path_exc} """
                
            c.execute_ssh_command(cmd)
            #if inverse: c.execute_ssh_command(f"echo '{password_origin}' | sudo -S chmod 777 {path_origin}/{os.path.basename(os.path.normpath(path_exc))}")
            c.ssh.close()
        except Exception as e:
            print(f"Error connecting to {ip_origin}: {e}", flush=True)

    def __make_script_exc(self, taskset: list, script: str, gpu_id: int = -1) -> str:
        """ Generates a Python script to run a shell script with CPU affinity and optional GPU assignment.

        This method creates a Python script that sets CPU core affinity using the `taskset` command, and optionally sets the GPU 
        using the `CUDA_VISIBLE_DEVICES` environment variable. The script is then executed by calling the `sh` shell command. 
        The script also writes to a file named `labmonitor.status` to log the stages of the script execution process.

        Args:
        - taskset (list): A list of CPU cores to which the process should be bound (using `taskset` command).
        - script (str): The path to the shell script that should be executed.
        - gpu_id (int, optional): The ID of the GPU to assign the process. Default is -1, indicating no GPU assignment.

        Returns:
        - str: A string containing the Python script that configures and executes the shell script.
        """

        return f"""
import os
import subprocess
with open("labmonitor.status", "w") as log: log.write("started  - "+ str(os.getpid()))
if {gpu_id} == -1:
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES= taskset -c {','.join(map(str, taskset))} sh {script} > {script.split(".")[0]}.log", shell=True)
else:
    with open("{script}", "r") as file:
        original_content = file.readlines()
    with open("{script}", "w") as file:
        file.write("CUDA_VISIBLE_DEVICES={gpu_id};")
        file.writelines(original_content)
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES={gpu_id} taskset -c {','.join(map(str, taskset))} sh {script} > {script.split(".")[0]}.log", shell=True)
with open("labmonitor.status", "w") as log: 
    log.write("running - "+ str(os.getpid()))
pcs.wait()
with open("labmonitor.status", "w") as log: 
    log.write("copy_finished - "+ str(os.getpid()))"""

    def prepare_job(self, machine_name: str, taskset: list, script: str, path_exc: str, gpu_id: int = -1) -> None:
        """ Prepares a job for execution on a remote machine by creating a script (`run_labmonitor.py`) and uploading it.

        This method connects to a remote machine identified by `machine_name`, generates a Python script to run a shell 
        script with specific CPU core affinity and optional GPU assignment, and uploads the script to the remote machine. 
        The job preparation involves using the `taskset` command to bind the process to specific CPU cores and setting the 
        GPU if specified. The script is saved as `run_labmonitor.py` in the directory specified by `path_exc` on the remote machine.

        Args:
        - machine_name (str): The name of the machine where the job will be prepared. This name must exist in the `self.data.machines` DataFrame.
        - taskset (list): A list of CPU cores to which the process should be bound (using `taskset` command).
        - script (str): The path to the shell script that should be executed.
        - path_exc (str): The path on the remote machine where the Python script (`run_labmonitor.py`) will be stored.
        - gpu_id (int, optional): The ID of the GPU to assign the process. Default is -1, indicating no GPU assignment.

        Returns:
        - None

        Raises:
        - Exception: If there is an error while connecting to the machine or preparing the job, an exception is raised.
        """

        row = self.data.machines[self.data.machines['name'] == machine_name].iloc[0]
        if pd.isna(gpu_id): gpu_id = -1
        try:
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"echo '{self.__make_script_exc(taskset, script, gpu_id)}' > {path_exc}/run_labmonitor.py")
            print(f"Preparation completed in {row['ip']} - {path_exc}", flush=True)
        except Exception as e:
            print(f"Connection error when preparing work (srcipt run_labmonitor.py): {e}", flush=True)

    def get_status_job(self, machine_name: str, path_exc: str) -> tuple[str, int]:
        """ Checks the status of a job running on a remote machine.

        This method connects to a remote machine identified by `machine_name`, retrieves the job status from a file (`labmonitor.status`),
        and verifies whether the job is still running based on the PID. If the process is no longer running but the status is still marked 
        as "running", the status is updated to "not_finished_correctly". The function returns the job status and the associated 
        process ID (PID).

        Args:
        - machine_name (str): The name of the machine where the job is running. This name must exist in the `self.data.machines` DataFrame.
        - path_exc (str): The path on the remote machine where the `labmonitor.status` file is located.

        Returns:
        - tuple: A tuple containing:
        - status (str): The current status of the job. It can be "running", "not_finished_correctly", or other statuses.
        - pid (int): The process ID (PID) of the job.

        Raises:
        - Exception: If there is an error while connecting to the machine or retrieving the job status, an exception is raised.
        """

        row = self.data.machines[self.data.machines['name'] == machine_name].iloc[0]

        try:
            print(f"Checking job status in {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            status, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')

            if (not pid.strip() in con.execute_ssh_command(f"ps -p {pid.strip()}")) and (status.strip() == 'running'): 
                status = "not_finished_correctly"; con.execute_ssh_command(f"echo '{status} - {pid}' > {path_exc}/labmonitor.status")

            con.ssh.close()
            return status.strip(), int(pid)
        except Exception as e:
            print(f"Error when checking job status: {e}", flush=True)
            return "", -1

    def start_job(self, machine_name: str, path_exc: str) -> int:
        """ Starts a job on a remote machine by executing a Python script (`run_labmonitor.py`) in the specified path.

        This method connects to the remote machine identified by `machine_name`, navigates to the directory `path_exc`, and executes 
        the Python script `run_labmonitor.py` in the background using `nohup`. The function waits briefly, retrieves the process ID (PID) 
        of the running job from the `labmonitor.status` file, and returns the PID. If an error occurs, the method returns `-1`.

        Args:
        - machine_name (str): The name of the machine where the job should be started. This name must exist in the `self.data.machines` DataFrame.
        - path_exc (str): The path on the remote machine where the `run_labmonitor.py` script is located and should be executed from.

        Returns:
        - int: The PID of the job being started on the remote machine. If an error occurs, returns `-1`.

        Raises:
        - Exception: If there is an error while connecting to the machine, executing the script, or retrieving the job PID, an exception is raised.
        """

        row = self.data.machines[self.data.machines['name'] == machine_name].iloc[0]

        try:
            print(f"Starting work in {row['ip']}", flush=True)

            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            ch = con.ssh.get_transport().open_session()
            ch.exec_command(f"cd {path_exc} && nohup python3 run_labmonitor.py >  run_labmonitor.log &")

            time.sleep(0.1)
            _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split("-")

            ch.close()
            con.ssh.close()

            return int(pid)
        except Exception as e:
            print(f"Error starting work {row['ip']} {path_exc}: {e}", flush=True)
            return -1
    
    def __make_dir_exc(self, machine_exc: str, dir_exc: str) -> bool:
        """ Creates a directory on a remote machine.

        This method connects to a remote machine specified by `machine_exc` and attempts to create a directory at the path 
        specified by `dir_exc` using the `mkdir` command. If the operation is successful, it returns `True`; otherwise, 
        it returns `False` and prints an error message.

        Args:
        - machine_exc (str): The name of the machine where the directory should be created. This name must exist in the `self.data.machines` DataFrame.
        - dir_exc (str): The path to the directory that should be created on the remote machine.

        Returns:
        - bool: `True` if the directory is created successfully, otherwise `False`.

        Raises:
        - Exception: If there is an error while connecting to the machine or creating the directory, an exception is raised.
        """

        row = self.data.machines[self.data.machines['name'] == machine_exc].iloc[0]
        try:
            print(f"Connecting to {row['ip']}...", flush=True)
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"mkdir {dir_exc}")
            print(f"mkdir {dir_exc}", flush=True)
            return True
        except Exception as e:
            print(f"Error connecting to create dir_exec {row['ip']}: {e}", flush=True)
            return False

    def __get_taskset(self, machine_name: str, n_cpu: int) -> list:
        """ Retrieves a list of available CPU cores (taskset) on a specified machine.

        This function checks which CPU cores are currently occupied by running tasks on the given machine, 
        and then returns a list of unoccupied cores (taskset) that can be used for new tasks. The number of 
        cores returned is determined by the value of `n_cpu`.

        Args:
        - machine_name (str): The name of the machine for which the available CPU cores are to be retrieved. This name must exist in the `self.df` DataFrame.
        - n_cpu (int): The number of CPU cores needed. The function will return at most `n_cpu` available cores.

        Returns:
        - list: A list of available CPU core indices (taskset) that can be used for new tasks. The length of the list will be up to `n_cpu`.
        """

        result_task = []
        task = self.df.loc[(self.df['name'] == machine_name) & (self.df['status'] == 'running'), 'taskset']
        all_task = [int(num) for t in task if isinstance(t, str) for num in t.split(',')]
        available_cpu = self.data.machines.loc[self.data.machines['name'] == machine_name, 'allowed_cpu'].iloc[0]
        cpu_add = 0
        
        for t in range(int(available_cpu)):
            if not t in all_task:
                result_task.append(t)
                cpu_add += 1
                if cpu_add == n_cpu: break

        return result_task


    # Limitações usuários  
    def __limit_per_user(self, index: int, limit: int = 2) -> bool:
        """ Checks whether a user has reached the limit of concurrent running jobs.

        This function checks if the user associated with the job at the specified index has reached the 
        specified limit of running jobs. If the user is currently executing jobs that meet or exceed the 
        limit, the function will return `False`. Otherwise, it returns `True`.

        Args:
        - index (int): The index of the job in the DataFrame to check the user for. The function retrieves the user's 
        information based on the job at this index.
        - limit (int, optional): The maximum number of concurrent jobs a user is allowed to have running. Default is 2.

        Returns:
        - bool: `True` if the user has not reached the limit of concurrent jobs, `False` if the user has 
        reached or exceeded the limit.
        """

        row = self.df.loc[index]
        user_filter = self.data.users.loc[self.data.users['username'] == row['username'], ['simultaneous_jobs_limit', 'gpu_limit', 'cpu_limit']]
        user_filter_default = self.data.users.loc[self.data.users['username'] == 'default', ['simultaneous_jobs_limit', 'gpu_limit', 'cpu_limit']]

        if not user_filter.empty:
            limit = user_filter.iloc[0]['simultaneous_jobs_limit']
            gpu_limit = user_filter.iloc[0]['gpu_limit']
        elif not user_filter_default.empty:
            limit = user_filter_default.iloc[0]['simultaneous_jobs_limit']
            gpu_limit = user_filter_default.iloc[0]['gpu_limit']

        jobs_user_exc = self.df.loc[(self.df['username'] == row['username']) & (self.df['status'] == 'running'), 'username'].shape[0]
        jobs_user_gpus = self.df.loc[(self.df['username'] == row['username']) & (self.df['status'] == 'running') & (self.df['gpu_name'].notna() & (self.df['gpu_name'] != '')), 'gpu_name'].shape[0]

        if jobs_user_exc < limit: 
            if jobs_user_gpus > gpu_limit and not pd.isna(row['gpu_requested']): 
                return False
            return True
        
        else:
            return False

    def limit_job(self, index, limit_per_user: bool = True, job_limit_per_user: int = 3) -> bool:
        """ Checks whether a job can be executed based on user-defined limits.

        This function evaluates whether a job at the specified index can be executed based on the user-defined 
        limits, such as the number of concurrent jobs a user is allowed to run. If the `limit_per_user` 
        parameter is set to `True`, it checks if the user has exceeded the allowed number of concurrent jobs 
        (as specified by `job_limit_per_user`).

        Args:
        - index (int): The index of the job in the DataFrame to check the user's job limits.
        - limit_per_user (bool, optional): Whether to apply the limit on the number of concurrent jobs per user. Default is True.
        - job_limit_per_user (int, optional): The maximum number of concurrent jobs allowed for each user. Default is 3.

        Returns:
        - bool: `True` if all conditions are met (i.e., the user has not exceeded the job limit). 
        `False` if any condition fails (e.g., the user has exceeded the job limit).
        """

        res = []
        if limit_per_user:
            res.append(self.__limit_per_user(index, limit=job_limit_per_user))

        return all(res)
    

    # Ações status
    def __pending(self, index: int) -> None:
        """ Prepares and starts a job on an available machine with the required resources.

        This function checks the resource availability (CPU, GPU) on the machines, selects one with enough resources, 
        updates the job status, allocates the necessary CPUs and GPUs, creates a directory for job execution, 
        copies required files, and starts the job execution on the selected machine. It also handles job notifications 
        and updates the job-related DataFrame accordingly.

        Args:
        - index (int): The index of the job in the DataFrame to prepare and start.

        Process:
        - The function first checks if the required CPUs and GPUs are available on the machines.
        - It then selects the first available machine, updates the job's status and assigns resources.
        - A new directory is created on the selected machine for job execution, and necessary files are copied.
        - The job is then prepared for execution by generating the taskset and script, and finally started.
        - If the job has not previously been notified, an email notification is sent to the user.
        - Updates to the machine and job data are saved.

        Returns:
        - None
        """

        n_cpu = self.df.loc[index, 'n_cpu']
        gpu = not pd.isna(self.df.loc[index, 'gpu_requested'])
        if gpu:
            gpu_name = self.df.loc[index, 'gpu_requested'].split(",")
        else:
            gpu_name = ["all"]

        machines = self.search_available_machine(n_cpu=n_cpu,
                                      gpu=gpu,
                                      gpu_name=gpu_name,
                                      n_cpu_reserve=6
                                    )
        
        if machines.shape[0] > 0:
            machine = machines.iloc[0]
            self.df.loc[index, ['status']] = 'running'
            self.df.loc[index, ['ip', 'name']] = machine[['ip', 'name']]

            # pegar start e and CPU e colocar na fila
            task = self.__get_taskset(machine_name=machine['name'], n_cpu=n_cpu)
            self.df.loc[index, 'taskset'] = ",".join(map(str, task))
            #max_cpu_end = self.df.loc[(self.df['name'] == machine['name']) & (self.df['status'] == 'running'), 'cpu_end'].max()
            #self.df.loc[index, ['cpu_start', 'cpu_end']] = (max_cpu_end+1, n_cpu-1)

            #if pd.isna(self.df.loc[index, 'cpu_start']): self.df.loc[index, 'cpu_start'] = 0

            # Atualziar CPUs ocupadas nas maquinas 
            self.data.machines.loc[self.data.machines['name'] == machine['name'], 'cpu_used'] += n_cpu

            if gpu:
                # Pegar GPU e Index na fila de trabalho
                gpu_status_cols = machines.loc[0:,machines.columns.str.contains(r"gpu.*status", case=False, regex=True)].columns
                gpu_name_cols = machines.loc[0:,machines.columns.str.contains(r"gpu.*name", case=False, regex=True)].columns
                for n, s in zip(gpu_name_cols, gpu_status_cols):
                    gpu_index = n.split('_')[1]
                    if "available" == machine[s] and (machine[n] in gpu_name or "all" in gpu_name):
                        self.df.loc[index, ['gpu_name', 'gpu_index']] = (machine[n], gpu_index)
                        # Atualizar status da GPU nas maquinas
                        self.data.machines.loc[self.data.machines['name'] == machine['name'], s] = "running"
            
            # Criar pasta na maquina exc com username_datasubmit
            self.__make_dir_exc(machine_exc=machine['name'], dir_exc=f"{machine['path_exc']}/{self.df.loc[index, 'username']}_{self.df.loc[index, 'submit'].strftime('%m_%d_%Y_%I-%M-%S')}/")

            # Atualizar diretorio exc 
            self.df.loc[index, ['path_exc']] = f"{machine['path_exc']}/{self.df.loc[index, 'username']}_{self.df.loc[index, 'submit'].strftime('%m_%d_%Y_%I-%M-%S')}/{os.path.basename(os.path.normpath(self.df.loc[index, 'path_origin']))}/"
    
            # Copiar arquivos 
            data_machines_origin = Data(); data_machines_origin.read_machines()
            
            self.copy_dir(ip_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'ip'].iloc[0],
                          username_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'username'].iloc[0],
                          password_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'password'].iloc[0],
                          path_origin=self.df.loc[index, 'path_origin'],
                          
                          ip_exc=self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'ip'].iloc[0],
                          username_exc=self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'username'].iloc[0],
                          password_exc=self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'password'].iloc[0],
                          path_exc=self.df.loc[index, 'path_exc']
                          )

            # Iniciar trabalho
            self.prepare_job(machine_name=machine['name'], 
                            taskset=task,
                            script=self.df.loc[index, 'script_name'],
                            path_exc=self.df.loc[index, 'path_exc'],
                            gpu_id=self.df.loc[index, 'gpu_index']
                            )

            pid = self.start_job(machine_name=machine['name'], path_exc=self.df.loc[index, 'path_exc'])
            self.df.loc[index, ['pid']] = pid
            self.df.loc[index, ['inicio']] = datetime.now()

            if self.df.loc[index, 'notification_start'] == "N":
                if self.__send_mail(subject=f"His work began {self.df.loc[index, 'job_name']} | LMDM",
                                message=self.__make_email_html(df_row=self.df.loc[index],
                                                                title="Inicio do trabalho",                                                            
                                                                ),
                                to=self.df.loc[index, 'e-mail'],
                                subtype="html"):
                    self.df.loc[index, 'notification_start'] = "Y"
            
            self.data.save_machines() 
            self.save()
            
    def __copy_finished(self, index: int) -> None:
        """ Method responsible for finalizing the job execution process after copying files between machines.

        Method responsible for finalizing the file copy between machines after a job execution.
        Updates the job status and manages the copy process.

        Args:
        - index (int): The index of the row in the DataFrame that contains job and machine information.
        """

        def subp_copy() -> None:
            """  Internal function that performs copy operations and status updates in a separate thread.

            Args:
            - None.

            Returns:
            - None.
            """

            data_machines_origin = Data(); data_machines_origin.read_machines()
            ip_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'ip'].iloc[0]
            username_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'username'].iloc[0]
            password_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'password'].iloc[0]
            path_exc = self.df.loc[index, 'path_exc']
            copiar = False
            copiado = False

            try:
                print(f"Updating copying status {ip_exc}", flush=True)
                con = Connection(ip=ip_exc,
                                username=username_exc, 
                                password=password_exc)
                
                _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')
                con.execute_ssh_command(f"echo 'copying - {pid}' > {path_exc}/labmonitor.status")
                con.ssh.close()
                self.df.loc[index, ['status']] = 'copying'; self.save()
                copiar = True
            except Exception as e:
                print(f"Error when updating job status for copying: {e}", flush=True)

            if copiar:
                try:
                    self.copy_dir(
                        ip_origin = data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'ip'].iloc[0],
                        username_origin = data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'username'].iloc[0],
                        password_origin = data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'password'].iloc[0],
                        path_origin = self.df.loc[index, 'path_origin'],
                        ip_exc = ip_exc,
                        username_exc = username_exc,
                        password_exc = password_exc,
                        path_exc = path_exc,
                        inverse = True
                    )
                    copiado = True
                    
                except Exception as e:
                    print(f'Error copying files from exc to origin {ip_exc}: {e}', flush=True)
            
            if copiado:
                cmd = f"echo 'finished - {pid}' > {path_exc}/labmonitor.status"
                self.read_csv()
                self.df.loc[index, ['status']] = 'finished'; self.save()
                self.__finished(index)
                
            else:
                self.read_csv()
                cmd = f"echo 'copy_fail - {pid}' > {path_exc}/labmonitor.status"
                self.df.loc[index, ['status']] = 'copy_fail'; self.save()
            try:
                print(f"Updating final copy status (copy_fail or finished - {copiado}) {ip_exc}", flush=True)
                con = Connection(ip=ip_exc,
                                username=username_exc, 
                                password=password_exc)
                con.execute_ssh_command(cmd)
                con.ssh.close()
            except Exception as e:
                print(f"Error when updating job status to finished: {e}", flush=True)          

        proc = threading.Thread(target=subp_copy)
        proc.start()
        
    def view_job_log(self, job_row:pd.Series, sufix: str = ".log") -> dict:
        """ Retrieves and displays the latest logs from a remote machine associated with a job.

        This method connects to the target machine via SSH, fetches the most recent log lines, 
        and parses the logs into a dictionary where the log file name is the key and the content is the value.

        Args:
        - job_row (pd.Series): A row from the DataFrame containing information about the job.
        - sufix (str): The suffix (file extension) of the log files to be retrieved. Default is ".log".

        Returns:
        - dict: A dictionary where the keys are log file names and the values are the corresponding log contents.
        """

        machine = self.data.machines[self.data.machines['name'] == job_row['name']].iloc[0]

        try:
            print(f"Connecting to {machine['ip']}...", flush=True)
            con = Connection(ip=machine['ip'], username=machine['username'], password=machine['password'])
            out = con.execute_ssh_command(f"tail -v -n 30 {job_row['path_exc']}/*{sufix}")
            r = {}
            logs = out.split("==>")
            for log in logs:
                l = log.split("<==") + ["", ""]
                r.update({l[0].split('/')[-1]: l[1]})
            del r['']
            return r 

        except Exception as e:
            print(f"Error when connecting to read logs {machine['ip']}: {e}", flush=True)
            return {"":""}

    def __running(self, index: int) -> None:
        """ Method to monitor the execution status of a job and update the job status accordingly.
        
        This method checks the status of a job running on a remote machine and updates the job status based on the current state.
        
        Args:
        - index (int): The index of the job in the DataFrame to monitor and update.
        
        Returns:
        - None
        """

        pass

    def __finished(self, index: int) -> None:
        """ Sends a notification email to the user when their job is completed successfully.

        This method triggers an email containing the completion message and updates the job's status.

        Args:
        - index (int): The index of the job in the DataFrame, indicating which job has finished.

        Returns:
        - None
        """
        
        def send() -> None:
            """ Handles sending the completion notification email.

            This inner function sends an email to inform the user that their job has been completed successfully. 
            The email contains a message indicating that the job has finished correctly and that the files have been 
            copied back to the origin directory. The function then updates the job status and saves the changes to the DataFrame.

            Args:
            - None

            Returns:
            - None
            """

            if self.df.loc[index, 'notification_end'] == "N":
                obs = """
                Your work has been finished correctly.  
                The files have been copied to their original directory."""

                if self.__send_mail(
                            subject = f"Job finished - {self.df.loc[index, 'job_name']} | LMDM",
                            message = self.__make_email_html(df_row = self.df.loc[index], observation = obs),
                            subtype = "html",
                            to = self.df.loc[index, 'e-mail'],
                        ):
                    
                    self.df.loc[index, 'notification_end'] = "Y"

        send()
        self.df.loc[index, ['fim']] = datetime.now()
        self.save()


    def __not_finished_correctly(self, index: int) -> None:
        """ Notifies the user when their job was not completed correctly.

        This method sends an email to inform the user about the possible failure reasons, updates the job's 
        status to "not_finished_correctly", and attempts to copy the necessary files back to the origin.

        Args:
        - index (int): The index of the job in the DataFrame, indicating which job experienced an issue.

        Returns:
        - None
        """

        def send() -> None:
            """ Handles sending the failure notification email.

            This inner function sends an email to inform the user about the failure and provides suggestions for re-submission. 
            The job status is then updated, and the files are copied back to the origin directory.

            Args:
            - None

            Returns:
            - None
            """

            if self.df.loc[index, 'notification_end'] == "N":
                obs = """
                Your work has not been finished properly.  
                The failure may have been due to using more resources than requested (CPU or GPU), an error in your execution script or the machine shutting down. 
                The files have been copied to their source directory, check and resubmit to the queue. 
                If possible, use the data produced to restart the work."""

                if self.__send_mail(
                            subject = f"Work not finished properly - {self.df.loc[index, 'job_name']} | LMDM",
                            message = self.__make_email_html(df_row = self.df.loc[index], observation = obs),
                            subtype = "html",
                            to = self.df.loc[index, 'e-mail'],
                        ):
                    self.df.loc[index, 'notification_end'] = "Y"
                
                self.__copy_finished(index)
                self.read_csv()
                self.df.loc[index, 'status'] = "not_finished_correctly" 
                
        send()
        self.df.loc[index, ['fim']] = datetime.now()
        self.save()
        
 
    def __copying(self, index) -> None:
        pass

    def __copy_fail(self, index) -> None:
        pass

    def __started(self, index) -> None:
        pass

    def __nenhum(self, index) -> None:
        pass

    def __monitor_now(self) -> None:
        """ Monitors the current status of all jobs and machines.

        This method updates the status of the jobs based on their current state and performs the appropriate actions for each job. 
        It maps actions to different job statuses, such as 'pending', 'copy_finished', 'running', etc. The method also reads 
        job data from the csv file, updates machine and job statuses, and iterates through all jobs to apply the relevant action 
        based on their status. It ensures that only jobs meeting the job limits are processed.

        Actions for each job status:
        - 'pending': Calls the __pending method.
        - 'copy_finished': Calls the __copy_finished method.
        - 'running': Calls the __running method.
        - 'finished': Calls the __finished method.
        - 'not_finished_correctly': Calls the __not_finished_correctly method.
        - 'copying': Calls the __copying method.
        - 'copy_fail': Calls the __copy_fail method.
        - 'started': Calls the __started method.
        - '': Calls the __nenhum method (for empty or undefined statuses).

        This method is designed to monitor the status of jobs and execute corresponding actions based on the job's state.

        Args:
        - None

        Returns:
        - None
        """

        action = {'pending': self.__pending, 
                  "copy_finished": self.__copy_finished,
                  "running": self.__running, 
                  "finished": self.__finished, 
                  "not_finished_correctly": self.__not_finished_correctly,
                  "copying":self.__copying,
                  "copy_fail": self.__copy_fail,
                  "started": self.__started,
                  "": self.__nenhum
                  }
        
        try: self.data.read_users()
        except Exception as e: print(f"Error updating user limits: {e}", flush=True)

        try: self.read_csv()
        except Exception as e: print(f"Error updating data jobs:", flush=True)

        try: self.update_status_machines()
        except Exception as e: print(f"Error updating status_machines: {e}",  flush=True)
        
        try: self.update_status_jobs()
        except Exception as e: print(f"Error updating jobs: {e}",  flush=True)

        print(self.df, flush=True)
        
        for i, row in self.df.iterrows():
            if not self.limit_job(index=i): continue
            action[row['status']](index=i)

    def monitor(self, feq_time: int = 300, now: bool = False) -> None:
        """ Monitors jobs and machines periodically or immediately based on the provided parameters.

        This method continuously checks the status of the jobs and machines at regular intervals if the `now` flag is False. 
        If `now` is set to True, it monitors the jobs and machines immediately without waiting.

        Args:
        - feq_time (int): The frequency in seconds (default: 300). Defines how often the monitor should run when `now` is False.
        - now (bool): A flag to determine whether to monitor immediately (`True`) or at regular intervals (`False`).

        Returns:
        - None

        Behavior:
        - When `now` is False:
        - The method prints the start and end time of each monitoring cycle.
        - After each monitoring cycle, it waits for the specified `feq_time` before repeating the process.
        - When `now` is True:
        - The method performs one immediate monitoring cycle without waiting.

        This method executes the monitoring process (via `__monitor_now`), either in an infinite loop (when `now=False`) or once (when `now=True`).
        """

        while not now:
            print(f"Monitoring the start: {datetime.now()}", flush=True)

            self.__monitor_now()
            
            print(f"Monitoring end: {datetime.now()}", flush=True)
            time.sleep(feq_time)
        else:
            self.__monitor_now()

    def __head_mail(self) -> str:
        """ Generates the HTML header for the email content.

        This method generates the HTML header content for the email message, including the CSS styles for the email layout.

        Args:
        - None

        Returns:
        - str: The HTML content for the email header.
        """

        return """<head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header {
                    background-color: #A8D08D; /* verde claro */
                    color: white;
                    padding: 10px 0;
                    text-align: center;
                }
                .container {
                    margin: 20px;
                }
                .table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                .table th, .table td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                .table th {
                    background-color: #f2f2f2;
                }
                .footer {
                    margin-top: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }
            </style>
            <div class="header">
                <span style="font-size: 24px; font-weight: bold; margin-left: 10px;">Laboratório de Modelagem e Dinâmica Molecular</span>
            </div>
        </head>"""

    def __footer_mail(self) -> str:
        """ Generates the HTML footer for the email content.

        This method generates the HTML footer content for the email message, including a disclaimer about automated emails.

        Args:
        - None

        Returns:
        - str: The HTML content for the email footer.
        """

        return """<div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
        </div>"""

    def __make_email_html(self, df_row: pd.Series, title: str = "Agendamento", observation: str = "") -> str:
        """ Generates an HTML email message for a job based on the information in the DataFrame row.

        This method creates an HTML email message with the job details, such as machine name, user, status,
        submission date, end date, CPU and GPU information, and any additional observations provided.

        Args:
        - df_row (pd.Series): A row from the DataFrame containing information about the job.
        - title (str): The title of the email message. Default is "Agendamento".
        - observation (str): Additional observations or notes to include in the email message. Default is an empty string.

        Returns:
        - str: The HTML content for the email message.
        """

        return f"""<html>
        {self.__head_mail()}
        <body>
            <div class="container">
                <h2>{title}</h2>
                <table class="table">
                    <tr>
                        <th>Máquina</th>
                        <td>{df_row['name']}</td>
                    </tr>
                    <tr>
                        <th>Usuário</th>
                        <td>{df_row['username']}</td>
                    </tr>
                    <tr>
                        <th>Status</th>
                        <td>{df_row['status']}</td>
                    </tr>
                    <tr>
                        <th>Data de submissão</th>
                        <td>{df_row['submit']}</td>
                    </tr>
                    <tr>
                        <th>Fim</th>
                        <td>{df_row['fim']}</td>
                    </tr>
                    <tr>
                        <th>CPU</th>
                        <td>{df_row['n_cpu']}</td>
                    </tr>
                    <tr>
                        <th>GPU</th>
                        <td>{df_row['gpu_name']} (Índice {df_row['gpu_index']})</td>
                    </tr>
                </table>
                {f'''
                <div class="observation">
                    <h3>Observações</h3>
                    <p>{observation}</p>
                </div>
                ''' if observation else ''}
            </div>
        {self.__footer_mail()}
        </body>
    </html>"""

    def __send_mail(self, subject: str, message: str, to: str, subtype: str = "plain") -> bool:
        """ Sends an email to the specified recipient with the given subject and message content.

        This method creates an email message and sends it using SMTP through a Gmail server. It uses the credentials stored in `self.data.email` 
        for authentication and sends the email in the specified format (`plain` or `html`).

        Args:
        - subject (str): The subject of the email.
        - message (str): The body content of the email.
        - to (str): The recipient's email address.
        - subtype (str): The subtype of the email content. Default is "plain". Can also be "html" to send an HTML formatted email.

        Returns:
        - bool: Returns `True` if the email was successfully sent, `False` if there was an error.

        This method uses Gmail's SMTP server (`smtp.gmail.com`) on port 587 for sending the email, and it requires a valid Gmail account password. 
        You should generate an app-specific password for this purpose if 2-step verification is enabled on your Gmail account.
        """

        try:
            msg = MIMEMultipart()
            # setup the parameters of the message
            self.data.read_email()
            password = self.data.email['password'] # a senha tem que ser gerada https://www.emailsupport.us/blog/gmail-smtp-not-working/
            msg['From'] = self.data.email['address'] 
            msg['To'] = to
            msg['Subject'] = subject
            
            # add in the message body
            msg.attach(MIMEText(message, subtype))
            
            #create server
            server = smtplib.SMTP('smtp.gmail.com: 587')
            
            server.starttls()
            
            # Login Credentials for sending the mail
            server.login(msg['From'], password)
        
            # send the message via the server.
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
            print (f"Successfully sent email {to}", flush=True)
            return True
        except Exception as e: 
            print(f"Error sending e-mail: {e}", flush=True)
            return False
