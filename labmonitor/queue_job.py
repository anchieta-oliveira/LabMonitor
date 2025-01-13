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



class QueueJob:
    """
    Class that manages job queue information and interacts with data regarding machine configurations 
    and job submissions. It allows reading job data from an Excel file, managing job states, and interacting 
    with the machine configurations to update job status.

    Attributes:
    - df (pd.DataFrame): DataFrame containing the job queue information, read from the specified Excel file.
    - path (str): The path to the Excel file containing the queue job data (default: 'queue_job.xlsx').
    - data (Data): The data object containing machine and email configurations.
    - machines (pd.DataFrame): DataFrame containing machine configurations from `data.machines`.

    Methods:
    - __init__(self, data:Data, path:str="queue_job.xlsx"): Constructor for initializing the QueueJob object.
    - read_excel(self, path:str) -> pd.DataFrame: Reads job queue data from an Excel file and returns it as a DataFrame.
    """
    def __init__(self, data:Data, path:str="queue_job.xlsx"):
        self.df = self.read_excel(path)
        self.path = path
        self.data = data
        self.machines = data.machines

    def read_excel(self, path:str="queue_job.xlsx") -> pd.DataFrame:
        """
        Reads an Excel file and processes its contents into a DataFrame.
        
        Parameters:
        - path (str): The file path to the Excel file. Defaults to "queue_job.xlsx".
        
        Returns:
        - pd.DataFrame: A DataFrame containing the contents of the Excel file.
        
        Behavior:
        - If the file specified by `path` exists, it reads the file into a DataFrame.
        - Converts the 'fim' and 'inicio' columns to datetime objects for proper handling of date and time data.
        - If the file does not exist, it resets the DataFrame using the `reset` method.
        """
        if os.path.exists(path):
            self.df = pd.read_excel(path)
            self.df['fim'] = self.df['fim'] = pd.to_datetime(self.df['fim'])
            self.df['inicio'] = self.df['inicio'] = pd.to_datetime(self.df['inicio'])
        else:
            self.reset()
        return self.df

    def save(self):
        """
        Saves the current DataFrame to an Excel file.
        
        Behavior:
        - Writes the contents of the DataFrame `self.df` to an Excel file specified by `self.path`.
        - The file is saved without including the index.
        """
        self.df.to_excel(self.path, index=False)

    def reset(self) -> pd.DataFrame:
        """
        Resets the DataFrame to a default structure and saves it to an Excel file.
        
        Returns:
        - pd.DataFrame: A new DataFrame with predefined columns and no data.
        
        Behavior:
        - Initializes a new DataFrame with a specified set of columns, representing job information and metadata.
        - Saves the newly created empty DataFrame to an Excel file named "queue_job.xlsx" without including the index.
        - Returns the new empty DataFrame.
        """
        columns = ["ip", "name", "username", "job_name", "status", "pid", "path_exc", "path_origin", "machine_origin", "script_name", "submit", "inicio", "fim", "n_cpu", "taskset", "gpu_requested", "gpu_name", "gpu_index", "e-mail", "notification_start", "notification_end"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_excel("queue_job.xlsx", index=False)
        return self.df
    

    def submit(self, username:str, job_name:str, machine_origin:str, script_name:str, path_origin:str, n_cpu:int, email:str, gpus:list=['all']):
        """
        Submits a new job by adding its details to the DataFrame and saving the updated DataFrame to an Excel file.

        Parameters:
        - username (str): The username of the individual submitting the job.
        - job_name (str): The name of the job being submitted.
        - machine_origin (str): The origin machine from where the job is submitted.
        - script_name (str): The name of the script associated with the job.
        - path_origin (str): The origin path of the job's script.
        - n_cpu (int): The number of CPUs requested for the job.
        - email (str): The email address for job notifications.
        - gpus (list): A list of GPUs requested for the job, defaults to `['all']`.

        Behavior:
        - Creates a dictionary with the job details, including the current timestamp as the submission time.
        - Converts the list of GPUs into a comma-separated string.
        - Adds the new job to the DataFrame.
        - Saves the updated DataFrame to an Excel file using the `save` method.
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

        self.df = pd.concat([self.df, pd.DataFrame([new_job])], ignore_index=True)
        self.save()
        print(self.df)

    

    def update_gpu(self):
        """
        Updates the GPU information for each machine listed in the 'machines' DataFrame.

        This method connects to each machine, retrieves the GPU usage statistics, and updates
        the 'machines' DataFrame with the latest GPU information. It then saves the updated 
        DataFrame to ensure the information is persistent.
        """
        def run(ip, name, user, pw):
            try:
                print(f"Conectando a {ip}...")
                results = {}
                c = Connection(ip, user, pw)
                m = Monitor(c)
            except Exception as e:
                print(f"Erro ao conectar a {ip}: {e}")
                return name, None
            try:
                results.update(m.get_usage_gpu())
            except Exception as e:
                results.update({"gpu_info": []})
                print(f"Erro ao obter informações de GPU de {ip}: {e}")
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

    def __allowed_gpu(self):
        """
        Updates the GPU status for each machine based on the allowed GPUs.

        This method checks which GPUs are allowed for each machine and updates their status 
        to 'disponivel' (available) if they match the allowed GPU names. If a GPU does not match
        or is not listed, its status is set to 'bloqueada' (blocked).

        The allowed GPU names are specified in the 'name_allowed_gpu' column, while the GPU names
        and their statuses are updated in corresponding columns in the 'machines' DataFrame.
        """
        g_names = [e.split(",") for e in self.data.machines['name_allowed_gpu'].to_list()]
        col = self.data.machines.loc[:, self.data.machines.columns.str.contains(r"gpu_.*_name", case=False, regex=True)]

        for i, row in self.data.machines.iterrows():
            for c in col:
                for name in g_names[i]:
                    if name == self.data.machines[c].iloc[i]:
                        self.data.machines.loc[i, c.replace("Name", "status")] = "disponivel"
                    elif name != self.data.machines[c].iloc[i]: 
                        self.data.machines.loc[i, c.replace("Name", "status")] = "bloqueada"
                    elif pd.isna(self.data.machines[c].iloc[i]):
                        self.data.machines.loc[i, c.replace("Name", "status")] = "bloqueada"


    def __status_in_queue(self):
        """
        Updates the status of GPUs in the machines DataFrame to 'executando' (executing) for jobs that are currently running.

        This method checks the DataFrame for jobs with a status of 'executando' and updates the corresponding GPU status
        in the machines DataFrame. If the 'gpu_index' is NaN for any job, it is set to 0 by default.
        """
        v = self.df[self.df['status'] == "executando"]
        for i, maq in v.iterrows():
            if pd.isna(maq['gpu_index']): self.df.loc[i, ['gpu_index']] = 0; maq['gpu_index'] = 0
            self.data.machines.loc[
                    (self.data.machines['name'] == maq['name']) & 
                    (self.data.machines['ip'] == maq['ip']) & 
                    (self.data.machines[f"GPU_{int(maq['gpu_index'])}_Name"] == maq['gpu_name']),
                    f"GPU_{int(maq['gpu_index'])}_status"
                ] = "executando"
     

    def __update_cpu_used(self):
        """
        Updates the 'cpu_used' column in the machines DataFrame based on the number of CPUs allocated
        to currently running jobs.

        This method resets the 'cpu_used' column to 0 and then iterates over the jobs with the status
        'executando', incrementing the 'cpu_used' count for each corresponding machine.
        """
        v = self.df[self.df['status'] == "executando"]
        self.data.machines.loc[:,'cpu_used'] = 0
        for i, maq in v.iterrows():
            self.data.machines.loc[
                    (self.data.machines['name'] == maq['name']) & 
                    (self.data.machines['ip'] == maq['ip']),
                    "cpu_used"
                ] += maq['n_cpu']


    def update_status_machines(self):
        """
        Updates the status of machines by reading machine data, updating GPU and CPU usage,
        and modifying the job status for each machine.

        This method:
        - Reads the current machine data from a specified file.
        - Updates GPU status using the `update_gpu` method.
        - Updates the allowed GPU status with the `__allowed_gpu` method.
        - Updates CPU usage based on currently executing jobs using the `__update_cpu_used` method.
        - Updates the job status in the queue with the `__status_in_queue` method.
        - Saves the updated machine data to the specified path.
        """
        self.data.read_machines(self.data.path_machines)
        self.update_gpu()
        self.__allowed_gpu()
        self.__update_cpu_used()
        self.__status_in_queue()
        self.data.save_machines()


    def search_available_machine(self, n_cpu:int, gpu:bool = False, gpu_name:list = ["all"], cpu_reserve:bool=True, n_cpu_reserve:int=0):
        """
        Searches for available machines based on CPU and GPU requirements. Filters machines with:
        - Sufficient available CPU considering possible reservations.
        - Optional GPU requirements, including the ability to filter by GPU names.
        
        Parameters:
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

        else: available_cpu = self.data.machines.loc[(((self.data.machines['allowed_cpu']) - self.data.machines['cpu_used']) >= n_cpu)]

        if gpu:
            if cpu_reserve and n_cpu_reserve >= n_cpu: available_cpu = self.data.machines.loc[(((self.data.machines['allowed_cpu']) - self.data.machines['cpu_used']) >= n_cpu)]

            gpu_status_cols = self.data.machines.loc[:,self.data.machines.columns.str.contains(r"gpu.*status", case=False, regex=True)].columns
            gpu_name_cols = self.data.machines.loc[:,self.data.machines.columns.str.contains(r"gpu.*name", case=False, regex=True)].columns
            
            gpu_status_available = self.data.machines[gpu_status_cols].eq("disponivel").any(axis=1)

            if gpu_name[0] != "all": gpu_name_match = self.data.machines[gpu_name_cols].isin(gpu_name).any(axis=1) 
            else: gpu_name_match = self.data.machines[gpu_name_cols].any(axis=1) 
            
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



    def update_status_jobs(self):
        """
        Updates the status and PID of jobs in the DataFrame.

        For each job in the `self.df` DataFrame:
        - If the status is 'executing', the `get_status_job` method is called to fetch the updated status and PID.
        - If the status is missing (NaN), it is set to 'waiting'.
        
        After the updates, the changes are saved by calling the `save` method.

        This function modifies the `self.df` DataFrame directly and does not return any value.

        Parameters:
        ----------
        None.

        Returns:
        --------
        None.
        """
        for i, job in self.df.iterrows():
            if job['status'] == 'executando': self.df.loc[i, ['status', 'pid']] = self.get_status_job(job['name'], job['path_exc'])
            if pd.isna(job['status']): self.df.loc[i, ['status']] = 'esperando'
        self.save()


    def copy_dir(self, ip_origin, username_origin, password_origin, ip_exc, username_exc, password_exc, path_origin:str, path_exc:str, inverse:bool = False):
        """
        Copies a directory between two remote machines using SCP, with an optional inverse operation.

        This method connects to a source machine (origin) via SSH, and then uses `sshpass` and `scp` 
        to copy the directory from the origin machine to the destination machine (execution machine). 
        The `inverse` parameter determines the direction of the copy operation:
        - If `inverse` is False (default), the directory is copied from the origin to the execution machine.
        - If `inverse` is True, the directory is copied from the execution machine to the origin.

        Parameters:
        -----------
        ip_origin : str
            The IP address of the origin machine.
        
        username_origin : str
            The SSH username for the origin machine.
        
        password_origin : str
            The SSH password for the origin machine.
        
        ip_exc : str
            The IP address of the execution machine (destination).
        
        username_exc : str
            The SSH username for the execution machine.
        
        password_exc : str
            The SSH password for the execution machine.
        
        path_origin : str
            The path of the directory on the origin machine to be copied.
        
        path_exc : str
            The path on the execution machine to copy the directory to.
        
        inverse : bool, optional
            If True, the directory is copied from the execution machine to the origin machine. Default is False.

        Returns:
        --------
        None.

        Raises:
        ------
        Exception
            If there is an error connecting to the origin machine or executing the copy command, an exception is raised.
        """
        try:
            print(f"Conectando a {ip_origin}...")
            c = Connection(ip_origin, username_origin, password_origin)
            if inverse: cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass && echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {username_exc}@{ip_exc}:{path_exc}/ {path_origin}/ && echo '{password_origin}' | sudo -S chmod -R 777 {path_origin}/{os.path.basename(os.path.normpath(path_exc))}"""
            else: cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass && echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {path_origin}/ {username_exc}@{ip_exc}:{path_exc} """
                
            c.execute_ssh_command(cmd)
            #if inverse: c.execute_ssh_command(f"echo '{password_origin}' | sudo -S chmod 777 {path_origin}/{os.path.basename(os.path.normpath(path_exc))}")
            c.ssh.close()
        except Exception as e:
            print(f"Erro ao conectar a {ip_origin}: {e}")

        
        
    def __make_script_exc(self, taskset:list, script:str, gpu_id:int=-1):
        """
        Generates a Python script that runs a shell script with specific CPU core affinity and optional GPU assignment.

        This method creates a Python script that sets CPU core affinity using the `taskset` command, and optionally sets the GPU 
        using the `CUDA_VISIBLE_DEVICES` environment variable. The script is then executed by calling the `sh` shell command. 
        The script also writes to a file named `labmonitor.status` to log the stages of the script execution process.

        Parameters:
        -----------
        taskset : list
            A list of CPU cores to which the process should be bound (using `taskset` command).
        
        script : str
            The path to the shell script that should be executed.

        gpu_id : int, optional
            The ID of the GPU to assign the process. Default is -1, indicating no GPU assignment.

        Returns:
        --------
        str
            A string containing the Python script that configures and executes the shell script.

        Example:
        --------
        taskset = [0, 1, 2, 3]
        script = "my_script.sh"
        gpu_id = 0
        generated_script = self.__make_script_exc(taskset, script, gpu_id)
        print(generated_script)
        """
        return f"""
import os
import subprocess
with open("labmonitor.status", "w") as log: log.write("iniciado  - "+ str(os.getpid()))
if {gpu_id} == -1:
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES= taskset -c {','.join(map(str, taskset))} sh {script} > {script.split(".")[0]}.log", shell=True)
else:
    with open("{script}", "r") as file: original_content = file.readlines()
    with open("{script}", "w") as file: file.write("CUDA_VISIBLE_DEVICES={gpu_id};"); file.writelines(original_content)
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES={gpu_id} taskset -c {','.join(map(str, taskset))} sh {script} > {script.split(".")[0]}.log", shell=True)
with open("labmonitor.status", "w") as log: log.write("executando - "+ str(os.getpid()))
pcs.wait()
with open("labmonitor.status", "w") as log: log.write("finalizado_copiar - "+ str(os.getpid()))"""
    

    def prepare_job(self, machine_name:str, taskset:list, script:str, path_exc:str, gpu_id:int=-1):
        """
        Prepares a job for execution on a remote machine by creating a script (`run_labmonitor.py`) and uploading it.

        This method connects to a remote machine identified by `machine_name`, generates a Python script to run a shell 
        script with specific CPU core affinity and optional GPU assignment, and uploads the script to the remote machine. 
        The job preparation involves using the `taskset` command to bind the process to specific CPU cores and setting the 
        GPU if specified. The script is saved as `run_labmonitor.py` in the directory specified by `path_exc` on the remote machine.

        Parameters:
        -----------
        machine_name : str
            The name of the machine where the job will be prepared. This name must exist in the `self.data.machines` DataFrame.
        
        taskset : list
            A list of CPU cores to which the process should be bound (using `taskset` command).
        
        script : str
            The path to the shell script that should be executed.
        
        path_exc : str
            The path on the remote machine where the Python script (`run_labmonitor.py`) will be stored.

        gpu_id : int, optional
            The ID of the GPU to assign the process. Default is -1, indicating no GPU assignment.

        Raises:
        -------
        Exception
            If there is an error while connecting to the machine or preparing the job, an exception is raised.
        """
        row = self.data.machines[self.data.machines['name'] == machine_name].iloc[0]
        if pd.isna(gpu_id): gpu_id = -1
        try:
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"echo '{self.__make_script_exc(taskset, script, gpu_id)}' > {path_exc}/run_labmonitor.py")
            print(f"Preparação concluída em {row['ip']} - {path_exc}")
        except Exception as e:
            print(f"Erro na conexão ao preparar trabalho (srcipt run_labmonitor.py): {e}")


    def get_status_job(self, machine_name:str, path_exc:str):
        """
        Checks the status of a job running on a remote machine.

        This method connects to a remote machine identified by `machine_name`, retrieves the job status from a file (`labmonitor.status`),
        and verifies whether the job is still running based on the PID. If the process is no longer running but the status is still marked 
        as "executando", the status is updated to "nao_finalizado_corretamente". The function returns the job status and the associated 
        process ID (PID).

        Parameters:
        -----------
        machine_name : str
            The name of the machine where the job is running. This name must exist in the `self.data.machines` DataFrame.
        
        path_exc : str
            The path on the remote machine where the `labmonitor.status` file is located.

        Returns:
        --------
        tuple:
            A tuple containing:
            - status (str): The current status of the job. It can be "executando", "nao_finalizado_corretamente", or other statuses.
            - pid (int): The process ID (PID) of the job.

        Raises:
        -------
        Exception:
            If there is an error while connecting to the machine or retrieving the job status, an exception is raised.
        """
        row = self.data.machines[self.data.machines['name'] == machine_name].iloc[0]
        try:
            print(f"Verificando status do job em {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            status, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')
            if (not pid.strip() in con.execute_ssh_command(f"ps -p {pid.strip()}")) and (status.strip() == 'executando'): status = "nao_finalizado_corretamente"; con.execute_ssh_command(f"echo '{status} - {pid}' > {path_exc}/labmonitor.status")
            con.ssh.close()
            return status.strip(), int(pid)
        except Exception as e:
            print(f"Erro ao verificar status do job: {e}")
            return "", -1


    def star_job(self, machine_name:str, path_exc:str)  -> int:
        """
        Starts a job on a remote machine by executing a Python script (`run_labmonitor.py`) in the specified path.

        This method connects to the remote machine identified by `machine_name`, navigates to the directory `path_exc`, and executes 
        the Python script `run_labmonitor.py` in the background using `nohup`. The function waits briefly, retrieves the process ID (PID) 
        of the running job from the `labmonitor.status` file, and returns the PID. If an error occurs, the method returns `-1`.

        Parameters:
        -----------
        machine_name : str
            The name of the machine where the job should be started. This name must exist in the `self.data.machines` DataFrame.

        path_exc : str
            The path on the remote machine where the `run_labmonitor.py` script is located and should be executed from.

        Returns:
        --------
        int:
            The PID of the job being started on the remote machine. If an error occurs, returns `-1`.

        Raises:
        -------
        Exception:
            If there is an error while connecting to the machine, executing the script, or retrieving the job PID, an exception is raised.
        """
        row = self.data.machines[self.data.machines['name'] == machine_name].iloc[0]
        try:
            print(f"Iniciando trabalho em {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            ch = con.ssh.get_transport().open_session()
            ch.exec_command(f"cd {path_exc} && nohup python3 run_labmonitor.py >  run_labmonitor.log &")
            time.sleep(0.1)
            _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split("-")
            ch.close()
            con.ssh.close()
            return int(pid)
        except Exception as e:
            print(f"Erro a iniciar trabalho {row['ip']} {path_exc}: {e}")
            return -1
    

    def __make_dir_exc(self, machine_exc:str, dir_exc:str):
        """
        Creates a directory on a remote machine.

        This method connects to a remote machine specified by `machine_exc` and attempts to create a directory at the path 
        specified by `dir_exc` using the `mkdir` command. If the operation is successful, it returns `True`; otherwise, 
        it returns `False` and prints an error message.

        Parameters:
        -----------
        machine_exc : str
            The name of the machine where the directory should be created. This name must exist in the `self.data.machines` DataFrame.

        dir_exc : str
            The path to the directory that should be created on the remote machine.

        Returns:
        --------
        bool:
            `True` if the directory is created successfully, otherwise `False`.

        Raises:
        -------
        Exception:
            If there is an error while connecting to the machine or creating the directory, an exception is raised.
        """
        row = self.data.machines[self.data.machines['name'] == machine_exc].iloc[0]
        try:
            print(f"Conectando a {row['ip']}...")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"mkdir {dir_exc}")
            print(f"mkdir {dir_exc}")
            return True
        except Exception as e:
            print(f"Erro ao conectar a para criar dir_exec {row['ip']}: {e}")
            return False
    

    def __get_taskset(self, machine_name:str, n_cpu:int):
        """
        Retrieves a list of available CPU cores (taskset) on a specified machine.

        This function checks which CPU cores are currently occupied by running tasks on the given machine, 
        and then returns a list of unoccupied cores (taskset) that can be used for new tasks. The number of 
        cores returned is determined by the value of `n_cpu`.

        Parameters:
        -----------
        machine_name : str
            The name of the machine for which the available CPU cores are to be retrieved. This name must exist 
            in the `self.df` DataFrame.

        n_cpu : int
            The number of CPU cores needed. The function will return at most `n_cpu` available cores.

        Returns:
        --------
        list:
            A list of available CPU core indices (taskset) that can be used for new tasks. The length of the list 
            will be up to `n_cpu`.
        """
        result_task = []
        task = self.df.loc[(self.df['name'] == machine_name) & (self.df['status'] == 'executando'), 'taskset']
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
    def __limit_per_user(self, index:int, limit:int=2) -> bool:
        """
        Checks whether a user has reached the limit of concurrent running jobs.

        This function checks if the user associated with the job at the specified index has reached the 
        specified limit of running jobs. If the user is currently executing jobs that meet or exceed the 
        limit, the function will return `False`. Otherwise, it returns `True`.

        Parameters:
        -----------
        index : int
            The index of the job in the DataFrame to check the user for. The function retrieves the user's 
            information based on the job at this index.

        limit : int, optional, default=2
            The maximum number of concurrent jobs a user is allowed to have running. The default is 2.

        Returns:
        --------
        bool:
            `True` if the user has not reached the limit of concurrent jobs, `False` if the user has 
            reached or exceeded the limit.
        """
        row = self.df.loc[index]
        jobs_user_exc = self.df.loc[(self.df['username'] == row['username']) & (self.df['status'] == 'executando'), 'username'].shape[0]
        if jobs_user_exc >= limit: return False
        else: return True

    def limit_job(self, index, limit_per_user:bool=True, job_limit_per_user:int=3) -> bool:
        """
        Checks whether a job can be executed based on user-defined limits.

        This function evaluates whether a job at the specified index can be executed based on the user-defined 
        limits, such as the number of concurrent jobs a user is allowed to run. If the `limit_per_user` 
        parameter is set to `True`, it checks if the user has exceeded the allowed number of concurrent jobs 
        (as specified by `job_limit_per_user`).

        Parameters:
        -----------
        index : int
            The index of the job in the DataFrame to check the user's job limits.
        
        limit_per_user : bool, optional, default=True
            Whether to apply the limit on the number of concurrent jobs per user. If `True`, the limit will be applied.

        job_limit_per_user : int, optional, default=3
            The maximum number of concurrent jobs allowed for each user. The default value is 3.

        Returns:
        --------
        bool:
            `True` if all conditions are met (i.e., the user has not exceeded the job limit). 
            `False` if any condition fails (e.g., the user has exceeded the job limit).
        """
        res = []
        if limit_per_user: res.append(self.__limit_per_user(index, limit=job_limit_per_user))

        return all(res)
    

    # Ações status
    def __esperando(self, index:int):
        """
        Prepares and starts a job on an available machine with the required resources.

        This function checks the resource availability (CPU, GPU) on the machines, selects one with enough resources, 
        updates the job status, allocates the necessary CPUs and GPUs, creates a directory for job execution, 
        copies required files, and starts the job execution on the selected machine. It also handles job notifications 
        and updates the job-related DataFrame accordingly.

        Parameters:
        -----------
        index : int
            The index of the job in the DataFrame to prepare and start.

        Process:
        --------
        - The function first checks if the required CPUs and GPUs are available on the machines.
        - It then selects the first available machine, updates the job's status and assigns resources.
        - A new directory is created on the selected machine for job execution, and necessary files are copied.
        - The job is then prepared for execution by generating the taskset and script, and finally started.
        - If the job has not previously been notified, an email notification is sent to the user.
        - Updates to the machine and job data are saved.

        Returns:
        --------
        None
        """
        n_cpu=self.df.loc[index, 'n_cpu']
        gpu = not pd.isna(self.df.loc[index, 'gpu_requested'])
        if gpu: gpu_name = self.df.loc[index, 'gpu_requested'].split(",")
        else: gpu_name = ["all"]

        machines = self.search_available_machine(n_cpu=n_cpu,
                                      gpu=gpu,
                                      gpu_name=gpu_name,
                                      n_cpu_reserve=6
                                      )
        
        if machines.shape[0] > 0:
            machine = machines.iloc[0]
            self.df.loc[index, ['status']] = 'executando'
            self.df.loc[index, ['ip', 'name']] = machine[['ip', 'name']]

            # pegar start e and CPU e colocar na fila
            task = self.__get_taskset(machine_name=machine['name'], n_cpu=n_cpu)
            self.df.loc[index, 'taskset'] = ",".join(map(str, task))
            #max_cpu_end = self.df.loc[(self.df['name'] == machine['name']) & (self.df['status'] == 'executando'), 'cpu_end'].max()
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
                    if "disponivel" == machine[s] and (machine[n] in gpu_name or "all" in gpu_name):
                        self.df.loc[index, ['gpu_name', 'gpu_index']] = (machine[n], gpu_index)
                        # Atualizar status da GPU nas maquinas
                        self.data.machines.loc[self.data.machines['name'] == machine['name'], s] = "executando"
            
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

            pid = self.star_job(machine_name=machine['name'], path_exc=self.df.loc[index, 'path_exc'])
            self.df.loc[index, ['pid']] = pid
            self.df.loc[index, ['inicio']] = datetime.now()

            if self.df.loc[index, 'notification_start'] == "N":
                if self.__send_mail(subject=f"Seu trabalho começou {self.df.loc[index, 'job_name']} | LMDM",
                                message=self.__make_email_html(df_row=self.df.loc[index],
                                                                title="Inicio do trabalho",                                                            
                                                                ),
                                to=self.df.loc[index, 'e-mail'],
                                subtype="html"):
                    self.df.loc[index, 'notification_start'] = "Y"
            
            self.data.save_machines() 
            self.save()
            

    def __finalizado_copiar(self, index:int):
        """
        Method responsible for finalizing the file copy between machines after a job execution.
        Updates the job status and manages the copy process.

        Parameters:
        - index (int): The index of the row in the DataFrame that contains job and machine information.
        """
        def subp_copy():
            """
            Internal function that performs copy operations and status updates in a separate thread.
            """
            data_machines_origin = Data(); data_machines_origin.read_machines()
            ip_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'ip'].iloc[0]
            username_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'username'].iloc[0]
            password_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'password'].iloc[0]
            path_exc = self.df.loc[index, 'path_exc']
            copiar = False
            copiado = False

            try:
                print(f"Atualziando status copiando {ip_exc}")
                con = Connection(ip=ip_exc,
                                username=username_exc, 
                                password=password_exc)
                
                _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')
                con.execute_ssh_command(f"echo 'copiando - {pid}' > {path_exc}/labmonitor.status")
                con.ssh.close()
                self.df.loc[index, ['status']] = 'copiando'; self.save()
                copiar = True
            except Exception as e:
                print(f"Erro ao atualizar status do job p/ copiando: {e}")

            if copiar:
                try:
                    self.copy_dir(ip_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'ip'].iloc[0],
                        username_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'username'].iloc[0],
                        password_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'password'].iloc[0],
                        path_origin=self.df.loc[index, 'path_origin'],
                        
                        ip_exc=ip_exc,
                        username_exc=username_exc,
                        password_exc=password_exc,
                        path_exc=path_exc,
                        inverse=True
                        )
                    copiado = True
                    
                except Exception as e:
                    print(f'Erro ao copiar arquivos de exc para origin {ip_exc}: {e}')
            
            if copiado:
                cmd = f"echo 'finalizado - {pid}' > {path_exc}/labmonitor.status"
                self.read_excel()
                self.df.loc[index, ['status']] = 'finalizado'; self.save()
                self.__finalizado(index)
                
            else:
                self.read_excel()
                cmd = f"echo 'falha_ao_copiar - {pid}' > {path_exc}/labmonitor.status"
                self.df.loc[index, ['status']] = 'falha_ao_copiar'; self.save()
            try:
                print(f"Atualziando status final de copia (falha_ao_copiar ou finalizado - {copiado}) {ip_exc}")
                con = Connection(ip=ip_exc,
                                username=username_exc, 
                                password=password_exc)
                con.execute_ssh_command(cmd)
                con.ssh.close()
            except Exception as e:
                print(f"Erro ao atualizar status do job p/ finalizado: {e}")
                

        proc = threading.Thread(target=subp_copy)
        proc.start()
        
        
    def view_job_log(self, job_row:pd.Series, sufix:str=".log"):
        """
        Method to retrieve and display the latest logs from a remote machine associated with a job.
        The method connects to the target machine via SSH, fetches the most recent log lines, 
        and parses the logs into a dictionary where the log file name is the key and the content is the value.

        Parameters:
        - job_row (pd.Series): A row from the DataFrame containing information about the job.
        - sufix (str): The suffix (file extension) of the log files to be retrieved, default is ".log".

        Returns:
        - r (dict): A dictionary where the keys are log file names and the values are the corresponding log contents.
        """
        machine = self.data.machines[self.data.machines['name'] == job_row['name']].iloc[0]
        try:
            print(f"Conectando a {machine['ip']}...")
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
            print(f"Erro ao conectar para criar ler logs {machine['ip']}: {e}")
            return {"":""}


    def __executando(self, index:int):
        pass

    def __finalizado(self, index:int):
        """
        Method to send a notification email to the user when their job is completed successfully.
        This method triggers an email containing the completion message and updates the job's status.
        
        Parameters:
        - index (int): The index of the job in the DataFrame, indicating which job has finished.
        """
        def send():
            if self.df.loc[index, 'notification_end'] == "N":
                obs = """
                Seu trabalho foi finalizado corretamente. 
                Os arquivos foram copiados para seu diretório de origem."""

                if self.__send_mail(subject=f"Trabalho finalizado - {self.df.loc[index, 'job_name']} | LMDM",
                                message=self.__make_email_html(df_row=self.df.loc[index], observation=obs),
                                subtype="html",
                                to=self.df.loc[index, 'e-mail'],
                                ): self.df.loc[index, 'notification_end'] = "Y"
                self.save()

        proc = threading.Thread(target=send)
        proc.start()
        self.df.loc[index, ['fim']] = datetime.now()


    def __nao_finalizado_corretamente(self, index):
        """
        Method to notify the user when their job was not completed correctly.
        It sends an email to inform the user about the possible failure reasons, updates the job's 
        status to "nao_finalizado_corretamente", and attempts to copy the necessary files back to the origin.

        Parameters:
        - index (int): The index of the job in the DataFrame, indicating which job experienced an issue.
        """
        def send():
            """
            Inner function to handle sending the failure notification email.
            It sends an email to inform the user about the failure and provides suggestions for re-submission.
            The job status is then updated, and the files are copied back to the origin directory.
            """
            if self.df.loc[index, 'notification_end'] == "N":
                obs = """
                Seu trabalho não foi finalizado corretamente. 
                A falha pode ter sido devido ao uso de mais recursos que solicitado (CPU ou GPU), erro no seu script de execução ou desligamento da máquina. 
                Os arquivos foram copiados para seu diretório de origem, verifique e faça uma nova submissão à fila. 
                Caso possível, aproveite os dados produzidos para reiniciar o trabalho."""

                if self.__send_mail(subject=f"Trabalho não finalizado corretamente - {self.df.loc[index, 'job_name']} | LMDM",
                                message=self.__make_email_html(df_row=self.df.loc[index], observation=obs),
                                subtype="html",
                                to=self.df.loc[index, 'e-mail'],
                                ): self.df.loc[index, 'notification_end'] = "Y"
                
                self.__finalizado_copiar(index)
                self.df.loc[index, 'status'] = "nao_finalizado_corretamente" 
                self.save()
                
        proc = threading.Thread(target=send)
        proc.start()
 
    def __copiando(self, index):
        pass

    def __falha_ao_copiar(self, index):
        pass

    def __iniciado(self, index):
        pass

    def __nenhum(self, index):
        pass

    def __monitor_now(self):
        """
        Method to monitor the current status of all jobs and machines. 
        It updates the status of the jobs based on their current state and performs the appropriate actions for each job.
        
        The actions are mapped to different job statuses, such as 'esperando', 'finalizado_copiar', 'executando', etc.
        The method also reads job data from the Excel file, updates machine and job statuses, and iterates through all jobs 
        to apply the relevant action based on their status.

        The method ensures that only jobs that meet the job limits are processed.

        Actions for each job status:
        - 'esperando': Calls the __esperando method
        - 'finalizado_copiar': Calls the __finalizado_copiar method
        - 'executando': Calls the __executando method
        - 'finalizado': Calls the __finalizado method
        - 'nao_finalizado_corretamente': Calls the __nao_finalizado_corretamente method
        - 'copiando': Calls the __copiando method
        - 'falha_ao_copiar': Calls the __falha_ao_copiar method
        - 'iniciado': Calls the __iniciado method
        - '': Calls the __nenhum method (for empty or undefined statuses)

        This method is designed to monitor the status of jobs and execute corresponding actions based on the job's state.

        Parameters:
        - None
        """
        action = {'esperando': self.__esperando, 
                  "finalizado_copiar": self.__finalizado_copiar,
                  "executando": self.__executando, 
                  "finalizado": self.__finalizado, 
                  "nao_finalizado_corretamente": self.__nao_finalizado_corretamente,
                  "copiando":self.__copiando,
                  "falha_ao_copiar": self.__falha_ao_copiar,
                  "iniciado": self.__iniciado,
                  "": self.__nenhum
                  }
        
        self.read_excel()
        self.update_status_machines()
        self.update_status_jobs()
        print(self.df)
        
        for i, row in self.df.iterrows():
            if not self.limit_job(index=i): continue
            action[row['status']](index=i)



    def monitor(self, feq_time:int=300, now:bool=False):
        """
        Method to monitor jobs and machines periodically or immediately based on the provided parameters.
        
        This method continuously checks the status of the jobs and machines at regular intervals if the 'now' flag is False.
        If 'now' is set to True, it monitors the jobs and machines immediately without waiting.

        Parameters:
        - feq_time (int): The frequency in seconds (default: 300). Defines how often the monitor should run when `now` is False.
        - now (bool): A flag to determine whether to monitor immediately (True) or at regular intervals (False).

        The method will continuously execute the monitoring process (via `__monitor_now`), either in an infinite loop (when `now=False`) or once (when `now=True`).

        Behavior:
        - When `now` is False:
            - The method prints the start and end time of each monitoring cycle.
            - After each monitoring cycle, it waits for the specified `feq_time` before repeating the process.
        - When `now` is True:
            - The method performs one immediate monitoring cycle without waiting.
        """
        while not now:
            print(f"Monitorando inicio: {datetime.now()}")

            self.__monitor_now()
            
            print(f"Monitorando fim: {datetime.now()}")
            time.sleep(feq_time)
        else:
            self.__monitor_now()

    def __head_mail(self) -> str:
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
        return """<div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
        </div>"""

    def __make_email_html(self, df_row: pd.Series, title: str = "Agendamento", observation:str=""):
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

    def __send_mail(self, subject:str, message:str, to:str, subtype:str="plain") -> bool:
        """
        Sends an email to the specified recipient with the given subject and message content.
        
        This method creates an email message and sends it using SMTP through a Gmail server. It uses the credentials stored in `self.data.email` 
        for authentication and sends the email in the specified format (`plain` or `html`).

        Parameters:
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
            print (f"Successfully sent email {to}")
            return True
        except Exception as e: 
            print(f"Erro a enviar e-mail: {e}")
            return False
