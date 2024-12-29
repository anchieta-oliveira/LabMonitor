import os
import time
import pandas as pd
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.connection import Connection
from concurrent.futures import ThreadPoolExecutor, as_completed



class QueueJob:
    def __init__(self, data:Data, path:str="queue_job.xlsx"):
        self.df = self.read_excel(path)
        self.path = path
        self.data = data
        self.machines = data.machines

    def read_excel(self, path:str="queue_job.xlsx") -> pd.DataFrame:
        if os.path.exists(path):
            self.df = pd.read_excel(path)
            self.df['fim'] = self.df['fim'] = pd.to_datetime(self.df['fim'])
            self.df['inicio'] = self.df['inicio'] = pd.to_datetime(self.df['inicio'])
        else:
            self.reset()
        return self.df

    def save(self):
        self.df.to_excel(self.path, index=False)

    def reset(self) -> pd.DataFrame:
        columns = ["ip", "name", "username", "status", "pid", "path_exc", "path_origin", "script_name", "datatime_agendamento", "inicio", "fim", "n_cpu", "gpu_name", "gpu_index", "e-mail", "notification_start", "notification_end"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_excel("queue_job.xlsx", index=False)
        return self.df
    
    def update_gpu(self):
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
                if self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0] != "": sts = self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0]
                row[f"GPU_{gpu_index}_status"] = sts

            data_gpu.append(row)

        self.data.machines = pd.merge(self.machines[['ip','name', 'username', 'password', 'status', 'allowed_cpu', 'name_allowed_gpu', 'path_exc']], pd.DataFrame(data_gpu), on="name")
        self.data.save_machines()

    def __allowed_gpu(self):
        g_names = [e.split(",") for e in self.machines['name_allowed_gpu'].to_list()]
        col = self.machines.loc[:, self.machines.columns.str.contains(r"gpu_.*_name", case=False, regex=True)]

        for i, row in self.machines.iterrows():
            for c in col:
                for name in g_names[i]:
                    if name == self.machines[c].iloc[i]:
                        self.machines.loc[i, c.replace("Name", "status")] = "disponivel"
                    elif name != self.machines[c].iloc[i] and pd.isna(self.machines[c].iloc[i]): 
                        self.machines.loc[i, c.replace("Name", "status")] = "bloqueada"


    def __status_in_queue(self):
        v = self.df[self.df['status'] == "executando"]
        for i, maq in v.iterrows():
            self.machines.loc[
                    (self.machines['name'] == maq['name']) & 
                    (self.machines['ip'] == maq['ip']) & 
                    (self.machines[f"GPU_{maq['gpu_index']}_Name"] == maq['gpu_name']),
                    f"GPU_{maq['gpu_index']}_status"
                ] = "executando"
     

    def update_status_machines(self):
        self.update_gpu()
        self.__allowed_gpu()
        self.__status_in_queue()
        self.data.machines = self.machines
        self.data.save_machines()


    def update_status_jobs(self):
        for i, job in self.df.iterrows():
            if job['status'].strip() == 'executando': self.df.loc[i, ['status', 'pid']] = self.get_status_job(job['name'], job['path_exc'])
        self.save()


    def copy_dir(self, ip_origin, username_origin, password_origin, ip_exc, username_exc, password_exc, path_origin:str, path_exc:str):
        try:
            print(f"Conectando a {ip_origin}...")
            c = Connection(ip_origin, username_origin, password_origin)
            cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass & echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {path_origin}/ {username_exc}@{ip_exc}:{path_exc} """
            c.execute_ssh_command(cmd)
            c.ssh.close()
        except Exception as e:
            print(f"Erro ao conectar a {ip_origin}: {e}")

        
        
    def __make_script_exc(self, cpu_start:int, cpu_end:int, script:str, gpu_id:int=-1):
        return f"""
import os
import subprocess
with open("labmonitor.status", "w") as log: log.write("iniciado  - "+ str(os.getpid()))
if {gpu_id} == -1:
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES= taskset -c {cpu_start}-{cpu_end} sh {script} > {script.split(".")[-1]}", shell=True)
else:
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES={gpu_id} taskset -c {cpu_start}-{cpu_end} sh {script} > {script.split(".")[-1]}", shell=True)
with open("labmonitor.status", "w") as log: log.write("executando - "+ str(os.getpid()))
pcs.wait()
with open("labmonitor.status", "w") as log: log.write("finalizado_copiar - "+ str(os.getpid()))"""
    

    def prepare_job(self, machine_name:str, cpu_start:int, cpu_end:int, script:str, path_exc:str, gpu_id:int=-1):
        row = self.machines[self.machines['name'] == machine_name].iloc[0]
        try:
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"echo '{self.__make_script_exc(cpu_start, cpu_end, script, gpu_id)}' > {path_exc}/run_labmonitor.py")
            print(f"Preparação concluída em {row['ip']} - {path_exc}")
        except Exception as e:
            print(f"Erro na conexão ao preparar trabalho (srcipt run_labmonitor.py): {e}")


    def get_status_job(self, machine_name:str, path_exc:str):
        row = self.machines[self.machines['name'] == machine_name].iloc[0]
        try:
            print(f"Iniciando trabalho em {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            status, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')
            if (not pid in con.execute_ssh_command(f"ps -p {pid}")) and (status.strip() == 'executando'): status = "nao_finalizado_corretamente"
            con.ssh.close()
            return status.strip(), int(pid)
        except Exception as e:
            print(f"Erro ao verificar status do job: {e}")
            return "", -1


    def star_job(self, machine_name:str, path_exc:str)  -> int:
        row = self.machines[self.machines['name'] == machine_name].iloc[0]
        try:
            print(f"Iniciando trabalho em {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            ch = con.ssh.get_transport().open_session()
            ch.exec_command(f"cd {path_exc} && nohup python3 run_labmonitor.py >  run_labmonitor.log &")
            _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split("-")
            ch.close()
            con.ssh.close()
            return int(pid)
        except Exception as e:
            print(f"Erro na conexão ao iniciar o trabalho: {e}")
            return -1
    
    def __monitor_now(self):
        self.update_status_machines()


    def monitor(self, fist_day:bool=True, last_day:bool=True, send_email:bool=True, feq_time:int=43200, now:bool=False):
        while not now:
            self.__monitor_now()
            time.sleep(feq_time)
        else:
            self.__monitor_now()